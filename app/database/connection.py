from settings import settings
from psycopg2 import connect
from sqlalchemy import create_engine
from .models import Base
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale
from urllib.parse import quote_plus


DB_CONFIG = {
    'dbname': settings.DB_NAME,
    'user': settings.DB_USER,
    'password': quote_plus(settings.DB_PASSWORD),
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
}


class EmployeeCatalog:
    """Класс для проведения операции над базой данных работников"""
    def __init__(self):
        self.conn = connect(**DB_CONFIG)
        self.engine = create_engine(settings.DATABASE_URL)
        self.person = Person(Locale.RU)
        self.datetime = Datetime()
        self.finance = Finance()
        self.text = Text()

        self.init_tables()

    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    def init_tables(self):
        """Определение структуры таблиц"""
        Base.metadata.create_all(self.engine)