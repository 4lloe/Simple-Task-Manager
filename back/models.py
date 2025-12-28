"""
Модуль моделей даних (models.py)
Практична робота №5 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Використовується Pydantic для валідації вхідних/вихідних даних REST API.
Розширено для підтримки веб-інтерфейсу (TaskViewModel).
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """
    Модель запиту на створення нового завдання.
    Реалізує валідацію на рівні додатку (Pydantic).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "category_id": 2,
                "title": "Здати практичну роботу №5",
                "description": "Комплексування сервісної архітектури",
                "priority": "High",
                "due_date": "2025-12-30T10:00:00"
            }
        }
    )
    
    user_id: int = Field(1, gt=0, description="ID користувача (заглушка)")
    category_id: Optional[int] = Field(None, gt=0, description="ID категорії")
    title: str = Field(..., min_length=3, max_length=150, description="Заголовок завдання")
    description: Optional[str] = Field("", description="Опис завдання")
    priority: str = Field('Medium', pattern='^(Low|Medium|High)$', description="Пріоритет: Low, Medium, High")
    due_date: Optional[datetime] = Field(None, description="Дедлайн виконання")

    @field_validator('due_date')
    @classmethod
    def validate_date(cls, v):
        """
        Валідатор для перевірки, що дедлайн не є у минулому.
        Забезпечує вимогу до надійності з ТЗ.
        """
        if v and v < datetime.now():
            raise ValueError('Дедлайн не може бути у минулому')
        return v


class TaskViewModel(BaseModel):
    """
    Модель для відображення завдання у веб-інтерфейсі.
    Використовується для GET /tasks ендпоінту (дашборд).
    """
    idTask: int
    Title: str
    Priority: str
    Status: str
    DueDate: Optional[datetime] = None
    CategoryName: Optional[str] = None


class APIResponse(BaseModel):
    """
    Стандартна модель відповіді API.
    Забезпечує уніфікований формат відповідей сервісу.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "task_id": 15,
                "message": "Task created successfully. Auto-reminder triggers checked."
            }
        }
    )
    
    success: bool = Field(..., description="Статус виконання операції")
    task_id: Optional[int] = Field(None, description="ID створеного завдання")
    message: str = Field(..., description="Повідомлення про результат операції")


class TaskResponse(BaseModel):
    """
    Модель відповіді з даними завдання.
    """
    task_id: int
    user_id: int
    category_id: Optional[int]
    title: str
    description: Optional[str]
    priority: str
    status: str
    due_date: Optional[datetime]
    created_at: datetime
