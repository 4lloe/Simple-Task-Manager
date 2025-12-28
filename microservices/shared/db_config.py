"""
Конфігурація бази даних (Спільний модуль)
"""

import mysql.connector
from mysql.connector import Error


class DBConfig:
    """Конфігурація підключення до БД"""
    
    TASK_DB = {
        'host': 'localhost',
        'user': 'root',
        'password': '1972',
        'database': 'simpletaskmanager'
    }


def get_db_connection():
    """
    Створює з'єднання з базою даних.
    
    Returns:
        mysql.connector.connection або None
    """
    try:
        conn = mysql.connector.connect(**DBConfig.TASK_DB)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"DB Connection Error: {e}")
        return None
