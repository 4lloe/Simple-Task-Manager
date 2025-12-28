# Simple Task Manager - Task Registry Service (svc_task_core)

## Практична робота №5 — Комплексування сервісної архітектури
**Дисципліна:** Сервіс-орієнтована архітектура програмного забезпечення  
**Студент:** Малий Д.Д., гр. КНТ-22-4  
**ХНУРЕ, 2025**

---

## Опис проекту

Комплексна система управління завданнями **Simple Task Manager**, яка об'єднує:
- **Backend (ПЗ-4):** Python FastAPI мікросервіс
- **Database (ПЗ-2):** MySQL з тригерами автоматичних нагадувань
- **Service Registry (ПЗ-3):** Service Discovery через збережені процедури
- **Frontend (ПЗ-5):** Веб-інтерфейс (SPA) для користувача

### Функціональність:
- **GET /categories:** Отримання списку категорій для веб-форми
- **GET /tasks:** Отримання списку завдань для дашборду
- **POST /tasks:** Додавання нового завдання з валідацією
- **Service Discovery:** Динамічний пошук адреси БД через Реєстр сервісів
- **Auto-Reminders:** Тригери БД автоматично створюють нагадування для High пріоритету

---

## Архітектура (Three-Tier)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│              index.html (SPA, JavaScript)                        │
│                     ↓ AJAX/Fetch API ↓                           │
├─────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                             │
│           app.py (FastAPI, Python, Port 8000)                    │
│                          ↓                                       │
│    registry.py → CALL GetServiceAddress('svc_task_core')         │
│                          ↓                                       │
├─────────────────────────────────────────────────────────────────┤
│                       DATA LAYER                                 │
│              MySQL (simpletaskmanager)                           │
│         Tables: Tasks, Categories, Reminders                     │
│         Triggers: AfterTaskInsert (auto-reminder)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Структура проекту

```
Simple Task Manager/
├── app.py              # Головний контролер (FastAPI) v2.0.0
├── config.py           # Модуль конфігурації БД
├── models.py           # Моделі даних (Pydantic + TaskViewModel)
├── registry.py         # Клієнт реєстру сервісів (Service Discovery)
├── index.html          # Веб-інтерфейс (SPA) — ПЗ №5
├── requirements.txt    # Залежності Python
├── tests.py            # Тести
└── README.md           # Документація
```

---

## Встановлення та запуск

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Запуск Backend сервісу

```bash
python app.py
```

Або через uvicorn:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Запуск Frontend

Відкрийте файл `index.html` у браузері або використайте Live Server.

### 4. Доступ до системи

- **Web UI:** Відкрити `index.html` у браузері
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

---

## API Endpoints

### GET /categories
Отримання списку категорій для випадаючого списку.

**Response:**
```json
[
  {"idCategory": 1, "CategoryName": "Робота"},
  {"idCategory": 2, "CategoryName": "Навчання"}
]
```

### GET /tasks
Отримання списку завдань для дашборду (останні 20).

**Response:**
```json
[
  {
    "idTask": 25,
    "Title": "Підготувати звіт з ПЗ №5",
    "Priority": "High",
    "Status": "Pending",
    "DueDate": "2025-12-30T10:00:00",
    "CategoryName": "Навчання"
  }
]
```

### POST /tasks
Створення нового завдання.

**Request Body:**
```json
{
  "user_id": 1,
  "category_id": 2,
  "title": "Здати практичну роботу №5",
  "description": "Комплексування сервісної архітектури",
  "priority": "High",
  "due_date": "2025-12-30T10:00:00"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "task_id": 25,
  "message": "Task created successfully. Auto-reminder triggers checked."
}
```

---

## Кольорова індикація пріоритетів

| Пріоритет | Колір | Опис |
|-----------|-------|------|
| 🔴 High | Червоний | Важливі завдання (автоматичне нагадування) |
| 🟡 Medium | Жовтий | Звичайні завдання |
| 🟢 Low | Зелений | Не термінові завдання |

---

## Технології

- **Python 3.10+** — мова програмування
- **FastAPI** — веб-фреймворк (Application Layer)
- **Pydantic** — валідація даних
- **MySQL** — СУБД (Data Layer)
- **HTML/CSS/JavaScript** — веб-інтерфейс (Presentation Layer)
- **Uvicorn** — ASGI сервер

---

## Коди відповідей

| Код | Опис |
|-----|------|
| 200 | Успішний GET запит |
| 201 | Завдання успішно створено |
| 400 | Помилка валідації |
| 404 | Завдання не знайдено |
| 503 | Реєстр сервісів недоступний |

---

## Автор

**Малий Д.Д.**  
Група КНТ-22-4  
ХНУРЕ, 2025

