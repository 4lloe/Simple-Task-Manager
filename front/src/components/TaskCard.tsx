import { Task } from '@/types/task';
import { Button } from '@/components/ui/button';
import { Check, RotateCcw, Trash2, Clock, Tag } from 'lucide-react';
import { format } from 'date-fns';
import { uk } from 'date-fns/locale';

interface TaskCardProps {
  task: Task;
  onToggleComplete: (id: number) => void;
  onDelete: (id: number) => void;
}

export const TaskCard = ({ task, onToggleComplete, onDelete }: TaskCardProps) => {
  const priorityClasses = {
    High: 'priority-high',
    Medium: 'priority-medium',
    Low: 'priority-low',
  };

  const statusClasses = {
    Pending: 'status-pending',
    Completed: 'status-completed',
    Overdue: 'status-overdue',
  };

  const statusLabels = {
    Pending: 'В очікуванні',
    Completed: 'Виконано',
    Overdue: 'Прострочено',
  };

  const isCompleted = task.status === 'Completed';
  const isOverdue = task.status === 'Overdue';

  return (
    <div 
      className={`glass-card rounded-xl p-4 animate-slide-up transition-all hover:shadow-elevated group ${
        isCompleted ? 'opacity-70' : ''
      } ${isOverdue ? 'border-l-4 border-l-[hsl(var(--overdue))]' : ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`priority-badge ${priorityClasses[task.priority]}`}>
              {task.priority}
            </span>
            <span className={`priority-badge ${statusClasses[task.status]}`}>
              {statusLabels[task.status]}
            </span>
          </div>

          <h3 className={`font-semibold text-foreground mb-1 ${isCompleted ? 'line-through text-muted-foreground' : ''}`}>
            {task.title}
          </h3>

          {task.description && (
            <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
              {task.description}
            </p>
          )}

          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {task.categoryName}
            </span>
            {task.dueDate && (
              <span className={`flex items-center gap-1 ${isOverdue ? 'text-[hsl(var(--overdue))] font-medium' : ''}`}>
                <Clock className="w-3 h-3" />
                {format(new Date(task.dueDate), 'dd MMM, HH:mm', { locale: uk })}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onToggleComplete(task.id)}
            className={`h-8 w-8 ${isCompleted ? 'text-warning hover:text-warning' : 'text-success hover:text-success'}`}
            title={isCompleted ? 'Скасувати виконання' : 'Позначити виконаним'}
          >
            {isCompleted ? <RotateCcw className="w-4 h-4" /> : <Check className="w-4 h-4" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(task.id)}
            className="h-8 w-8 text-destructive hover:text-destructive"
            title="Видалити"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
