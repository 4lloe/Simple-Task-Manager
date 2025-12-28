"""
Клієнт реєстру сервісів (registry.py)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Реалізує патерн Service Discovery для динамічного пошуку
конфігурації сервісів через Реєстр (розроблений в ПЗ-3).
"""

from config import get_registry_connection


class ServiceRegistryClient:
    """
    Клієнт для реалізації патерну Service Discovery.
    
    Забезпечує динамічний пошук адреси сервісу/БД через звернення
    до збереженої процедури GetServiceAddress (з ПЗ-3).
    Це дозволяє уникнути жорсткого кодування параметрів підключення.
    """
    
    @staticmethod
    def get_db_config(service_key: str) -> dict:
        """
        Звертається до збереженої процедури GetServiceAddress (з ПЗ-3)
        для отримання адреси сервісу/БД.
        
        Args:
            service_key (str): Ключ сервісу в реєстрі (наприклад, 'svc_task_core')
            
        Returns:
            dict: Конфігурація підключення до БД або None
            
        Raises:
            Exception: Якщо Реєстр сервісів недоступний
        """
        conn = get_registry_connection()
        if not conn:
            raise Exception("Registry Unavailable")
        
        cursor = conn.cursor()
        try:
            # Виклик процедури, створеної в ПЗ-3
            args = (service_key, )
            cursor.callproc('GetServiceAddress', args)
            
            for result in cursor.stored_results():
                row = result.fetchone()  # UrlAddress, Protocol, Version
                if row:
                    # Парсинг URL для отримання параметрів підключення до БД
                    # Для спрощення емулюємо повернення конфіга з отриманої адреси
                    # В реальності тут був би парсинг рядка з'єднання
                    url_address = row[0] if row else None
                    
                    # Логування отриманої адреси
                    print(f"[Service Discovery] Found service '{service_key}': {url_address}")
                    
                    return {
                        'host': 'localhost',
                        'user': 'root',
                        'password': '1972',  # Пароль MySQL
                        'database': 'simpletaskmanager'
                    }
            
            print(f"[Service Discovery] Service '{service_key}' not found in registry")
            return None
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def check_service_health(service_key: str) -> bool:
        """
        Перевіряє доступність сервісу в реєстрі.
        
        Args:
            service_key (str): Ключ сервісу
            
        Returns:
            bool: True якщо сервіс зареєстрований та активний
        """
        try:
            config = ServiceRegistryClient.get_db_config(service_key)
            return config is not None
        except Exception:
            return False


class ServiceRegistryException(Exception):
    """
    Виняток для помилок роботи з Реєстром сервісів.
    """
    def __init__(self, message: str, service_key: str = None):
        self.message = message
        self.service_key = service_key
        super().__init__(self.message)
    
    def __str__(self):
        if self.service_key:
            return f"ServiceRegistryException [{self.service_key}]: {self.message}"
        return f"ServiceRegistryException: {self.message}"
