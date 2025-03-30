from settings import settings
from psycopg import connect
from sqlalchemy import create_engine
from .models import Base
from mimesis import Person, Datetime, Finance, Text
from mimesis.locales import Locale
from urllib.parse import quote_plus


DB_CONFIG = {
    'dbname': settings.DB_NAME,
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
}


'''with connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("""CREATE TABLE test (
                    id serial PRYMARY KEY,
                    num integer)"""
        )
        conn.commit()'''




class EmployeeCatalog:
    """Класс для проведения операции над базой данных работников"""
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.person = Person(Locale.RU)
        self.datetime = Datetime()
        self.finance = Finance()
        self.text = Text()

        self.init_tables()

    
    def init_tables(self):
        """Определение структуры таблиц"""
        with connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS test (
                    id serial PRIMARY KEY,
                    num integer)"""
                )
                conn.commit()
