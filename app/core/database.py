from core.settings import settings
from psycopg import connect
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import Session, joinedload, aliased
from employees.models import Base, POSITION_HIERARCHY, Position, Employee
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale
from mimesis.enums import Gender
from mimesis.builtins.ru import RussiaSpecProvider
import random


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
        Generates initial data in tables.
        :param rows: Count of records to be added.
        :type rows: int
        :param reset: Flag for deleting all previous data in all tables.
        :type reset: bool
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
        """Generate data for one employee"""
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

    def get_employees_list(self, order_field: str | None = None, descending: bool = False):
        PositionAlias = aliased(Position)
        ManagerAlias = aliased(Employee)
        stmt = select(Employee).options(
            joinedload(Employee.position.of_type(PositionAlias)),
            joinedload(Employee.manager.of_type(ManagerAlias))
        )
        if order_field:
            match order_field:
                case 'id':
                    stmt = stmt.order_by(Employee.id.desc() if descending else Employee.id)  
                case 'name':
                    stmt = stmt.order_by(
                        Employee.last_name.desc() if descending else Employee.last_name,
                        Employee.first_name.desc() if descending else Employee.first_name,
                        Employee.patronymic.desc() if descending else Employee.patronymic
                    )
                case 'position':
                    stmt = stmt.order_by(
                        PositionAlias.title.desc() if descending else PositionAlias.title
                    )
                case 'date':
                    stmt = stmt.order_by(
                        Employee.hire_date.desc() if descending else Employee.hire_date
                    )
                case 'salary':
                    stmt = stmt.order_by(
                        Employee.salary.desc() if descending else Employee.salary
                    )
                case 'manager':
                    stmt = stmt.order_by(
                        ManagerAlias.last_name.desc() if descending else ManagerAlias.last_name,
                        ManagerAlias.first_name.desc() if descending else ManagerAlias.first_name,
                        ManagerAlias.patronymic.desc() if descending else ManagerAlias.patronymic
                    )
        stmt = stmt.limit(10)
        with Session(self.engine) as session:
            empls = list(session.scalars(stmt))
        return empls


employee_catalog = EmployeeCatalog()
