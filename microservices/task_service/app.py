"""
Task Service (Мікросервіс управління завданнями)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Порт: 8001
"""

import uvicorn
import mysql.connector
import requests
import threading
import time
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

SERVICE_NAME = "task-service"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8001
REGISTRY_URL = "http://127.0.0.1:8500"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1972',
    'database': 'simpletaskmanager'
}

app = FastAPI(
    title="Task Service",
    description="Мікросервіс управління завданнями",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== МОДЕЛІ ==============
class TaskCreate(BaseModel):
    user_id: int = 1
    category_id: Optional[int] = None
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = ""
    priority: str = Field('Medium', pattern='^(Low|Medium|High)$')
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    idTask: int
    Title: str
    Priority: str
    Status: str
    DueDate: Optional[datetime] = None
    CategoryName: Optional[str] = None


class APIResponse(BaseModel):
    success: bool
    task_id: Optional[int] = None
    message: str


# ============== БАЗА ДАНИХ ==============
def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ============== РЕЄСТРАЦІЯ ==============
service_id = None

def register_service():
    global service_id
    try:
        r = requests.post(f"{REGISTRY_URL}/register", json={
            "service_name": SERVICE_NAME,
            "host": SERVICE_HOST,
            "port": SERVICE_PORT
        }, timeout=5)
        if r.status_code == 200:
            service_id = r.json().get("service_id")
            print(f"[{SERVICE_NAME}] Registered: {service_id}")
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

threading.Thread(target=heartbeat_loop, daemon=True).start()


# ============== ЕНДПОІНТИ ==============
@app.get("/health")
def health():
    return {"status": "healthy", "service": SERVICE_NAME, "port": SERVICE_PORT}


@app.post("/tasks", status_code=201, response_model=APIResponse)
def create_task(task: TaskCreate):
    """Створення завдання"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Tasks (User_ID, Category_ID, Title, Priority, Status, DueDate, CreatedAt)
            VALUES (%s, %s, %s, %s, 'Pending', %s, NOW())
        """, (task.user_id, task.category_id, task.title, task.priority, task.due_date))
        conn.commit()
        return APIResponse(success=True, task_id=cursor.lastrowid, message="Task created")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(status_filter: Optional[str] = None, priority: Optional[str] = None, limit: int = 20):
    """Отримання завдань"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT t.idTask, t.Title, t.Priority, t.Status, t.DueDate, c.CategoryName
            FROM Tasks t
            LEFT JOIN Categories c ON t.Category_ID = c.idCategory
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND t.Status = %s"
            params.append(status_filter)
        if priority:
            query += " AND t.Priority = %s"
            params.append(priority)
        query += " ORDER BY t.CreatedAt DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    """Отримання завдання за ID"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.idTask, t.Title, t.Priority, t.Status, t.DueDate, c.CategoryName
            FROM Tasks t
            LEFT JOIN Categories c ON t.Category_ID = c.idCategory
            WHERE t.idTask = %s
        """, (task_id,))
        task = cursor.fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    finally:
        cursor.close()
        conn.close()


@app.patch("/tasks/{task_id}/status", response_model=APIResponse)
def update_status(task_id: int, new_status: str):
    """Оновлення статусу"""
    if new_status not in ['Pending', 'Completed', 'Overdue']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Tasks SET Status = %s WHERE idTask = %s", (new_status, task_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return APIResponse(success=True, task_id=task_id, message=f"Status updated to {new_status}")
    finally:
        cursor.close()
        conn.close()


@app.delete("/tasks/{task_id}", response_model=APIResponse)
def delete_task(task_id: int):
    """Видалення завдання"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Tasks WHERE idTask = %s", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return APIResponse(success=True, task_id=task_id, message="Task deleted")
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup():
    register_service()


if __name__ == "__main__":
    print("=" * 60)
    print(f"TASK SERVICE - порт {SERVICE_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
