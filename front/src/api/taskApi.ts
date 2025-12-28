/**
 * API клієнт для взаємодії з бекендом Simple Task Manager
 * Практична робота №5 - Комплексування компонентів
 */

// URL бекенду - CORS вже налаштований у FastAPI
const API_BASE_URL = 'http://127.0.0.1:8000';

export interface TaskFromAPI {
  idTask: number;
  Title: string;
  Priority: string;
  Status: string;
  DueDate: string | null;
  CategoryName: string | null;
}

export interface CategoryFromAPI {
  idCategory: number;
  CategoryName: string;
}

export interface CreateTaskPayload {
  user_id?: number;
  category_id: number | null;
  title: string;
  description: string;
  priority: string;
  due_date: string | null;
}

export interface APIResponse {
  success: boolean;
  task_id: number | null;
  message: string;
}

/**
 * Отримання списку завдань з бекенду
 */
export async function fetchTasks(): Promise<TaskFromAPI[]> {
  const response = await fetch(`${API_BASE_URL}/tasks`);
  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Отримання списку категорій з бекенду
 */
export async function fetchCategories(): Promise<CategoryFromAPI[]> {
  const response = await fetch(`${API_BASE_URL}/categories`);
  if (!response.ok) {
    throw new Error(`Failed to fetch categories: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Створення нового завдання
 */
export async function createTaskAPI(payload: CreateTaskPayload): Promise<APIResponse> {
  const response = await fetch(`${API_BASE_URL}/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to create task');
  }
  
  return response.json();
}

/**
 * Оновлення статусу завдання
 */
export async function updateTaskStatusAPI(taskId: number, newStatus: string): Promise<APIResponse> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/status?new_status=${newStatus}`, {
    method: 'PATCH',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to update task status');
  }
  
  return response.json();
}

/**
 * Перевірка доступності бекенду
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
