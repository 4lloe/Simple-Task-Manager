"""
Головний контролер (app.py)
Практична робота №5 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Task Registry Service (svc_task_core) - мікросервіс управління реєстром завдань.
Реалізує REST API для CRUD операцій із завданнями з використанням Service Discovery.
Версія 2.0.0 - додано комплексування з веб-інтерфейсом.
"""

import uvicorn
import mysql.connector
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from models import TaskCreateRequest, APIResponse, TaskViewModel
from registry import ServiceRegistryClient

# Ініціалізація FastAPI додатку
app = FastAPI(
    title="Simple Task Manager API",
    description="""
    ## Simple Task Manager - Сервіс управління завданнями (svc_task_core)
    
    Практична робота №5 з дисципліни «Сервіс-орієнтована архітектура ПЗ»
    Комплексування компонентів: Backend (ПЗ-4) + БД (ПЗ-2) + Реєстр (ПЗ-3) + Web UI
    
    ### Функціональність:
    * **GET /categories:** Отримання списку категорій для веб-форми
    * **GET /tasks:** Отримання списку завдань для дашборду
    * **POST /tasks:** Додавання нового завдання з валідацією
    * **Service Discovery:** Динамічний пошук адреси БД через Реєстр сервісів
    
    ### Автор:
    Студент гр. КНТ-22-4 Малий Д.Д.
    """,
    version="2.0.0",
    contact={
        "name": "Малий Д.Д.",
        "email": "malyi@example.com"
    }
)

# Налаштування CORS для доступу з браузера (веб-інтерфейс)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PATCH"],
    allow_headers=["*"],
)


# ============================================================================
# ЕНДПОІНТИ ДЛЯ ВЕБ-ІНТЕРФЕЙСУ (ПЗ №5)
# ============================================================================

@app.get("/categories", tags=["Web UI"])
def get_categories():
    """
    Отримання списку категорій для випадаючого списку у веб-формі.
    Використовується для заповнення <select> елемента на фронтенді.
    """
    db_config = ServiceRegistryClient.get_db_config('svc_task_core')
    if not db_config:
        return []
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT idCategory, CategoryName FROM Categories")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@app.get("/tasks", response_model=List[TaskViewModel], tags=["Web UI"])
def get_tasks():
    """
    Отримання списку завдань для дашборду.
    Повертає останні 20 завдань з інформацією про категорію.
    """
    db_config = ServiceRegistryClient.get_db_config('svc_task_core')
    if not db_config:
        return []

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT t.idTask, t.Title, t.Priority, t.Status, t.DueDate, c.CategoryName
        FROM Tasks t
        LEFT JOIN Categories c ON t.Category_ID = c.idCategory
        ORDER BY t.CreatedAt DESC LIMIT 20
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# СИСТЕМНІ ЕНДПОІНТИ
# ============================================================================

@app.get("/", tags=["Health Check"])
def root():
    """
    Кореневий ендпоінт для перевірки працездатності сервісу.
    """
    return {
        "service": "Simple Task Manager API",
        "version": "2.0.0",
        "status": "running",
        "description": "Simple Task Manager - Практична робота №5 (Комплексування)"
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    """
    Перевірка здоров'я сервісу та доступності залежностей.
    """
    registry_available = ServiceRegistryClient.check_service_health('svc_task_core')
    return {
        "status": "healthy" if registry_available else "degraded",
        "registry_available": registry_available
    }


@app.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED,
    response_model=APIResponse,
    tags=["Tasks"],
    summary="Створення нового завдання",
    description="""
    Створює нове завдання в системі Simple Task Manager.
    
    **Алгоритм виконання:**
    1. Отримання HTTP-запиту POST /tasks
    2. Валідація JSON-тіла (Pydantic model)
    3. Запит до Реєстру Сервісів для отримання Connection String
    4. Відкриття транзакції
    5. INSERT запис у таблицю Tasks
    6. COMMIT транзакції (спрацьовує тригер нагадувань)
    7. Формування відповіді JSON
    
    **Примітка:** Якщо пріоритет 'High', тригер AfterTaskInsert (ПЗ-2) 
    автоматично створює запис у таблиці Reminders.
    """
)
def create_task(task: TaskCreateRequest):
    """
    Створення нового завдання в системі.
    
    Args:
        task (TaskCreateRequest): Дані для створення завдання
        
    Returns:
        APIResponse: Результат операції з ID створеного завдання
        
    Raises:
        HTTPException 400: Помилка валідації або БД
        HTTPException 503: Реєстр сервісів недоступний
    """
    conn = None
    cursor = None
    
    # 1. Service Discovery: Отримуємо доступ до БД через Реєстр
    try:
        # Шукаємо конфіг для ключа svc_task_core (визначено в ПЗ-3)
        db_config = ServiceRegistryClient.get_db_config('svc_task_core')
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database config not found in Registry"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Registry Error: {str(e)}"
        )

    # 2. Підключення до бізнес-БД
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Початок транзакції для забезпечення ACID
        conn.start_transaction()
        
        # 3. Вставка завдання
        sql = """
            INSERT INTO Tasks (User_ID, Category_ID, Title, Description, Priority, DueDate)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        vals = (
            task.user_id,
            task.category_id,
            task.title,
            task.description,
            task.priority,
            task.due_date
        )
        
        cursor.execute(sql, vals)
        new_task_id = cursor.lastrowid
        
        # 4. Commit транзакції
        # Тут автоматично спрацює тригер AfterTaskInsert (ПЗ-2),
        # якщо пріоритет High - створить запис у таблиці Reminders
        conn.commit()
        
        return APIResponse(
            success=True,
            task_id=new_task_id,
            message="Task created successfully. Auto-reminder triggers checked."
        )

    except mysql.connector.IntegrityError as e:
        # Помилка цілісності (наприклад, неіснуючий User_ID або Category_ID)
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity Error: Invalid User_ID or Category_ID. {str(e)}"
        )
    except mysql.connector.Error as e:
        # Інші помилки БД
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database Error: {str(e)}"
        )
    finally:
        # Закриття ресурсів
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Отримання завдання за ID"
)
def get_task(task_id: int):
    """
    Отримання інформації про завдання за його ID.
    
    Args:
        task_id (int): ID завдання
        
    Returns:
        dict: Дані завдання
    """
    conn = None
    cursor = None
    
    try:
        db_config = ServiceRegistryClient.get_db_config('svc_task_core')
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database config not found in Registry"
            )
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM Tasks WHERE idTask = %s"
        cursor.execute(sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.patch(
    "/tasks/{task_id}/status",
    tags=["Tasks"],
    summary="Оновлення статусу завдання"
)
def update_task_status(task_id: int, new_status: str):
    """
    Оновлення статусу завдання (управління життєвим циклом).
    
    Можливі переходи: Pending -> In_Progress -> Completed
    
    Args:
        task_id (int): ID завдання
        new_status (str): Новий статус (Pending, In_Progress, Completed)
    """
    valid_statuses = ['Pending', 'In_Progress', 'Completed']
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    conn = None
    cursor = None
    
    try:
        db_config = ServiceRegistryClient.get_db_config('svc_task_core')
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database config not found in Registry"
            )
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        conn.start_transaction()
        
        sql = "UPDATE Tasks SET Status = %s WHERE idTask = %s"
        cursor.execute(sql, (new_status, task_id))
        
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        
        conn.commit()
        
        return APIResponse(
            success=True,
            task_id=task_id,
            message=f"Task status updated to '{new_status}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Запуск сервера на порту 8000 для веб-інтерфейсу (ПЗ-5)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
