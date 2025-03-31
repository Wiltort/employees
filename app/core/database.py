from core.settings import settings
from psycopg import connect
from sqlalchemy import create_engine, MetaData, insert
from sqlalchemy.orm import Session
from employees.models import Base, POSITION_HIERARCHY, Position, Employee
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale


DB_CONFIG = {
    'dbname': settings.DB_NAME,
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
}


class EmployeeCatalog:
    """Class for managing employees database"""
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.person = Person(Locale.RU)
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
                session.add_all(data)
                session.commit()
                