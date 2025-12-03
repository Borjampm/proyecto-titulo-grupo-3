import { useState } from 'react';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import {
  Clock,
  Circle,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  UserCircle,
} from 'lucide-react';
import { Task, WorkerSimple } from '../types';
import { updateTask } from '../lib/api-fastapi';
import { toast } from 'sonner';
import { EditTaskModal } from './EditTaskModal';

interface TaskCardProps {
  task: Task;
  workers: WorkerSimple[];
  onTaskUpdated: () => void;
  onStatusChange?: (taskId: string, newStatus: string) => void;
  onAssigneeChange?: (taskId: string, assigneeId: string) => void;
  showCompletedInfo?: boolean;
  variant?: 'default' | 'compact';
}

export function TaskCard({
  task,
  workers,
  onTaskUpdated,
  onStatusChange,
  onAssigneeChange,
  showCompletedInfo = true,
  variant = 'default',
}: TaskCardProps) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const isCompleted = task.status === 'completed';

  const getDueDateStatus = (dueDate?: string) => {
    if (!dueDate) return null;
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    
    const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'overdue';
    if (diffDays === 0) return 'today';
    if (diffDays <= 2) return 'soon';
    return 'ok';
  };

  const dueDateStatus = getDueDateStatus(task.dueDate);

  const handleStatusChange = async (newStatus: string) => {
    if (onStatusChange) {
      onStatusChange(task.id, newStatus);
    } else {
      try {
        await updateTask(task.id, { status: newStatus as any });
        toast.success('Estado de tarea actualizado');
        onTaskUpdated();
      } catch (error) {
        console.error('Error updating task status:', error);
        toast.error('Error al actualizar estado');
      }
    }
  };

  const handleAssigneeChange = async (assigneeId: string) => {
    if (onAssigneeChange) {
      onAssigneeChange(task.id, assigneeId);
    } else {
      try {
        await updateTask(task.id, { assignedToId: assigneeId || undefined });
        toast.success('Asignación actualizada');
        onTaskUpdated();
      } catch (error) {
        console.error('Error updating assignee:', error);
        toast.error('Error al actualizar asignación');
      }
    }
  };

  if (variant === 'compact') {
    return (
      <>
        <div
          className="border rounded-lg p-4 cursor-pointer hover:bg-muted/20 transition-colors"
          onClick={() => setIsEditModalOpen(true)}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                {task.status === 'in-progress' ? (
                  <Clock className="w-4 h-4 text-yellow-600" />
                ) : (
                  <Circle className="w-4 h-4 text-gray-400" />
                )}
                <h4>{task.title}</h4>
              </div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-muted-foreground">Responsable:</span>
                <span className="text-sm font-medium">{task.assignedTo || 'Sin asignar'}</span>
              </div>
              {task.description && (
                <p className="text-muted-foreground mb-2">{task.description}</p>
              )}
              <div className="flex items-center gap-2 flex-wrap">
                <Badge
                  variant="outline"
                  className={
                    task.priority === 'high'
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : task.priority === 'medium'
                      ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                      : 'bg-blue-50 text-blue-700 border-blue-200'
                  }
                >
                  Prioridad {task.priority === 'high' ? 'Alta' : task.priority === 'medium' ? 'Media' : 'Baja'}
                </Badge>
                <Badge variant="outline" className="flex items-center gap-1">
                  <UserCircle className="w-3 h-3" />
                  {task.assignedTo}
                </Badge>
                {task.dueDate && (
                  <Badge
                    variant="outline"
                    className={
                      new Date(task.dueDate) < new Date()
                        ? 'bg-red-50 text-red-700 border-red-200'
                        : 'bg-gray-50'
                    }
                  >
                    <Calendar className="w-3 h-3 mr-1" />
                    {new Date(task.dueDate).toLocaleDateString('es-ES')}
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
              <Select value={task.status} onValueChange={handleStatusChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pending">Pendiente</SelectItem>
                  <SelectItem value="in-progress">En Progreso</SelectItem>
                  <SelectItem value="completed">Completada</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={task.assignedToId || 'unassigned'}
                onValueChange={(value) => handleAssigneeChange(value === 'unassigned' ? '' : value)}
              >
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Asignar..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Sin asignar</SelectItem>
                  {workers.map((worker) => (
                    <SelectItem key={worker.id} value={worker.id}>
                      {worker.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <EditTaskModal
          open={isEditModalOpen}
          onOpenChange={setIsEditModalOpen}
          task={task}
          onTaskUpdated={onTaskUpdated}
        />
      </>
    );
  }

  return (
    <>
      <div
        className={`border rounded-lg p-4 transition-colors cursor-pointer ${
          isCompleted ? 'bg-green-50/50 border-green-200' : 'hover:bg-muted/20'
        }`}
        onClick={() => setIsEditModalOpen(true)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {isCompleted ? (
                <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
              ) : task.status === 'in-progress' ? (
                <Clock className="w-4 h-4 text-yellow-600 shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-gray-400 shrink-0" />
              )}
              <h4 className={`font-medium truncate ${isCompleted ? 'text-muted-foreground line-through' : ''}`}>
                {task.title}
              </h4>
            </div>
            {task.description && (
              <p className="text-muted-foreground text-sm mb-2 line-clamp-2">
                {task.description}
              </p>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <Badge
                variant="outline"
                className={
                  isCompleted
                    ? 'bg-green-50 text-green-700 border-green-200'
                    : task.priority === 'high'
                    ? 'bg-red-50 text-red-700 border-red-200'
                    : task.priority === 'medium'
                    ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                    : 'bg-blue-50 text-blue-700 border-blue-200'
                }
              >
                {isCompleted
                  ? 'Completada'
                  : task.priority === 'high'
                  ? 'Alta'
                  : task.priority === 'medium'
                  ? 'Media'
                  : 'Baja'}
              </Badge>
              {task.dueDate && (
                <Badge
                  variant="outline"
                  className={
                    isCompleted
                      ? 'bg-gray-100 text-gray-600 border-gray-200'
                      : dueDateStatus === 'overdue'
                      ? 'bg-red-100 text-red-800 border-red-300'
                      : dueDateStatus === 'today'
                      ? 'bg-orange-100 text-orange-800 border-orange-300'
                      : dueDateStatus === 'soon'
                      ? 'bg-yellow-100 text-yellow-800 border-yellow-300'
                      : 'bg-gray-100 text-gray-700 border-gray-300'
                  }
                >
                  <Calendar className="w-3 h-3 mr-1" />
                  {!isCompleted && dueDateStatus === 'overdue' && (
                    <AlertTriangle className="w-3 h-3 mr-1" />
                  )}
                  {new Date(task.dueDate).toLocaleDateString('es-ES')}
                </Badge>
              )}
              {showCompletedInfo && isCompleted && task.completedAt && (
                <span className="text-xs text-muted-foreground">
                  Completada el {new Date(task.completedAt).toLocaleDateString('es-ES')}
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
            <Select value={task.status} onValueChange={handleStatusChange}>
              <SelectTrigger className={`w-[130px] ${isCompleted ? 'bg-green-50' : ''}`}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pending">Pendiente</SelectItem>
                <SelectItem value="in-progress">En Progreso</SelectItem>
                <SelectItem value="completed">Completada</SelectItem>
              </SelectContent>
            </Select>
            {!isCompleted && (
              <Select
                value={task.assignedToId || 'unassigned'}
                onValueChange={(value) => handleAssigneeChange(value === 'unassigned' ? '' : value)}
              >
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Asignar a..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Sin asignar</SelectItem>
                  {workers.map((worker) => (
                    <SelectItem key={worker.id} value={worker.id}>
                      {worker.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {isCompleted && task.assignedTo && task.assignedTo !== 'Sin asignar' && (
              <span className="text-xs text-muted-foreground">
                Por: {task.assignedTo}
              </span>
            )}
          </div>
        </div>
      </div>

      <EditTaskModal
        open={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
        task={task}
        onTaskUpdated={onTaskUpdated}
      />
    </>
  );
}

