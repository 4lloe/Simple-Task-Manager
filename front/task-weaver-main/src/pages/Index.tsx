import { useTaskManager } from '@/hooks/useTaskManager';
import { TaskForm } from '@/components/TaskForm';
import { TaskList } from '@/components/TaskList';
import { CheckSquare, Sparkles } from 'lucide-react';

const Index = () => {
  const { tasks, categories, isLoading, createTask, toggleTaskComplete, deleteTask } = useTaskManager();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Завантаження...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <CheckSquare className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Simple Task Manager</h1>
              <p className="text-xs text-muted-foreground">Керування завданнями • SOA ПЗ-5</p>
            </div>
            <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground bg-secondary/50 px-3 py-1.5 rounded-full">
              <Sparkles className="w-3 h-3 text-primary" />
              Auto-reminders enabled
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container max-w-6xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-[380px,1fr] gap-8">
          {/* Sidebar - Form */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <TaskForm categories={categories} onSubmit={createTask} />
          </aside>

          {/* Main - Task List */}
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-5">Мої завдання</h2>
            <TaskList
              tasks={tasks}
              onToggleComplete={toggleTaskComplete}
              onDelete={deleteTask}
            />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 py-6 mt-12">
        <div className="container max-w-6xl mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>Simple Task Manager • Малий Д.Д., КНТ-22-4 • ПЗ №5 «Комплексування ПЗ у сервісній архітектурі»</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
