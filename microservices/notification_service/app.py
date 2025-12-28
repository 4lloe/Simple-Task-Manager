"""
Notification Service (Мікросервіс сповіщень)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Порт: 8003
"""

import uvicorn
import mysql.connector
import requests
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

SERVICE_NAME = "notification-service"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8003
REGISTRY_URL = "http://127.0.0.1:8500"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1972',
    'database': 'simpletaskmanager'
}

app = FastAPI(
    title="Notification Service",
    description="Мікросервіс сповіщень та нагадувань",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== МОДЕЛІ ==============
class DeadlineAlert(BaseModel):
    task_id: int
    title: str
    priority: str
    due_date: datetime
    time_remaining_minutes: int
    alert_level: str


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


@app.get("/deadlines/check", response_model=List[DeadlineAlert])
def check_deadlines(minutes: int = 30):
    """Перевірка наближення дедлайнів"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        now = datetime.now()
        threshold = now + timedelta(minutes=minutes)
        
        cursor.execute("""
            SELECT idTask, Title, Priority, DueDate
            FROM Tasks
            WHERE Status = 'Pending' AND DueDate IS NOT NULL AND DueDate <= %s
            ORDER BY DueDate ASC
        """, (threshold,))
        
        alerts = []
        for task in cursor.fetchall():
            due = task['DueDate']
            remaining = (due - now).total_seconds() / 60
            
            if remaining < 0:
                level = "overdue"
            elif remaining <= 15:
                level = "critical"
            else:
                level = "warning"
            
            alerts.append(DeadlineAlert(
                task_id=task['idTask'],
                title=task['Title'],
                priority=task['Priority'],
                due_date=due,
                time_remaining_minutes=int(remaining),
                alert_level=level
            ))
        return alerts
    finally:
        cursor.close()
        conn.close()


@app.post("/deadlines/analyze")
def analyze_overdue():
    """Аналіз та оновлення прострочених завдань"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        now = datetime.now()
        
        cursor.execute("""
            SELECT idTask, Title, Priority, DueDate
            FROM Tasks WHERE Status = 'Pending' AND DueDate < %s
        """, (now,))
        overdue = cursor.fetchall()
        
        if overdue:
            ids = [t['idTask'] for t in overdue]
            placeholders = ','.join(['%s'] * len(ids))
            cursor.execute(f"UPDATE Tasks SET Status = 'Overdue' WHERE idTask IN ({placeholders})", ids)
            conn.commit()
        
        return {
            "success": True,
            "analyzed_at": now.isoformat(),
            "overdue_count": len(overdue),
            "updated_count": cursor.rowcount if overdue else 0,
            "tasks": overdue
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/statistics")
def get_statistics():
    """Статистика завдань"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT Status, COUNT(*) as count FROM Tasks GROUP BY Status")
        by_status = {r['Status']: r['count'] for r in cursor.fetchall()}
        
        cursor.execute("SELECT Priority, COUNT(*) as count FROM Tasks GROUP BY Priority")
        by_priority = {r['Priority']: r['count'] for r in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) as count FROM Tasks WHERE Status='Pending' AND DueDate < NOW()")
        overdue = cursor.fetchone()['count']
        
        return {
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue_pending": overdue,
            "total": sum(by_status.values())
        }
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup():
    register_service()


if __name__ == "__main__":
    print("=" * 60)
    print(f"NOTIFICATION SERVICE - порт {SERVICE_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
