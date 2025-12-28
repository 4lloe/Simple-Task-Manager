"""
API Gateway (Єдина точка входу)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Маршрутизує запити до мікросервісів через Service Discovery.
Порт: 8000
"""

import uvicorn
import httpx
import requests
import threading
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

SERVICE_NAME = "api-gateway"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8000
REGISTRY_URL = "http://127.0.0.1:8500"

app = FastAPI(
    title="API Gateway",
    description="Єдина точка входу для Simple Task Manager",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.AsyncClient(timeout=30.0)


# ============== РЕЄСТРАЦІЯ ==============
service_id = None
heartbeat_started = False

def register_service():
    global service_id, heartbeat_started
    try:
        r = requests.post(f"{REGISTRY_URL}/register", json={
            "service_name": SERVICE_NAME,
            "host": SERVICE_HOST,
            "port": SERVICE_PORT
        }, timeout=5)
        if r.status_code == 200:
            service_id = r.json().get("service_id")
            print(f"[{SERVICE_NAME}] Registered: {service_id}")
            # Запускаємо heartbeat тільки після успішної реєстрації
            if not heartbeat_started:
                threading.Thread(target=heartbeat_loop, daemon=True).start()
                heartbeat_started = True
    except Exception as e:
        print(f"[{SERVICE_NAME}] Registration failed: {e}")

def heartbeat_loop():
    while True:
        time.sleep(10)
        if service_id:
            try:
                requests.post(f"{REGISTRY_URL}/heartbeat/{service_id}", timeout=5)
            except:
                pass


# ============== SERVICE DISCOVERY ==============
def discover(service_name: str) -> str:
    """Знайти URL сервісу через Registry"""
    try:
        r = requests.get(f"{REGISTRY_URL}/discover/{service_name}", timeout=5)
        if r.status_code == 200:
            return r.json().get("url")
    except Exception as e:
        print(f"[Discovery] Failed to discover {service_name}: {e}")
    return None


async def proxy(service_name: str, path: str, request: Request, method: str = None):
    """Проксі запиту до мікросервісу"""
    url = discover(service_name)
    if not url:
        raise HTTPException(status_code=503, detail=f"Service '{service_name}' unavailable")
    
    target = f"{url}{path}"
    if request.url.query:
        target += f"?{request.url.query}"
    
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    try:
        resp = await http_client.request(
            method=method or request.method,
            url=target,
            content=body,
            headers={"Content-Type": "application/json"}
        )
        return JSONResponse(status_code=resp.status_code, content=resp.json() if resp.content else None)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Cannot connect to {service_name}")


# ============== СИСТЕМНІ ЕНДПОІНТИ ==============
@app.get("/")
def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "routes": {
            "/api/tasks": "task-service",
            "/api/categories": "category-service",
            "/api/notifications": "notification-service"
        }
    }


@app.get("/health")
async def health():
    """Перевірка стану всіх сервісів"""
    services = {}
    for svc in ["task-service", "category-service", "notification-service"]:
        url = discover(svc)
        if url:
            try:
                r = await http_client.get(f"{url}/health", timeout=3)
                services[svc] = "UP" if r.status_code == 200 else "DOWN"
            except:
                services[svc] = "DOWN"
        else:
            services[svc] = "NOT_REGISTERED"
    
    return {"status": "healthy", "gateway": "UP", "services": services}


@app.get("/services")
def list_services():
    """Список зареєстрованих сервісів"""
    try:
        r = requests.get(f"{REGISTRY_URL}/services", timeout=5)
        return r.json()
    except:
        return {"error": "Registry unavailable"}


# ============== TASK SERVICE (8001) ==============
@app.api_route("/api/tasks", methods=["GET", "POST"])
async def tasks_proxy(request: Request):
    return await proxy("task-service", "/tasks", request, request.method)


@app.api_route("/api/tasks/{task_id}", methods=["GET", "DELETE"])
async def task_by_id_proxy(task_id: int, request: Request):
    return await proxy("task-service", f"/tasks/{task_id}", request, request.method)


@app.patch("/api/tasks/{task_id}/status")
async def task_status_proxy(task_id: int, new_status: str):
    url = discover("task-service")
    if not url:
        raise HTTPException(status_code=503, detail="task-service unavailable")
    r = await http_client.patch(f"{url}/tasks/{task_id}/status?new_status={new_status}")
    return JSONResponse(status_code=r.status_code, content=r.json())


# ============== CATEGORY SERVICE (8002) ==============
@app.api_route("/api/categories", methods=["GET", "POST"])
async def categories_proxy(request: Request):
    return await proxy("category-service", "/categories", request, request.method)


@app.api_route("/api/categories/{category_id}", methods=["GET", "DELETE"])
async def category_by_id_proxy(category_id: int, request: Request):
    return await proxy("category-service", f"/categories/{category_id}", request, request.method)


# ============== NOTIFICATION SERVICE (8003) ==============
@app.get("/api/notifications/deadlines")
async def deadlines_proxy(minutes: int = 30):
    url = discover("notification-service")
    if not url:
        raise HTTPException(status_code=503, detail="notification-service unavailable")
    r = await http_client.get(f"{url}/deadlines/check?minutes={minutes}")
    return JSONResponse(status_code=r.status_code, content=r.json())


@app.post("/api/notifications/deadlines/analyze")
async def analyze_proxy():
    url = discover("notification-service")
    if not url:
        raise HTTPException(status_code=503, detail="notification-service unavailable")
    r = await http_client.post(f"{url}/deadlines/analyze")
    return JSONResponse(status_code=r.status_code, content=r.json())


@app.get("/api/notifications/statistics")
async def statistics_proxy():
    url = discover("notification-service")
    if not url:
        raise HTTPException(status_code=503, detail="notification-service unavailable")
    r = await http_client.get(f"{url}/statistics")
    return JSONResponse(status_code=r.status_code, content=r.json())


# ============== АГРЕГАЦІЯ ==============
@app.get("/api/dashboard")
async def dashboard():
    """Агрегація даних з усіх сервісів"""
    result = {"tasks": [], "categories": [], "statistics": {}, "deadlines": []}
    
    try:
        url = discover("task-service")
        if url:
            r = await http_client.get(f"{url}/tasks?limit=10")
            if r.status_code == 200:
                result["tasks"] = r.json()
    except: pass
    
    try:
        url = discover("category-service")
        if url:
            r = await http_client.get(f"{url}/categories")
            if r.status_code == 200:
                result["categories"] = r.json()
    except: pass
    
    try:
        url = discover("notification-service")
        if url:
            r = await http_client.get(f"{url}/statistics")
            if r.status_code == 200:
                result["statistics"] = r.json()
            r = await http_client.get(f"{url}/deadlines/check?minutes=60")
            if r.status_code == 200:
                result["deadlines"] = r.json()
    except: pass
    
    return result


@app.on_event("startup")
def startup():
    register_service()


@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()


if __name__ == "__main__":
    print("=" * 60)
    print(f"API GATEWAY - порт {SERVICE_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
