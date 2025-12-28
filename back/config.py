

import mysql.connector
from mysql.connector import Error


class DBConfig:
    """
    Конфігурація підключення ТІЛЬКИ до Реєстру сервісів.
    Адресу основної БД ми отримаємо динамічно через Service Discovery.
    """
    REGISTRY_DB = {
        'host': 'localhost',
        'user': 'root',
        'password': '1972',  # Вказати власний пароль
        'database': 'taskmanager_service_registry'
    }


def get_registry_connection():
    """
    Створює з'єднання з базою даних Реєстру сервісів.
    
    Returns:
        mysql.connector.connection: Об'єкт з'єднання або None у разі помилки
    """
    try:
        conn = mysql.connector.connect(**DBConfig.REGISTRY_DB)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Registry Connection Error: {e}")
        return None
