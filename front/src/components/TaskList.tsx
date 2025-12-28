import { Task, TaskStatus } from '@/types/task';
import { TaskCard } from './TaskCard';
import { ClipboardList, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface TaskListProps {
  tasks: Task[];
  onToggleComplete: (id: number) => void;
  onDelete: (id: number) => void;
}

export const TaskList = ({ tasks, onToggleComplete, onDelete }: TaskListProps) => {
  const pendingTasks = tasks.filter(t => t.status === 'Pending');
  const overdueTasks = tasks.filter(t => t.status === 'Overdue');
  const completedTasks = tasks.filter(t => t.status === 'Completed');

  const stats = [
    { label: 'Всього', value: tasks.length, icon: ClipboardList, color: 'text-primary' },
    { label: 'В очікуванні', value: pendingTasks.length, icon: Clock, color: 'text-muted-foreground' },
    { label: 'Прострочено', value: overdueTasks.length, icon: AlertCircle, color: 'text-[hsl(var(--overdue))]' },
    { label: 'Виконано', value: completedTasks.length, icon: CheckCircle2, color: 'text-[hsl(var(--success))]' },
  ];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="glass-card rounded-xl p-4 text-center">
            <stat.icon className={`w-5 h-5 mx-auto mb-1 ${stat.color}`} />
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <div className="text-xs text-muted-foreground">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Task Sections */}
      {overdueTasks.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-[hsl(var(--overdue))] mb-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Прострочені ({overdueTasks.length})
          </h3>
          <div className="space-y-3">
            {overdueTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onToggleComplete={onToggleComplete}
                onDelete={onDelete}
              />
            ))}
          </div>
        </section>
      )}

      {pendingTasks.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            В очікуванні ({pendingTasks.length})
          </h3>
          <div className="space-y-3">
            {pendingTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onToggleComplete={onToggleComplete}
                onDelete={onDelete}
              />
            ))}
          </div>
        </section>
      )}

      {completedTasks.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-[hsl(var(--success))] mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Виконані ({completedTasks.length})
          </h3>
          <div className="space-y-3">
            {completedTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onToggleComplete={onToggleComplete}
                onDelete={onDelete}
              />
            ))}
          </div>
        </section>
      )}

      {tasks.length === 0 && (
        <div className="text-center py-12">
          <ClipboardList className="w-12 h-12 mx-auto text-muted-foreground/40 mb-3" />
          <p className="text-muted-foreground">Завдань немає. Створіть перше!</p>
        </div>
      )}
    </div>
  );
};
