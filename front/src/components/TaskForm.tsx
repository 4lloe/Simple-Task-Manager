import { useState } from 'react';
import { Category, Priority, CreateTaskPayload } from '@/types/task';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Plus, Calendar, Tag, AlertTriangle, FileText } from 'lucide-react';

interface TaskFormProps {
  categories: Category[];
  onSubmit: (payload: CreateTaskPayload) => void;
}

export const TaskForm = ({ categories, onSubmit }: TaskFormProps) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState<string>('');
  const [priority, setPriority] = useState<Priority>('Medium');
  const [dueDate, setDueDate] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !categoryId) return;

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      category_id: parseInt(categoryId),
      priority,
      due_date: dueDate || null,
    });

    // Очистка форми
    setTitle('');
    setDescription('');
    setCategoryId('');
    setPriority('Medium');
    setDueDate('');
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card rounded-xl p-6 animate-fade-in">
      <h2 className="text-lg font-semibold text-foreground mb-5 flex items-center gap-2">
        <Plus className="w-5 h-5 text-primary" />
        Нове завдання
      </h2>

      <div className="space-y-4">
        <div>
          <Label htmlFor="title" className="text-sm font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            Назва
          </Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Введіть назву завдання..."
            className="bg-background/50 border-border/50 focus:border-primary transition-colors"
            required
          />
        </div>

        <div>
          <Label htmlFor="description" className="text-sm font-medium text-muted-foreground mb-1.5">
            Опис
          </Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Додатковий опис..."
            rows={2}
            className="bg-background/50 border-border/50 focus:border-primary transition-colors resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5" />
              Категорія
            </Label>
            <Select value={categoryId} onValueChange={setCategoryId} required>
              <SelectTrigger className="bg-background/50 border-border/50">
                <SelectValue placeholder="Оберіть..." />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat.idCategory} value={cat.idCategory.toString()}>
                    {cat.CategoryName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-sm font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              Пріоритет
            </Label>
            <Select value={priority} onValueChange={(v) => setPriority(v as Priority)}>
              <SelectTrigger className="bg-background/50 border-border/50">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Low">
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--priority-low))]" />
                    Low
                  </span>
                </SelectItem>
                <SelectItem value="Medium">
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--priority-medium))]" />
                    Medium
                  </span>
                </SelectItem>
                <SelectItem value="High">
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--priority-high))]" />
                    High (Auto Reminder)
                  </span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="dueDate" className="text-sm font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            Дедлайн
          </Label>
          <Input
            id="dueDate"
            type="datetime-local"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="bg-background/50 border-border/50 focus:border-primary transition-colors"
          />
        </div>

        <Button 
          type="submit" 
          className="w-full mt-2 bg-primary hover:bg-primary/90 text-primary-foreground font-medium transition-all hover:shadow-lg"
          disabled={!title.trim() || !categoryId}
        >
          <Plus className="w-4 h-4 mr-2" />
          Додати завдання
        </Button>
      </div>
    </form>
  );
};
