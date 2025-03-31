from core.settings import settings
from psycopg import connect
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import Session
from employees.models import Base, POSITION_HIERARCHY, Position, Employee
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale
from mimesis.enums import Gender
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
        print('OK')
        self.init_data()

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
                session.add_all(data)
                session.commit()
        emp_count = 0
        managers = {}
        for level in range(1, 5):
            data = []
            with Session(self.engine) as session:
                stmt = select(Position.id).where(Position.level == level)
                position_ids = list(session.scalars(stmt))
                managers[level] = []
                if not position_ids:
                    continue
                managers_count = int((0.1 ** (5 - level)) * rows)
                emp_count += managers_count
                print(managers_count)
                for _ in range(managers_count):
                    position_id = random.choice(position_ids)
                    if level != 1:
                        manager_id = random.choice(managers[level - 1])
                    else:
                        manager_id = None
                    manager = self.generate_employee(position_id=position_id, manager_id=manager_id)
                    managers[level].append(manager.id)
                    print(managers)
                    data.append(manager)
                session.add_all(data)
                session.commit()

    def generate_employee(
        self, position_id: int | None = None, manager_id: int | None = None
    ) -> Employee:
        """Generate data for one employee"""
        data = {}
        gender = random.choice([Gender.MALE, Gender.FEMALE])
        data["first_name"] = self.person.first_name(gender=gender)
        data["last_name"] = self.person.last_name(gender=gender)
        data["patronymic"] = (
            self.person.surname(gender=gender) if settings.LANGUAGE == "ru" else None
        )
        data["hire_date"] = self.datetime.date(start=2015, end=2024)
        data["salary"] = self.finance.price(minimum=30000, maximum=300000)
        data["position_id"] = position_id
        data["manager_id"] = manager_id
        return Employee(**data)


employee_catalog = EmployeeCatalog()
