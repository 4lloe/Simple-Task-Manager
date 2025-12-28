import { useState, useEffect, useCallback } from 'react';
import { Task, Category, Priority, TaskStatus, CreateTaskPayload } from '@/types/task';
import { toast } from 'sonner';

// Mock categories для демонстрації
const mockCategories: Category[] = [
  { idCategory: 1, CategoryName: 'Робота' },
  { idCategory: 2, CategoryName: 'Навчання' },
  { idCategory: 3, CategoryName: 'Особисте' },
  { idCategory: 4, CategoryName: 'Проект' },
];

// Генерація початкових завдань
const generateInitialTasks = (): Task[] => {
  const now = new Date();
  return [
    {
      id: 1,
      title: 'Підготувати звіт з ПЗ №5',
      description: 'Комплексування сервісної архітектури',
      categoryId: 2,
      categoryName: 'Навчання',
      priority: 'High',
      status: 'Pending',
      dueDate: new Date(now.getTime() + 2 * 60 * 60 * 1000),
      createdAt: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      completedAt: null,
    },
    {
      id: 2,
      title: 'Зустріч з командою',
      description: 'Обговорення архітектури системи',
      categoryId: 1,
      categoryName: 'Робота',
      priority: 'Medium',
      status: 'Pending',
      dueDate: new Date(now.getTime() + 48 * 60 * 60 * 1000),
      createdAt: new Date(now.getTime() - 12 * 60 * 60 * 1000),
      completedAt: null,
    },
    {
      id: 3,
      title: 'Прострочене завдання',
      description: 'Це завдання вже прострочено',
      categoryId: 3,
      categoryName: 'Особисте',
      priority: 'Low',
      status: 'Overdue',
      dueDate: new Date(now.getTime() - 2 * 60 * 60 * 1000),
      createdAt: new Date(now.getTime() - 48 * 60 * 60 * 1000),
      completedAt: null,
    },
    {
      id: 4,
      title: 'Виконане завдання',
      description: 'Це завдання успішно виконано',
      categoryId: 4,
      categoryName: 'Проект',
      priority: 'High',
      status: 'Completed',
      dueDate: new Date(now.getTime() + 24 * 60 * 60 * 1000),
      createdAt: new Date(now.getTime() - 72 * 60 * 60 * 1000),
      completedAt: new Date(now.getTime() - 6 * 60 * 60 * 1000),
    },
  ];
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
  const [categories] = useState<Category[]>(mockCategories);
  const [isLoading, setIsLoading] = useState(true);
  const [notifiedTasks, setNotifiedTasks] = useState<Set<number>>(new Set());

  // Завантаження завдань
  useEffect(() => {
    const savedTasks = localStorage.getItem('tasks');
    if (savedTasks) {
      const parsed = JSON.parse(savedTasks).map((t: any) => ({
        ...t,
        dueDate: t.dueDate ? new Date(t.dueDate) : null,
        createdAt: new Date(t.createdAt),
        completedAt: t.completedAt ? new Date(t.completedAt) : null,
      }));
      setTasks(parsed);
    } else {
      setTasks(generateInitialTasks());
    }
    setIsLoading(false);
  }, []);

  // Збереження завдань
  useEffect(() => {
    if (!isLoading) {
      localStorage.setItem('tasks', JSON.stringify(tasks));
    }
  }, [tasks, isLoading]);

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
  const createTask = useCallback((payload: CreateTaskPayload) => {
    const category = categories.find(c => c.idCategory === payload.category_id);
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
    toast.success('Завдання створено!', {
      description: payload.priority === 'High' 
        ? 'Автоматичне нагадування активовано'
        : newTask.title,
    });

    return newTask;
  }, [categories]);

  // Позначити як виконане
  const toggleTaskComplete = useCallback((taskId: number) => {
    setTasks(prev => prev.map(task => {
      if (task.id === taskId) {
        const isCompleting = task.status !== 'Completed';
        const newStatus: TaskStatus = isCompleting ? 'Completed' : 
          (task.dueDate && new Date(task.dueDate) < new Date() ? 'Overdue' : 'Pending');
        
        if (isCompleting) {
          playNotificationSound();
          toast.success('Завдання виконано! ✓', { description: task.title });
        } else {
          toast.info('Статус скасовано', { description: task.title });
        }

        return {
          ...task,
          status: newStatus,
          completedAt: isCompleting ? new Date() : null,
        };
      }
      return task;
    }));
  }, []);

  // Видалення завдання
  const deleteTask = useCallback((taskId: number) => {
    setTasks(prev => prev.filter(t => t.id !== taskId));
    toast.info('Завдання видалено');
  }, []);

  return {
    tasks,
    categories,
    isLoading,
    createTask,
    toggleTaskComplete,
    deleteTask,
  };
};
