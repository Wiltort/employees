import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Класс настроек для управления базой данных и консольным приложением"""
    # Настройки базы данных
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'employee_catalog')

    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    LANGUAGE = os.getenv('LANGUAGE', 'ru')
    INITIAL_DATA_COUNT = int(os.getenv('INITIAL_DATA_COUNT', 50000))


settings = Settings()