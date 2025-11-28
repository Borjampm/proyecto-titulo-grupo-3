import { TimelineEvent } from '../types';
import { 
  FileText, 
  CheckCircle, 
  Circle, 
  AlertTriangle, 
  Upload, 
  Calendar,
  ClipboardList,
  Activity,
  User,
  PlayCircle,
  XCircle,
  PauseCircle
} from 'lucide-react';
import { Badge } from './ui/badge';
import { cn } from './ui/utils';

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events }: TimelineProps) {
  // Sort events by timestamp (most recent first)
  const sortedEvents = [...events].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const getEventIcon = (type: TimelineEvent['type'], metadata?: TimelineEvent['metadata']) => {
    switch (type) {
      case 'task-created':
        return ClipboardList;
      case 'task-completed':
        return CheckCircle;
      case 'task-updated':
        // Different icons based on new status
        const newStatus = metadata?.new_status?.toUpperCase();
        if (newStatus === 'IN_PROGRESS') {
          return PlayCircle;
        } else if (newStatus === 'CANCELLED') {
          return XCircle;
        } else if (newStatus === 'PENDING') {
          return PauseCircle;
        }
        return Activity;
      case 'document':
        return Upload;
      case 'alert':
        return AlertTriangle;
      case 'admission':
        return Calendar;
      case 'status-change':
        return Activity;
      default:
        return Circle;
    }
  };

  const getEventColor = (type: TimelineEvent['type'], metadata?: TimelineEvent['metadata']) => {
    switch (type) {
      case 'task-created':
        return 'text-violet-600 bg-violet-50 border-violet-300';
      case 'task-completed':
        return 'text-emerald-700 bg-emerald-100 border-emerald-400';
      case 'task-updated':
        // Different colors based on new status
        const newStatus = metadata?.new_status?.toUpperCase();
        if (newStatus === 'IN_PROGRESS') {
          return 'text-blue-600 bg-blue-50 border-blue-300';
        } else if (newStatus === 'CANCELLED') {
          return 'text-rose-600 bg-rose-50 border-rose-300';
        } else if (newStatus === 'PENDING') {
          return 'text-slate-600 bg-slate-50 border-slate-300';
        }
        return 'text-amber-600 bg-amber-50 border-amber-300';
      case 'document':
        return 'text-indigo-600 bg-indigo-50 border-indigo-200';
      case 'alert':
        return metadata?.severity === 'high' 
          ? 'text-red-600 bg-red-50 border-red-200'
          : 'text-orange-600 bg-orange-50 border-orange-200';
      case 'admission':
        return 'text-teal-600 bg-teal-50 border-teal-200';
      case 'status-change':
        return 'text-cyan-600 bg-cyan-50 border-cyan-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getEventTypeLabel = (type: TimelineEvent['type'], metadata?: TimelineEvent['metadata']) => {
    switch (type) {
      case 'task-created':
        return 'Tarea Creada';
      case 'task-completed':
        return 'Tarea Completada';
      case 'task-updated':
        // Determine label based on new status
        const newStatus = metadata?.new_status?.toUpperCase();
        if (newStatus === 'IN_PROGRESS') {
          return 'En Progreso';
        } else if (newStatus === 'CANCELLED') {
          return 'Cancelada';
        } else if (newStatus === 'PENDING') {
          return 'Pendiente';
        }
        return 'Actualizada';
      case 'document':
        return 'Documento';
      case 'alert':
        return 'Alerta';
      case 'admission':
        return 'Ingreso';
      case 'status-change':
        return 'Cambio de Estado';
      default:
        return 'Evento';
    }
  };

  const getRoleLabel = (role?: string) => {
    switch (role) {
      case 'coordinator':
        return 'Coordinador';
      case 'social-worker':
        return 'Trabajador Social';
      case 'analyst':
        return 'Analista';
      case 'chief':
        return 'Jefe de Servicio';
      case 'clinical-service':
        return 'Servicio Clínico';
      default:
        return '';
    }
  };

  const formatStatusLabel = (status: string): string => {
    const statusMap: { [key: string]: string } = {
      'PENDING': 'Pendiente',
      'IN_PROGRESS': 'En Progreso',
      'COMPLETED': 'Completada',
      'CANCELLED': 'Cancelada',
      'OVERDUE': 'Vencida',
      'pending': 'Pendiente',
      'in_progress': 'En Progreso',
      'completed': 'Completada',
      'cancelled': 'Cancelada',
      'overdue': 'Vencida',
    };
    return statusMap[status] || status;
  };

  const formatDescription = (description: string, type: TimelineEvent['type']): string => {
    // Handle task status change messages
    const statusChangeMatch = description.match(/Task '(.+)' status changed from (\w+) to (\w+)/i);
    if (statusChangeMatch) {
      const [, taskName, fromStatus, toStatus] = statusChangeMatch;
      return `Estado de tarea "${taskName}" cambió de ${formatStatusLabel(fromStatus)} a ${formatStatusLabel(toStatus)}`;
    }

    // Handle "Status updated from X to Y" messages
    const statusUpdatedMatch = description.match(/Status updated from (\w+) to (\w+)/i);
    if (statusUpdatedMatch) {
      const [, fromStatus, toStatus] = statusUpdatedMatch;
      return `Estado actualizado de ${formatStatusLabel(fromStatus)} a ${formatStatusLabel(toStatus)}`;
    }

    // Handle "Task created" messages
    if (description.toLowerCase().includes('task created')) {
      return 'Tarea creada';
    }

    return description;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    let relativeTime = '';
    if (diffDays > 0) {
      relativeTime = `Hace ${diffDays} día${diffDays > 1 ? 's' : ''}`;
    } else if (diffHours > 0) {
      relativeTime = `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    } else if (diffMinutes > 0) {
      relativeTime = `Hace ${diffMinutes} minuto${diffMinutes > 1 ? 's' : ''}`;
    } else {
      relativeTime = 'Hace un momento';
    }

    return {
      absolute: date.toLocaleString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }),
      relative: relativeTime
    };
  };

  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No hay eventos registrados en la línea de tiempo
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sortedEvents.map((event, index) => {
        const Icon = getEventIcon(event.type, event.metadata);
        const colorClasses = getEventColor(event.type, event.metadata);
        const timestamp = formatTimestamp(event.timestamp);
        const isLast = index === sortedEvents.length - 1;

        return (
          <div key={event.id} className="relative">
            {/* Timeline line */}
            {!isLast && (
              <div className="absolute left-6 top-12 bottom-0 w-0.5 bg-border" />
            )}

            <div className="flex gap-4">
              {/* Icon */}
              <div className={cn('relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2', colorClasses)}>
                <Icon className="h-5 w-5" />
              </div>

              {/* Content */}
              <div className="flex-1 pb-8">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className={cn('text-xs', colorClasses)}>
                        {getEventTypeLabel(event.type, event.metadata)}
                      </Badge>
                      {event.metadata?.taskPriority && (
                        <Badge 
                          variant="outline" 
                          className={cn(
                            'text-xs',
                            event.metadata.taskPriority === 'high' ? 'bg-red-50 text-red-700 border-red-200' :
                            event.metadata.taskPriority === 'medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                            'bg-blue-50 text-blue-700 border-blue-200'
                          )}
                        >
                          Prioridad {event.metadata.taskPriority === 'high' ? 'Alta' : event.metadata.taskPriority === 'medium' ? 'Media' : 'Baja'}
                        </Badge>
                      )}
                    </div>
                    <h4 className="mb-1">{event.title}</h4>
                    <p className="text-muted-foreground">{formatDescription(event.description, event.type)}</p>
                  </div>
                  
                  <div className="text-right shrink-0">
                    <p className="text-muted-foreground" title={timestamp.absolute}>
                      {timestamp.relative}
                    </p>
                    <p className="text-muted-foreground">
                      {timestamp.absolute}
                    </p>
                  </div>
                </div>

                {/* Author info */}
                <div className="flex items-center gap-2 mt-2">
                  <User className="w-3 h-3 text-muted-foreground" />
                  <p className="text-muted-foreground">
                    {event.author}
                    {event.role && ` • ${getRoleLabel(event.role)}`}
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
