import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Task, WorkerSimple } from '../types';
import { updateTask, getWorkersSimple } from '../lib/api-fastapi';
import { toast } from 'sonner';

interface EditTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onTaskUpdated: () => void;
}

export function EditTaskModal({ open, onOpenChange, task, onTaskUpdated }: EditTaskModalProps) {
  const [workers, setWorkers] = useState<WorkerSimple[]>([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    status: 'pending' as 'pending' | 'in-progress' | 'completed',
    assignedToId: '',
    dueDate: '',
  });

  // Cargar trabajadores cuando se abre el modal
  useEffect(() => {
    if (open) {
      loadWorkers();
    }
  }, [open]);

  // Prellenar formulario cuando cambia la tarea
  useEffect(() => {
    if (task && open) {
      setFormData({
        title: task.title || '',
        description: task.description || '',
        priority: task.priority || 'medium',
        status: task.status || 'pending',
        assignedToId: task.assignedToId || '',
        dueDate: task.dueDate ? new Date(task.dueDate).toISOString().split('T')[0] : '',
      });
    }
  }, [task, open]);

  const loadWorkers = async () => {
    try {
      const workersData = await getWorkersSimple();
      setWorkers(workersData);
    } catch (error) {
      console.error('Error loading workers:', error);
      toast.error('Error al cargar trabajadores');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!task) return;

    if (!formData.title.trim()) {
      toast.error('El título es requerido');
      return;
    }

    try {
      setLoading(true);

      const updates: Partial<Task> = {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        priority: formData.priority,
        status: formData.status,
        assignedToId: formData.assignedToId || undefined,
        dueDate: formData.dueDate || undefined,
      };

      await updateTask(task.id, updates);
      toast.success('Tarea actualizada exitosamente');
      onTaskUpdated();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error updating task:', error);
      toast.error(error.message || 'Error al actualizar la tarea');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Editar Tarea</DialogTitle>
          <DialogDescription>
            Modifica los datos de la tarea. Los campos marcados con * son obligatorios.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-task-title">
                Título de la Tarea *
              </Label>
              <Input
                id="edit-task-title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Ej: Contactar familiar"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-task-description">Descripción</Label>
              <Textarea
                id="edit-task-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe los detalles de la tarea..."
                rows={4}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-task-priority">Prioridad</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value: 'low' | 'medium' | 'high') =>
                    setFormData({ ...formData, priority: value })
                  }
                >
                  <SelectTrigger id="edit-task-priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Baja</SelectItem>
                    <SelectItem value="medium">Media</SelectItem>
                    <SelectItem value="high">Alta</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-task-status">Estado</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value: 'pending' | 'in-progress' | 'completed') =>
                    setFormData({ ...formData, status: value })
                  }
                >
                  <SelectTrigger id="edit-task-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pendiente</SelectItem>
                    <SelectItem value="in-progress">En Progreso</SelectItem>
                    <SelectItem value="completed">Completada</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-task-assigned">Asignar a</Label>
                <Select
                  value={formData.assignedToId || 'unassigned'}
                  onValueChange={(value) =>
                    setFormData({ ...formData, assignedToId: value === 'unassigned' ? '' : value })
                  }
                >
                  <SelectTrigger id="edit-task-assigned">
                    <SelectValue placeholder="Seleccionar trabajador" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unassigned">Sin asignar</SelectItem>
                    {workers.map((worker) => (
                      <SelectItem key={worker.id} value={worker.id}>
                        {worker.name} {worker.role && `(${worker.role})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-task-duedate">Fecha de Vencimiento</Label>
                <Input
                  id="edit-task-duedate"
                  type="date"
                  value={formData.dueDate}
                  onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

