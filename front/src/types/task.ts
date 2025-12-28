export type Priority = 'Low' | 'Medium' | 'High';
export type TaskStatus = 'Pending' | 'Completed' | 'Overdue';

export interface Task {
  id: number;
  title: string;
  description: string;
  categoryId: number;
  categoryName: string;
  priority: Priority;
  status: TaskStatus;
  dueDate: Date | null;
  createdAt: Date;
  completedAt: Date | null;
}

export interface Category {
  idCategory: number;
  CategoryName: string;
}

export interface CreateTaskPayload {
  title: string;
  description: string;
  category_id: number;
  priority: Priority;
  due_date: string | null;
}
