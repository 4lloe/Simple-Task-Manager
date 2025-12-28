"""
Модуль тестування (tests.py)
Практична робота №4 - Simple Task Manager
Студент: Малий Д.Д., КНТ-22-4

Тести для перевірки працездатності сервісу Task Registry Service.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import app
from models import TaskCreateRequest, APIResponse


# Тестовий клієнт FastAPI
client = TestClient(app)


# ============================================
# Тести ендпоінтів Health Check
# ============================================

class TestHealthCheck:
    """Тести перевірки здоров'я сервісу"""
    
    def test_root_endpoint(self):
        """Тест кореневого ендпоінта"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Task Registry Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Тест ендпоінта health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "registry_available" in data


# ============================================
# Тести валідації моделей Pydantic
# ============================================

class TestTaskCreateRequestValidation:
    """Тести валідації моделі TaskCreateRequest"""
    
    def test_valid_task_creation(self):
        """Тест створення валідного завдання"""
        task = TaskCreateRequest(
            user_id=1,
            category_id=2,
            title="Тестове завдання",
            description="Опис завдання",
            priority="High",
            due_date=datetime.now() + timedelta(days=7)
        )
        assert task.user_id == 1
        assert task.title == "Тестове завдання"
        assert task.priority == "High"
    
    def test_minimal_task_creation(self):
        """Тест створення завдання з мінімальними полями"""
        task = TaskCreateRequest(
            user_id=1,
            title="Мінімальне завдання"
        )
        assert task.user_id == 1
        assert task.category_id is None
        assert task.priority == "Medium"  # значення за замовчуванням
    
    def test_invalid_user_id_zero(self):
        """Тест: user_id не може бути 0"""
        with pytest.raises(ValueError):
            TaskCreateRequest(user_id=0, title="Тест")
    
    def test_invalid_user_id_negative(self):
        """Тест: user_id не може бути від'ємним"""
        with pytest.raises(ValueError):
            TaskCreateRequest(user_id=-1, title="Тест")
    
    def test_invalid_title_too_short(self):
        """Тест: заголовок занадто короткий (менше 3 символів)"""
        with pytest.raises(ValueError):
            TaskCreateRequest(user_id=1, title="AB")
    
    def test_invalid_title_too_long(self):
        """Тест: заголовок занадто довгий (більше 150 символів)"""
        with pytest.raises(ValueError):
            TaskCreateRequest(user_id=1, title="A" * 151)
    
    def test_invalid_priority(self):
        """Тест: некоректне значення пріоритету"""
        with pytest.raises(ValueError):
            TaskCreateRequest(user_id=1, title="Тест", priority="Invalid")
    
    def test_valid_priorities(self):
        """Тест: всі допустимі значення пріоритету"""
        for priority in ["Low", "Medium", "High"]:
            task = TaskCreateRequest(user_id=1, title="Тест", priority=priority)
            assert task.priority == priority
    
    def test_due_date_in_past(self):
        """Тест: дедлайн не може бути у минулому"""
        with pytest.raises(ValueError) as exc_info:
            TaskCreateRequest(
                user_id=1,
                title="Тест",
                due_date=datetime.now() - timedelta(days=1)
            )
        assert "минулому" in str(exc_info.value)
    
    def test_due_date_in_future(self):
        """Тест: дедлайн у майбутньому - валідний"""
        future_date = datetime.now() + timedelta(days=30)
        task = TaskCreateRequest(
            user_id=1,
            title="Тест",
            due_date=future_date
        )
        assert task.due_date == future_date


# ============================================
# Тести моделі APIResponse
# ============================================

class TestAPIResponseModel:
    """Тести моделі відповіді API"""
    
    def test_success_response(self):
        """Тест успішної відповіді"""
        response = APIResponse(
            success=True,
            task_id=15,
            message="Task created successfully"
        )
        assert response.success is True
        assert response.task_id == 15
    
    def test_error_response(self):
        """Тест відповіді з помилкою"""
        response = APIResponse(
            success=False,
            task_id=None,
            message="Validation error"
        )
        assert response.success is False
        assert response.task_id is None


# ============================================
# Тести API ендпоінтів з мокуванням БД
# ============================================

class TestTasksAPI:
    """Тести API ендпоінтів для завдань"""
    
    @patch('app.ServiceRegistryClient.get_db_config')
    @patch('app.mysql.connector.connect')
    def test_create_task_success(self, mock_connect, mock_get_config):
        """Тест успішного створення завдання"""
        # Налаштування моків
        mock_get_config.return_value = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'SimpleTaskManager'
        }
        
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 100
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Виконання запиту
        response = client.post("/tasks", json={
            "user_id": 1,
            "category_id": 2,
            "title": "Тестове завдання",
            "priority": "High",
            "due_date": "2025-12-30T10:00:00"
        })
        
        # Перевірка
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["task_id"] == 100
    
    @patch('app.ServiceRegistryClient.get_db_config')
    def test_create_task_registry_unavailable(self, mock_get_config):
        """Тест: реєстр сервісів недоступний"""
        mock_get_config.side_effect = Exception("Registry Unavailable")
        
        response = client.post("/tasks", json={
            "user_id": 1,
            "title": "Тест"
        })
        
        assert response.status_code == 503
        assert "Registry" in response.json()["detail"]
    
    @patch('app.ServiceRegistryClient.get_db_config')
    def test_create_task_db_config_not_found(self, mock_get_config):
        """Тест: конфігурація БД не знайдена"""
        mock_get_config.return_value = None
        
        response = client.post("/tasks", json={
            "user_id": 1,
            "title": "Тест"
        })
        
        assert response.status_code == 503
        assert "not found" in response.json()["detail"]
    
    def test_create_task_validation_error_empty_title(self):
        """Тест: валідація - пустий заголовок"""
        response = client.post("/tasks", json={
            "user_id": 1,
            "title": ""
        })
        
        assert response.status_code == 422  # Validation Error
    
    def test_create_task_validation_error_missing_user_id(self):
        """Тест: валідація - відсутній user_id"""
        response = client.post("/tasks", json={
            "title": "Тестове завдання"
        })
        
        assert response.status_code == 422
    
    def test_create_task_validation_error_invalid_priority(self):
        """Тест: валідація - некоректний пріоритет"""
        response = client.post("/tasks", json={
            "user_id": 1,
            "title": "Тест",
            "priority": "Urgent"  # Невірне значення
        })
        
        assert response.status_code == 422
    
    @patch('app.ServiceRegistryClient.get_db_config')
    @patch('app.mysql.connector.connect')
    def test_get_task_success(self, mock_connect, mock_get_config):
        """Тест отримання завдання за ID"""
        mock_get_config.return_value = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'SimpleTaskManager'
        }
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'Task_ID': 1,
            'User_ID': 1,
            'Title': 'Тест',
            'Status': 'Pending'
        }
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        response = client.get("/tasks/1")
        
        assert response.status_code == 200
    
    @patch('app.ServiceRegistryClient.get_db_config')
    @patch('app.mysql.connector.connect')
    def test_get_task_not_found(self, mock_connect, mock_get_config):
        """Тест: завдання не знайдено"""
        mock_get_config.return_value = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'SimpleTaskManager'
        }
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        response = client.get("/tasks/999")
        
        assert response.status_code == 404
    
    @patch('app.ServiceRegistryClient.get_db_config')
    @patch('app.mysql.connector.connect')
    def test_update_task_status_success(self, mock_connect, mock_get_config):
        """Тест оновлення статусу завдання"""
        mock_get_config.return_value = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'SimpleTaskManager'
        }
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        response = client.patch("/tasks/1/status?new_status=In_Progress")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_update_task_status_invalid(self):
        """Тест: некоректний статус"""
        response = client.patch("/tasks/1/status?new_status=Invalid")
        
        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]


# ============================================
# Запуск тестів
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
