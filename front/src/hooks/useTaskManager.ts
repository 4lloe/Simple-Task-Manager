import { useState, useEffect, useCallback } from 'react';
import { Task, Category, Priority, TaskStatus, CreateTaskPayload } from '@/types/task';
import { toast } from 'sonner';
import { 
  fetchTasks, 
  fetchCategories, 
  createTaskAPI, 
  updateTaskStatusAPI,
  TaskFromAPI,
  checkHealth 
} from '@/api/taskApi';

// Fallback mock категорії (якщо бекенд недоступний)
const mockCategories: Category[] = [
  { idCategory: 1, CategoryName: 'Робота' },
  { idCategory: 2, CategoryName: 'Навчання' },
  { idCategory: 3, CategoryName: 'Особисте' },
  { idCategory: 4, CategoryName: 'Проект' },
];

/**
 * Конвертація завдання з API формату у фронтенд формат
 */
const mapTaskFromAPI = (apiTask: TaskFromAPI): Task => {
  const dueDate = apiTask.DueDate ? new Date(apiTask.DueDate) : null;
  const now = new Date();
  
  // Визначаємо статус: якщо Pending і прострочено - ставимо Overdue
  let status: TaskStatus = apiTask.Status as TaskStatus;
  if (status === 'Pending' && dueDate && dueDate < now) {
    status = 'Overdue';
  }
  // Маппінг In_Progress -> Pending для сумісності
  if (apiTask.Status === 'In_Progress') {
    status = 'Pending';
  }
  
  return {
    id: apiTask.idTask,
    title: apiTask.Title,
    description: '',
    categoryId: 0,
    categoryName: apiTask.CategoryName || 'Без категорії',
    priority: apiTask.Priority as Priority,
    status,
    dueDate,
    createdAt: new Date(),
    completedAt: status === 'Completed' ? new Date() : null,
  };
};

// Звуковий сигнал для нагадувань
const playNotificationSound = () => {
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  oscillator.frequency.value = 800;
  oscillator.type = 'sine';
  
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
  
  oscillator.start(audioContext.currentTime);
  oscillator.stop(audioContext.currentTime + 0.5);
};

export const useTaskManager = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [categories, setCategories] = useState<Category[]>(mockCategories);
  const [isLoading, setIsLoading] = useState(true);
  const [isBackendAvailable, setIsBackendAvailable] = useState(false);
  const [notifiedTasks, setNotifiedTasks] = useState<Set<number>>(new Set());

  // Завантаження даних з бекенду
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      
      // Перевіряємо доступність бекенду
      const backendOk = await checkHealth();
      setIsBackendAvailable(backendOk);
      
      if (backendOk) {
        try {
          // Завантажуємо категорії з бекенду
          const apiCategories = await fetchCategories();
          if (apiCategories.length > 0) {
            setCategories(apiCategories);
          }
          
          // Завантажуємо завдання з бекенду
          const apiTasks = await fetchTasks();
          const mappedTasks = apiTasks.map(mapTaskFromAPI);
          setTasks(mappedTasks);
          
          toast.success('Дані завантажено з сервера', {
            description: `Завдань: ${mappedTasks.length}, Категорій: ${apiCategories.length}`,
          });
        } catch (error) {
          console.error('Error loading data from backend:', error);
          toast.error('Помилка завантаження', {
            description: 'Не вдалося отримати дані з сервера',
          });
          setTasks([]);
        }
      } else {
        toast.warning('Бекенд недоступний', {
          description: 'Переконайтесь, що сервер запущено на порту 8000',
        });
        setTasks([]);
      }
      
      setIsLoading(false);
    };

    loadData();
  }, []);

  // Перевірка статусу "Прострочено"
  const checkOverdueTasks = useCallback(() => {
    const now = new Date();
    setTasks(prev => prev.map(task => {
      if (task.status === 'Pending' && task.dueDate && new Date(task.dueDate) < now) {
        return { ...task, status: 'Overdue' as TaskStatus };
      }
      return task;
    }));
  }, []);

  // Перевірка нагадувань (за 30 хв до дедлайну)
  const checkReminders = useCallback(() => {
    const now = new Date();
    const thirtyMinutes = 30 * 60 * 1000;

    tasks.forEach(task => {
      if (
        task.status === 'Pending' &&
        task.dueDate &&
        !notifiedTasks.has(task.id)
      ) {
        const timeUntilDue = new Date(task.dueDate).getTime() - now.getTime();
        
        if (timeUntilDue > 0 && timeUntilDue <= thirtyMinutes) {
          playNotificationSound();
          toast.warning(`⏰ Нагадування: "${task.title}"`, {
            description: `До дедлайну залишилось ${Math.round(timeUntilDue / 60000)} хв`,
            duration: 8000,
          });
          setNotifiedTasks(prev => new Set([...prev, task.id]));
        }
      }
    });
  }, [tasks, notifiedTasks]);

  // Інтервали перевірки
  useEffect(() => {
    const overdueInterval = setInterval(checkOverdueTasks, 60000);
    const reminderInterval = setInterval(checkReminders, 30000);
    
    checkOverdueTasks();
    checkReminders();

    return () => {
      clearInterval(overdueInterval);
      clearInterval(reminderInterval);
    };
  }, [checkOverdueTasks, checkReminders]);

  // Створення завдання
  const createTask = useCallback(async (payload: CreateTaskPayload) => {
    const category = categories.find(c => c.idCategory === payload.category_id);
    
    if (isBackendAvailable) {
      try {
        // Відправляємо на бекенд
        const response = await createTaskAPI({
          user_id: 1,
          category_id: payload.category_id,
          title: payload.title,
          description: payload.description,
          priority: payload.priority,
          due_date: payload.due_date,
        });
        
        if (response.success && response.task_id) {
          const newTask: Task = {
            id: response.task_id,
            title: payload.title,
            description: payload.description,
            categoryId: payload.category_id,
            categoryName: category?.CategoryName || 'Без категорії',
            priority: payload.priority,
            status: 'Pending',
            dueDate: payload.due_date ? new Date(payload.due_date) : null,
            createdAt: new Date(),
            completedAt: null,
          };

          setTasks(prev => [newTask, ...prev]);
          
          playNotificationSound();
          toast.success('Завдання створено на сервері!', {
            description: payload.priority === 'High' 
              ? 'Автоматичне нагадування активовано'
              : newTask.title,
          });

          return newTask;
        }
      } catch (error) {
        console.error('Error creating task:', error);
        toast.error('Помилка створення завдання', {
          description: error instanceof Error ? error.message : 'Невідома помилка',
        });
        return null;
      }
    } else {
      // Локальне створення, якщо бекенд недоступний
      const newTask: Task = {
        id: Date.now(),
        title: payload.title,
        description: payload.description,
        categoryId: payload.category_id,
        categoryName: category?.CategoryName || 'Без категорії',
        priority: payload.priority,
        status: 'Pending',
        dueDate: payload.due_date ? new Date(payload.due_date) : null,
        createdAt: new Date(),
        completedAt: null,
      };

      setTasks(prev => [newTask, ...prev]);
      
      playNotificationSound();
      toast.warning('Завдання створено локально', {
        description: 'Бекенд недоступний - дані не збережено на сервері',
      });

      return newTask;
    }
    
    return null;
  }, [categories, isBackendAvailable]);

  // Позначити як виконане
  const toggleTaskComplete = useCallback(async (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    const isCompleting = task.status !== 'Completed';
    const newStatus: TaskStatus = isCompleting ? 'Completed' : 
      (task.dueDate && new Date(task.dueDate) < new Date() ? 'Overdue' : 'Pending');
    
    // Маппінг статусу для API
    const apiStatus = newStatus === 'Overdue' ? 'Pending' : newStatus;
    
    if (isBackendAvailable) {
      try {
        await updateTaskStatusAPI(taskId, apiStatus);
        
        setTasks(prev => prev.map(t => {
          if (t.id === taskId) {
            if (isCompleting) {
              playNotificationSound();
              toast.success('Завдання виконано! ✓', { description: t.title });
            } else {
              toast.info('Статус скасовано', { description: t.title });
            }
            return {
              ...t,
              status: newStatus,
              completedAt: isCompleting ? new Date() : null,
            };
          }
          return t;
        }));
      } catch (error) {
        console.error('Error updating task status:', error);
        toast.error('Помилка оновлення статусу', {
          description: error instanceof Error ? error.message : 'Невідома помилка',
        });
      }
    } else {
      // Локальне оновлення
      setTasks(prev => prev.map(t => {
        if (t.id === taskId) {
          if (isCompleting) {
            playNotificationSound();
            toast.success('Завдання виконано! ✓', { description: t.title });
          } else {
            toast.info('Статус скасовано', { description: t.title });
          }
          return {
            ...t,
            status: newStatus,
            completedAt: isCompleting ? new Date() : null,
          };
        }
        return t;
      }));
    }
  }, [tasks, isBackendAvailable]);

  // Видалення завдання
  const deleteTask = useCallback((taskId: number) => {
    setTasks(prev => prev.filter(t => t.id !== taskId));
    toast.info('Завдання видалено');
  }, []);

  // Оновлення даних з сервера
  const refreshTasks = useCallback(async () => {
    if (!isBackendAvailable) {
      toast.warning('Бекенд недоступний');
      return;
    }
    
    setIsLoading(true);
    try {
      const apiTasks = await fetchTasks();
      const mappedTasks = apiTasks.map(mapTaskFromAPI);
      setTasks(mappedTasks);
      toast.success('Дані оновлено');
    } catch (error) {
      toast.error('Помилка оновлення');
    }
    setIsLoading(false);
  }, [isBackendAvailable]);

  return {
    tasks,
    categories,
    isLoading,
    isBackendAvailable,
    createTask,
    toggleTaskComplete,
    deleteTask,
    refreshTasks,
  };
};
