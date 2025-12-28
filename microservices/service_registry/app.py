"""
Service Registry (Реєстр Сервісів)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Централізований реєстр для реєстрації та виявлення мікросервісів.
Порт: 8500
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import threading
import time

app = FastAPI(
    title="Service Registry",
    description="Централізований реєстр мікросервісів Simple Task Manager",
    version="1.0.0"
)

# In-memory сховище зареєстрованих сервісів
services_registry: Dict[str, dict] = {}
lock = threading.Lock()

# Час життя реєстрації (секунди)
SERVICE_TTL = 30


class ServiceRegistration(BaseModel):
    """Модель для реєстрації сервісу"""
    service_name: str
    host: str
    port: int
    version: str = "1.0.0"
    metadata: Optional[dict] = None


class ServiceInfo(BaseModel):
    """Інформація про зареєстрований сервіс"""
    service_name: str
    host: str
    port: int
    version: str
    status: str
    registered_at: datetime
    last_heartbeat: datetime
    metadata: Optional[dict] = None


# ============================================================================
# ЕНДПОІНТИ РЕЄСТРУ
# ============================================================================

@app.post("/register", tags=["Registry"])
def register_service(registration: ServiceRegistration):
    """
    Реєстрація нового мікросервісу в реєстрі.
    
    Input: service_name, host, port, version
    Output: Статус реєстрації, ID сервісу
    """
    with lock:
        service_id = f"{registration.service_name}_{registration.host}_{registration.port}"
        now = datetime.now()
        
        services_registry[service_id] = {
            "service_name": registration.service_name,
            "host": registration.host,
            "port": registration.port,
            "version": registration.version,
            "status": "UP",
            "registered_at": now,
            "last_heartbeat": now,
            "metadata": registration.metadata
        }
        
        print(f"[Registry] Registered: {registration.service_name} at {registration.host}:{registration.port}")
        
        return {
            "success": True,
            "service_id": service_id,
            "message": f"Service '{registration.service_name}' registered successfully"
        }


@app.post("/heartbeat/{service_id}", tags=["Registry"])
def heartbeat(service_id: str):
    """
    Оновлення heartbeat для підтвердження активності сервісу.
    
    Input: service_id
    Output: Статус оновлення
    """
    with lock:
        if service_id not in services_registry:
            raise HTTPException(status_code=404, detail="Service not found")
        
        services_registry[service_id]["last_heartbeat"] = datetime.now()
        services_registry[service_id]["status"] = "UP"
        
        return {"success": True, "message": "Heartbeat received"}


@app.delete("/deregister/{service_id}", tags=["Registry"])
def deregister_service(service_id: str):
    """
    Видалення сервісу з реєстру.
    
    Input: service_id
    Output: Статус видалення
    """
    with lock:
        if service_id not in services_registry:
            raise HTTPException(status_code=404, detail="Service not found")
        
        del services_registry[service_id]
        print(f"[Registry] Deregistered: {service_id}")
        
        return {"success": True, "message": "Service deregistered"}


@app.get("/discover/{service_name}", tags=["Discovery"])
def discover_service(service_name: str):
    """
    Пошук активного екземпляра сервісу за назвою (Service Discovery).
    
    Input: service_name
    Output: host, port активного сервісу або помилка
    """
    with lock:
        for service_id, info in services_registry.items():
            if info["service_name"] == service_name and info["status"] == "UP":
                return {
                    "success": True,
                    "service_name": service_name,
                    "host": info["host"],
                    "port": info["port"],
                    "url": f"http://{info['host']}:{info['port']}"
                }
        
        raise HTTPException(
            status_code=404, 
            detail=f"Service '{service_name}' not found or unavailable"
        )


@app.get("/services", tags=["Registry"])
def list_services():
    """
    Отримання списку всіх зареєстрованих сервісів.
    
    Input: -
    Output: JSON-список сервісів з їх статусами
    """
    with lock:
        return {
            "success": True,
            "count": len(services_registry),
            "services": list(services_registry.values())
        }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check реєстру"""
    return {
        "status": "healthy",
        "service": "service-registry",
        "registered_services": len(services_registry)
    }


# ============================================================================
# ФОНОВА ЗАДАЧА - ПЕРЕВІРКА HEARTBEAT
# ============================================================================

def check_services_health():
    """Періодична перевірка здоров'я сервісів"""
    while True:
        time.sleep(10)
        with lock:
            now = datetime.now()
            for service_id, info in services_registry.items():
                elapsed = (now - info["last_heartbeat"]).total_seconds()
                if elapsed > SERVICE_TTL:
                    info["status"] = "DOWN"
                    print(f"[Registry] Service DOWN: {service_id} (no heartbeat for {elapsed:.0f}s)")


# Запуск фонової перевірки
health_thread = threading.Thread(target=check_services_health, daemon=True)
health_thread.start()


if __name__ == "__main__":
    print("=" * 60)
    print("SERVICE REGISTRY - Simple Task Manager")
    print("Порт: 8500")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8500)
