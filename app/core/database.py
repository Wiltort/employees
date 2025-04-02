from core.settings import settings
from psycopg import connect
from sqlalchemy import and_, create_engine, MetaData, select, func
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
                    filter_stmt.append(PositionAlias.title.ilike(f"%{f["value"]}%"))
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

    def get_direct_subordinates(self, employee_id: int, limit: int = 25) -> List[Employee]:
        """
        Retrieves list of direct subordinates for specified employee.

        :param employee_id: ID of the manager to get subordinates for
        :type employee_id: int

        :return: List of direct subordinates with loaded relationships
        :rtype: List[Employee]

        Example usage:
            subs = get_direct_subordinates(123)
            for sub in subs:
                print(f"{sub.get_full_name()} ({sub.position.title})")
        """
        PositionAlias = aliased(Position)
        ManagerAlias = aliased(Employee)

        stmt = (
            select(Employee)
            .options(
                joinedload(Employee.position.of_type(PositionAlias)),
                joinedload(Employee.manager.of_type(ManagerAlias)),
            )
            .where(Employee.manager_id == employee_id)
            .limit(limit)
        )

        with Session(self.engine) as session:
            return list(session.scalars(stmt))

    def get_employee_hierarchy(self, root_id: int | None = None, limit: int = 25) -> List[Dict]:
        """
        Retrieves employee hierarchy in tree structure format.

        :param root_id: Starting point for hierarchy (None returns full tree)
        :type root_id: int | None

        :return: Nested dictionary with employee data and subordinates
        :rtype: List[Dict]

        Example output:
        [
            {
                "id": 1,
                "name": "Ivanov Petr Sergeevich",
                "position": "CEO",
                "subordinates": [
                    {
                        "id": 2,
                        "name": "Smirnova Anna Vladimirovna",
                        "position": "Manager",
                        "subordinates": [...]
                    }
                ]
            }
        ]
        """
        # Get all employees with their relationships
        PositionAlias = aliased(Position)
        ManagerAlias = aliased(Employee)
        if root_id:
            stmt = (
                select(Employee)
                .options(
                    joinedload(Employee.position.of_type(PositionAlias)),
                    joinedload(Employee.manager.of_type(ManagerAlias)),
                )
                .where(id=root_id)
            )
        else:
            stmt = (
                select(Employee)
                .options(
                    joinedload(Employee.position.of_type(PositionAlias)),
                    joinedload(Employee.manager.of_type(ManagerAlias)),
                )
                .where(PositionAlias.level == 1)
            )
        with Session(self.engine) as session:
            root_managers = session.scalars(stmt)
        # Build tree structure
        hierarchy = []
        for emp in root_managers:
            hierarchy.append({
                "id": emp.id,
                "name": emp.get_full_name(),
                "position": emp.position.title,
            })

        return hierarchy

    def _get_employee_dict(self, emp_list, limit: int = 25):
        if emp_list == []:
            return
        for emp in emp_list:
            emp["subordinates"] = self.get_direct_subordinates(employee_id=emp['id'], limit=limit)
    


employee_catalog = EmployeeCatalog()
