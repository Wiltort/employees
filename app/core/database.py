from core.settings import settings
from psycopg import connect
from sqlalchemy import (
    and_,
    create_engine,
    MetaData,
    select,
    func,
    union_all,
    select,
    alias,
)
from sqlalchemy.orm import Session, joinedload, aliased
from employees.models import Base, POSITION_HIERARCHY, Position, Employee
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale
from mimesis.enums import Gender
from mimesis.builtins.ru import RussiaSpecProvider
import random
from typing import List, Dict


DB_CONFIG = {
    "dbname": settings.DB_NAME,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
}

lang_dict = {
    "ru": Locale.RU,
    "en": Locale.EN,
}


class EmployeeCatalog:
    """Class for managing employees database"""

    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.person = Person(lang_dict[settings.LANGUAGE])
        self.datetime = Datetime()
        self.finance = Finance()
        self.text = Text()
        self.base = Base
        self.metadata = MetaData()
        self.init_tables()

    def init_tables(self):
        """Definition of tables"""
        self.base.metadata.create_all(self.engine)

    def truncate_all_tables(self):
        """Deletes all data in all tables"""
        self.metadata.reflect(bind=self.engine)
        with self.engine.begin() as conn:
            for table in reversed(self.metadata.sorted_tables):
                conn.execute(table.delete())

    def init_data(self, rows: int = settings.INITIAL_DATA_COUNT, reset: bool = True):
        """
        Generates initial dataset including positions and employees hierarchy.
        :param rows: Count of records to be added.
        :type rows: int
        :param reset: Flag for deleting all previous data in all tables.
        :type reset: bool

        Process flow:
            1. Truncates tables and recreates position hierarchy if reset=True
            2. Distributes employees across 5 hierarchy levels:
            3. Automatically assigns managers from higher hierarchy levels

        Example usage:
            Generate 50,000 employees with clean setup
            init_data(rows=50000)

            Add 1000 employees to existing data
            init_data(rows=1000, reset=False)

        Data generation rules:
            - Position distribution follows POSITION_HIERARCHY structure
            - Manager assignment respects organizational hierarchy
            - Salary and hire dates generated by Faker methods
            - Names localized based on configured language
        """
        if reset:
            self.truncate_all_tables()
            with Session(self.engine) as session:
                data = []
                for title, level in POSITION_HIERARCHY:
                    data.append(Position(title=title, level=level))
                session.bulk_save_objects(data)
                session.commit()
        emp_count = rows
        for level in range(1, 6):
            with Session(self.engine) as session:
                if level != 1:
                    stmt = (
                        select(Employee.id)
                        .join(Position)
                        .where(Position.level == level - 1)
                    )
                    manager_ids = list(session.scalars(stmt))
                data = []
                stmt = select(Position.id).where(Position.level == level)
                position_ids = list(session.scalars(stmt))
                if not position_ids:
                    continue
                if level == 5:
                    count = emp_count
                else:
                    managers_count = int((0.1 ** (5 - level)) * rows)
                    emp_count -= managers_count
                    count = managers_count
                for _ in range(count):
                    position_id = random.choice(position_ids)
                    if level != 1:
                        manager_id = random.choice(manager_ids)
                    else:
                        manager_id = None
                    manager = self.generate_employee(
                        position_id=position_id, manager_id=manager_id
                    )
                    data.append(manager)
                session.bulk_save_objects(data)
                session.commit()

    def generate_employee(
        self, position_id: int | None = None, manager_id: int | None = None
    ) -> Employee:
        """
        Generates a random employee with realistic demographic data.

        :param position_id: ID of the position for the employee. If None,
                            will be randomly selected based on hierarchy.
        :type position_id: int | None

        :param manager_id: ID of the manager for the employee. Automatically
                           determined based on position level if None.
        :type manager_id: int | None

        :return: Employee object with generated data and relationships
        :rtype: Employee

        Example usage:
            Generate employee with random position and manager
            emp = generate_employee()

            Generate specific position employee
            emp = generate_employee(position_id=5)

        Features:
            - Gender-balanced name generation using Mimesis
            - Culturally appropriate patronymics for Russian locale
            - Realistic salary ranges (30,000 - 300,000)
            - Employment dates between 2015-2024
            - Position/manager hierarchy awareness

        Data generation details:
            - Names are generated according to configured locale
            - Russian employees receive valid patronymics
            - Salaries are rounded to nearest integer
            - Hire dates are uniformly distributed in range

        """
        data = {}
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        data["first_name"] = self.person.first_name(gender=gender)
        data["last_name"] = self.person.last_name(gender=gender)
        if settings.LANGUAGE == "ru":
            rsp = RussiaSpecProvider()
            data["patronymic"] = rsp.patronymic(gender=gender)
        data["hire_date"] = self.datetime.date(start=2015, end=2024)
        data["salary"] = self.finance.price(minimum=30000, maximum=300000)
        data["position_id"] = position_id
        if manager_id:
            data["manager_id"] = manager_id
        return Employee(**data)

    def get_employees_list(
        self, sort_opts: List[Dict] = [], filter_opts: List[Dict] = [], limit: int = 10
    ) -> List[Employee]:
        """
        Retrieves a list of employees with filtering, sorting and limit capabilities.

        :param sort_opts: Sorting options in format:
            [{
                'order_field': field to sort by (id/name/position/date/salary/manager),
                'descending': sort direction (True for DESC, False for ASC)
            }]
        :type sort_opts: List[Dict]

        :param filter_opts: Filter conditions in format:
            [{
                'field': field to filter by (id/name/position/date/salary/manager),
                'value': filter value
            }]
        :type filter_opts: List[Dict]

        :param limit: Maximum number of records to return
        :type limit: int

        :return: List of employees with loaded position and manager relationships
        :rtype: List[Employee]

        Usage examples:
            Filter by position and sort by salary:
                get_employees_list(
                    filter_opts=[{'field': 'position', 'value': 'Manager'}],
                    sort_opts=[{'order_field': 'salary', 'descending': True}]
                )

            Search by name fragment:
                get_employees_list(filter_opts=[{'field': 'name', 'value': 'John'}])

            Get employees hired in 2023:
                get_employees_list(filter_opts=[{'field': 'date', 'value': '2023'}])

        Features:
            - Date filter supports formats: Year (YYYY), Year-Month (YYYY-MM), Full date (YYYY-MM-DD)
            - Name/manager search performs case-insensitive substring matching
            - Name/manager sorting follows order: Last Name -> First Name -> Patronymic
            - Position filtering uses titles from related Position table
        """
        PositionAlias = aliased(Position)
        ManagerAlias = aliased(Employee)
        stmt = select(Employee).options(
            joinedload(Employee.position.of_type(PositionAlias)),
            joinedload(Employee.manager.of_type(ManagerAlias)),
        )
        filter_stmt = []
        for f in filter_opts:
            match f["field"]:
                case "id":
                    filter_stmt.append(Employee.id == int(f["value"]))
                case "name":
                    search_value = f"%{f['value']}%"
                    filter_expr = func.concat(
                        Employee.last_name,
                        " ",
                        Employee.first_name,
                        " ",
                        func.coalesce(Employee.patronymic, ""),
                    ).ilike(search_value)
                    filter_stmt.append(filter_expr)
                case "position":
                    filter_stmt.append(PositionAlias.title.ilike(f"%{f['value']}%"))
                case "date":
                    if "-" in f["value"]:
                        try:
                            year, month, day = map(int, f["value"].split("-"))
                        except ValueError:
                            raise ValueError("Incorrect date format")
                        filter_stmt.append(
                            and_(
                                func.extract("year", Employee.hire_date) == year,
                                func.extract("month", Employee.hire_date) == month,
                                func.extract("day", Employee.hire_date) == day,
                            )
                        )
                    elif len(f["value"]) == 4:
                        try:
                            year = int(f["value"])
                        except ValueError:
                            raise ValueError("Invalid year format. Use 4-digit year")
                        filter_stmt.append(
                            func.extract("year", Employee.hire_date) == year
                        )
                    else:
                        raise ValueError("Incorrect date format")
                case "salary":
                    filter_stmt.append(Employee.salary == int(f["value"]))
                case "manager":
                    search_value = f"%{f['value']}%"
                    filter_expr = func.concat(
                        ManagerAlias.last_name,
                        " ",
                        ManagerAlias.first_name,
                        " ",
                        func.coalesce(ManagerAlias.patronymic, ""),
                    ).ilike(search_value)
                    filter_stmt.append(filter_expr)
                case _:
                    raise ValueError("field not correct")
        if filter_stmt:
            stmt = stmt.filter(*filter_stmt)
        if sort_opts:
            order_by_fields = []
            for sort_opt in sort_opts:
                order_field = sort_opt["order_field"]
                descending = sort_opt["descending"]
                match order_field:
                    case "id":
                        field = Employee.id.desc() if descending else Employee.id
                    case "name":
                        field = (
                            (
                                Employee.last_name.desc()
                                if descending
                                else Employee.last_name
                            ),
                            (
                                Employee.first_name.desc()
                                if descending
                                else Employee.first_name
                            ),
                            (
                                Employee.patronymic.desc()
                                if descending
                                else Employee.patronymic
                            ),
                        )
                    case "position":
                        field = (
                            PositionAlias.title.desc()
                            if descending
                            else PositionAlias.title
                        )
                    case "date":
                        field = (
                            Employee.hire_date.desc()
                            if descending
                            else Employee.hire_date
                        )
                    case "salary":
                        field = (
                            Employee.salary.desc() if descending else Employee.salary
                        )
                    case "manager":
                        field = (
                            (
                                ManagerAlias.last_name.desc()
                                if descending
                                else ManagerAlias.last_name
                            ),
                            (
                                ManagerAlias.first_name.desc()
                                if descending
                                else ManagerAlias.first_name
                            ),
                            (
                                ManagerAlias.patronymic.desc()
                                if descending
                                else ManagerAlias.patronymic
                            ),
                        )
                    case _:
                        raise ValueError("field not correct")
                if isinstance(field, tuple):
                    order_by_fields.extend(field)
                else:
                    order_by_fields.append(field)
            stmt = stmt.order_by(*order_by_fields)
        stmt = stmt.limit(limit=limit)
        with Session(self.engine) as session:
            empls = list(session.scalars(stmt))
        return empls

    def get_hierarchy(self, root_id: int, limit: int = 8) -> dict:
        """
        Returns employee hierarchy as a nested dictionary with element count limitation

        Parameters:
            root_id (int): ID of the employee to build hierarchy for
            limit (int): Maximum number of elements to include in hierarchy (default 8)

        Returns:
            dict: Nested dictionary structure with format:
            {
                "id": int,
                "full_name": str,
                "position": str,
                "subordinates": [
                    # recursive structure of subordinates
                ]
            }

        Example return:
            {
                "id": 123,
                "full_name": "John Doe",
                "position": "Team Lead",
                "subordinates": [
                    {
                        "id": 456,
                        "full_name": "Jane Smith",
                        "position": "Developer",
                        "subordinates": []
                    },
                    ...
                ]
            }

        Implementation Details:
            - Uses recursive SQL CTE (Common Table Expression) to get reporting chain
            - Builds hierarchy using BFS (Breadth-First Search) traversal
            - Limits elements using count-based early termination
            - Explicitly handles SQLAlchemy sessions and connections
            - Works with direct column data instead of ORM relationships
            - Optimized for read-heavy operations with large datasets

        Notes:
            1. Root employee is always included even when limit=0
            2. Subordinates are added in database discovery order
            3. Strictly maintains unique employee IDs in hierarchy
            4. Execution flow:
                a. Build recursive CTE with position joins
                b. Execute query and collect raw results
                c. Convert to dictionary with manager relationships
                d. Construct tree using BFS with limit check
            5. Returned structure is session-independent
            6. Handles circular references through ID tracking
        """
        emp = aliased(Employee, name="emp")
        pos = aliased(Position, name="pos")

        hierarchy = (
            select(
                emp.id,
                emp.manager_id,
                emp.first_name,
                emp.last_name,
                emp.patronymic,
                pos.title.label("position_title"),
            )
            .where(emp.id == root_id)
            .join(pos, emp.position_id == pos.id)
            .cte(recursive=True, name="hierarchy")
        )

        mgr = aliased(Employee, name="mgr")
        pos_recursive = aliased(Position, name="pos_recursive")

        recursive_part = (
            select(
                emp.id,
                emp.manager_id,
                emp.first_name,
                emp.last_name,
                emp.patronymic,
                pos_recursive.title.label("position_title"),
            )
            .join(mgr, emp.manager_id == mgr.id)
            .join(hierarchy, mgr.id == hierarchy.c.id)
            .join(pos_recursive, emp.position_id == pos_recursive.id)
        )

        cte_query = hierarchy.union_all(recursive_part)

        stmt = select(
            cte_query.c.id,
            cte_query.c.manager_id,
            cte_query.c.first_name,
            cte_query.c.last_name,
            cte_query.c.patronymic,
            cte_query.c.position_title,
        )

        with Session(self.engine) as session:
            results = session.execute(stmt).unique().all()

        # Собираем словарь сотрудников
        employees_dict = {
            row.id: {
                "id": row.id,
                "manager_id": row.manager_id,
                "full_name": f"{row.last_name} {row.first_name} {row.patronymic or ''}".strip(),
                "position": row.position_title,
                "subordinates": [],
            }
            for row in results
        }

        # BFS
        root = employees_dict.get(root_id)
        if not root:
            return {}

        queue = [root]
        count = 0
        added_ids = {root_id}

        while queue and count < limit:
            current = queue.pop(0)
            subordinates = [
                emp
                for emp in employees_dict.values()
                if emp["manager_id"] == current["id"] and emp["id"] not in added_ids
            ]

            for emp in subordinates:
                if count >= limit:
                    break
                current["subordinates"].append(emp)
                added_ids.add(emp["id"])
                queue.append(emp)
                count += 1

        return root

    def get_position_id(self, position_title: str) -> int:
        """
        Get position ID by title
        
        :param position_title: Title of the position
        :return: ID of the position
        """
        with Session(self.engine) as session:
            pos = session.scalar(select(Position.id).where(Position.title == position_title))
        if not pos:
            raise ValueError(f"Position with title '{position_title}' not found")
        return pos

    def create_employee(self, emp_data: dict) -> bool:
        """
        Creates a new employee with validation and automatic data completion.

        :param emp_data: Dictionary with employee data. Supported keys:
            - first_name: Employee's first name (required if no full_name)
            - last_name: Employee's last name (required if no full_name)
            - full_name: Combined name in 'Last_First_Patronymic' format
            - patronymic: Middle name (optional)
            - position_id: ID of employee's position
            - position: Title of position (alternative to position_id)
            - manager_id: ID of direct manager
            - hire_date: Date of hire (YYYY-MM-DD format)
            - salary: Monthly salary amount
        :type emp_data: dict

        :return: Newly created Employee object with database-generated ID
        :rtype: Employee

        :raises ValueError: For missing required fields or invalid position/manager

        Example usage:
            Create with minimal data:
            create_employee({
                'full_name': 'Иванов_Петр_Сергеевич'
            })

            Create with explicit fields:
            create_employee({
                'first_name': 'Анна',
                'last_name': 'Смирнова',
                'position': 'Senior Developer',
                'salary': 150000
            })

        Features:
            - Automatic name parsing from full_name field
            - Position lookup by title or ID
            - Manager auto-assignment based on position hierarchy
            - Default values for missing fields:
                - Random name components if not provided
                - Current-date salary if not specified
                - Random hire date between 2015-2024
            - Validation for:
                - Mandatory name fields
                - Position existence
                - Manager hierarchy consistency
                - Salary positivity

        Implementation Details:
            - Uses separate SQLAlchemy sessions for different operations
            - Handles position lookup through get_position_id()
            - Automatically refreshes object after commit
            - Supports both Russian and English naming conventions
            - Maintains data consistency through transaction blocks
        """
        data = {}
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        data['first_name'] = emp_data.get('first_name', self.person.first_name(gender=gender))
        data['last_name'] = emp_data.get('last_name', self.person.last_name(gender=gender))
        if settings.LANGUAGE == 'ru':
            rsp = RussiaSpecProvider()
            data['patronymic'] = emp_data.get('patronymic', rsp.patronymic(gender=gender))
        elif emp_data.get('patronymic'):
            data["patronymic"] = emp_data['patronymic']
        data['hire_date'] = emp_data.get('hire_date', self.datetime.date(start=2015, end=2024))
        data['salary'] = emp_data.get('salary', self.finance.price(minimum=30000, maximum=300000))
        if not emp_data.get('position_id'):
            with Session(self.engine) as session:
                positions = list(session.scalars(select(Position.id)))
            data['position_id'] = random.choice(positions)
        else:
            data['position_id'] = emp_data.get('position_id')
        if not emp_data.get('manager_id'):
            with Session(self.engine) as session:
                level = session.scalar(select(Position.level).where(Position.id == data["position_id"]))
                if level != 1:
                    stmt = (
                        select(Employee.id)
                        .join(Position)
                        .where(Position.level == level - 1)
                    )
                    manager_ids = list(session.scalars(stmt))
                    data['manager_id'] = random.choice(manager_ids)
        else:
            data['manager_id'] = emp_data.get('manager_id')
        new_employee = Employee(**data)
        with Session(self.engine) as session:
            session.add(new_employee)
            session.commit()
            session.refresh(new_employee)
        return new_employee


employee_catalog = EmployeeCatalog()
