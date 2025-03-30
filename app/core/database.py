from core.settings import settings
from psycopg import connect
from sqlalchemy import create_engine
from employees.models import Base
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
    """Класс для проведения операции над базой данных работников"""
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.person = Person(Locale.RU)
        self.datetime = Datetime()
        self.finance = Finance()
        self.text = Text()
        self.base = Base
        self.init_tables()

    def init_tables(self):
        """Определение структуры таблиц"""
        self.base.metadata.create_all(self.engine)

    def init_data(self):
        """Генерация начальных данных в таблицах"""
        pass