"""
Клієнт Service Registry (Спільний модуль)
Використовується всіма мікросервісами для реєстрації та discovery.
"""

import requests
import threading
import time
from typing import Optional


class RegistryClient:
    """
    Клієнт для взаємодії з Service Registry.
    Забезпечує автоматичну реєстрацію та heartbeat.
    """
    
    REGISTRY_URL = "http://127.0.0.1:8500"
    
    def __init__(self, service_name: str, host: str, port: int, version: str = "1.0.0"):
        self.service_name = service_name
        self.host = host
        self.port = port
        self.version = version
        self.service_id: Optional[str] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False
    
    def register(self) -> bool:
        """Реєстрація сервісу в реєстрі"""
        try:
            response = requests.post(
                f"{self.REGISTRY_URL}/register",
                json={
                    "service_name": self.service_name,
                    "host": self.host,
                    "port": self.port,
                    "version": self.version
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.service_id = data.get("service_id")
                print(f"[{self.service_name}] Registered with ID: {self.service_id}")
                self._start_heartbeat()
                return True
        except Exception as e:
            print(f"[{self.service_name}] Registration failed: {e}")
        return False
    
    def deregister(self):
        """Видалення реєстрації при зупинці"""
        self._running = False
        if self.service_id:
            try:
                requests.delete(f"{self.REGISTRY_URL}/deregister/{self.service_id}", timeout=5)
                print(f"[{self.service_name}] Deregistered")
            except:
                pass
    
    def _start_heartbeat(self):
        """Запуск фонового heartbeat"""
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
    
    def _heartbeat_loop(self):
        """Цикл відправки heartbeat"""
        while self._running:
            time.sleep(10)
            if self.service_id:
                try:
                    requests.post(
                        f"{self.REGISTRY_URL}/heartbeat/{self.service_id}",
                        timeout=5
                    )
                except:
                    pass
    
    @staticmethod
    def discover(service_name: str) -> Optional[str]:
        """
        Пошук URL сервісу через Service Discovery.
        
        Returns:
            URL сервісу або None
        """
        try:
            response = requests.get(
                f"{RegistryClient.REGISTRY_URL}/discover/{service_name}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get("url")
        except Exception as e:
            print(f"[Discovery] Failed to discover {service_name}: {e}")
        return None
