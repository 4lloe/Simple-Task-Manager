"""
Category Service (Мікросервіс управління категоріями)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Порт: 8002
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

SERVICE_NAME = "category-service"
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8002
REGISTRY_URL = "http://127.0.0.1:8500"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1972',
    'database': 'simpletaskmanager'
}

app = FastAPI(
    title="Category Service",
    description="Мікросервіс управління категоріями",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== МОДЕЛІ ==============
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class CategoryResponse(BaseModel):
    idCategory: int
    CategoryName: str


class APIResponse(BaseModel):
    success: bool
    category_id: Optional[int] = None
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


@app.get("/categories", response_model=List[CategoryResponse])
def get_categories():
    """Отримання списку категорій"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT idCategory, CategoryName FROM Categories ORDER BY CategoryName")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@app.post("/categories", status_code=201, response_model=APIResponse)
def create_category(cat: CategoryCreate):
    """Створення категорії"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT idCategory FROM Categories WHERE CategoryName = %s", (cat.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Category already exists")
        
        cursor.execute("INSERT INTO Categories (CategoryName) VALUES (%s)", (cat.name,))
        conn.commit()
        return APIResponse(success=True, category_id=cursor.lastrowid, message="Category created")
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int):
    """Отримання категорії за ID"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT idCategory, CategoryName FROM Categories WHERE idCategory = %s", 
                      (category_id,))
        cat = cursor.fetchone()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        return cat
    finally:
        cursor.close()
        conn.close()


@app.delete("/categories/{category_id}", response_model=APIResponse)
def delete_category(category_id: int):
    """Видалення категорії"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Tasks WHERE Category_ID = %s", (category_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            raise HTTPException(status_code=409, detail=f"Cannot delete: {count} tasks use this category")
        
        cursor.execute("DELETE FROM Categories WHERE idCategory = %s", (category_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        return APIResponse(success=True, category_id=category_id, message="Category deleted")
    except HTTPException:
        raise
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup():
    register_service()


if __name__ == "__main__":
    print("=" * 60)
    print(f"CATEGORY SERVICE - порт {SERVICE_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
