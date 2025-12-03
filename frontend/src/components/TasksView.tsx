import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import {
  ClipboardList,
  Clock,
  Circle,
  CheckCircle2,
  Plus,
  UserPlus,
  Users,
  Filter,
  X,
  Eye,
} from 'lucide-react';
import { Task, Worker, WorkerSimple } from '../types';
import {
  getAllTasks,
  updateTask,
  getWorkersSimple,
  getWorkers,
  createWorker,
  deleteWorker,
} from '../lib/api-fastapi';
import { toast } from 'sonner';
import { TaskCard } from './TaskCard';
import { CreateTaskModal } from './CreateTaskModal';

export function TasksView() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workers, setWorkers] = useState<WorkerSimple[]>([]);
  const [allWorkers, setAllWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAssignee, setFilterAssignee] = useState<string>('all');
  const [showCompleted, setShowCompleted] = useState(false);
  
  // Create task modal
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  
  // Worker creation dialog
  const [isWorkerDialogOpen, setIsWorkerDialogOpen] = useState(false);
  const [newWorker, setNewWorker] = useState({
    name: '',
    email: '',
    role: '',
    department: '',
  });
  const [creatingWorker, setCreatingWorker] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadTasks();
  }, [filterAssignee, showCompleted]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tasksData, workersData, allWorkersData] = await Promise.all([
        getAllTasks({ openOnly: !showCompleted, orderByDueDate: true }),
        getWorkersSimple(),
        getWorkers(false),
      ]);
      setTasks(tasksData);
      setWorkers(workersData);
      setAllWorkers(allWorkersData);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async () => {
    try {
      const tasksData = await getAllTasks({
        openOnly: !showCompleted,
        orderByDueDate: true,
        assignedToId: filterAssignee !== 'all' ? filterAssignee : undefined,
      });
      setTasks(tasksData);
    } catch (error) {
      console.error('Error loading tasks:', error);
      toast.error('Error al cargar tareas');
    }
  };

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    try {
      await updateTask(taskId, { status: newStatus as any });
      toast.success('Estado de tarea actualizado');
      loadTasks();
    } catch (error) {
      console.error('Error updating task:', error);
      toast.error('Error al actualizar estado');
    }
  };

  const handleAssigneeChange = async (taskId: string, assigneeId: string) => {
    try {
      await updateTask(taskId, { assignedToId: assigneeId || undefined });
      toast.success('Asignación actualizada');
      loadTasks();
    } catch (error) {
      console.error('Error updating assignee:', error);
      toast.error('Error al actualizar asignación');
    }
  };

  const handleCreateWorker = async () => {
    if (!newWorker.name.trim()) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      setCreatingWorker(true);
      await createWorker({
        name: newWorker.name.trim(),
        email: newWorker.email.trim() || undefined,
        role: newWorker.role.trim() || undefined,
        department: newWorker.department.trim() || undefined,
      });
      toast.success('Trabajador creado exitosamente');
      setNewWorker({ name: '', email: '', role: '', department: '' });
      setIsWorkerDialogOpen(false);
      
      // Reload workers
      const [workersData, allWorkersData] = await Promise.all([
        getWorkersSimple(),
        getWorkers(false),
      ]);
      setWorkers(workersData);
      setAllWorkers(allWorkersData);
    } catch (error: any) {
      console.error('Error creating worker:', error);
      toast.error(error.message || 'Error al crear trabajador');
    } finally {
      setCreatingWorker(false);
    }
  };

  const handleDeleteWorker = async (workerId: string) => {
    try {
      await deleteWorker(workerId);
      toast.success('Trabajador desactivado');
      
      // Reload workers
      const [workersData, allWorkersData] = await Promise.all([
        getWorkersSimple(),
        getWorkers(false),
      ]);
      setWorkers(workersData);
      setAllWorkers(allWorkersData);
    } catch (error) {
      console.error('Error deleting worker:', error);
      toast.error('Error al desactivar trabajador');
    }
  };


  const pendingTasks = tasks.filter(t => t.status === 'pending');
  const inProgressTasks = tasks.filter(t => t.status === 'in-progress');
  const completedTasks = tasks.filter(t => t.status === 'completed');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Tareas</h1>
          <p className="text-muted-foreground">
            Gestión de tareas abiertas y en progreso
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isWorkerDialogOpen} onOpenChange={setIsWorkerDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="w-4 h-4 mr-2" />
                Nuevo Trabajador
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Crear Nuevo Trabajador</DialogTitle>
                <DialogDescription>
                  Agrega un nuevo trabajador al sistema para asignar tareas.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="worker-name">Nombre *</Label>
                <Input
                  id="worker-name"
                  value={newWorker.name}
                  onChange={(e) => setNewWorker({ ...newWorker, name: e.target.value })}
                  placeholder="Nombre del trabajador"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="worker-email">Email</Label>
                <Input
                  id="worker-email"
                  type="email"
                  value={newWorker.email}
                  onChange={(e) => setNewWorker({ ...newWorker, email: e.target.value })}
                  placeholder="email@ejemplo.com"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="worker-role">Rol</Label>
                  <Input
                    id="worker-role"
                    value={newWorker.role}
                    onChange={(e) => setNewWorker({ ...newWorker, role: e.target.value })}
                    placeholder="Ej: Asistente Social"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="worker-department">Departamento</Label>
                  <Input
                    id="worker-department"
                    value={newWorker.department}
                    onChange={(e) => setNewWorker({ ...newWorker, department: e.target.value })}
                    placeholder="Ej: Servicio Social"
                  />
                </div>
              </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsWorkerDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleCreateWorker} disabled={creatingWorker}>
                  {creatingWorker ? 'Creando...' : 'Crear Trabajador'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className={`grid grid-cols-1 gap-4 ${showCompleted ? 'sm:grid-cols-4' : 'sm:grid-cols-3'}`}>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-100">
              <Circle className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{pendingTasks.length}</p>
              <p className="text-sm text-muted-foreground">Pendientes</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-100">
              <Clock className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{inProgressTasks.length}</p>
              <p className="text-sm text-muted-foreground">En Progreso</p>
            </div>
          </div>
        </Card>
        {showCompleted && (
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{completedTasks.length}</p>
                <p className="text-sm text-muted-foreground">Completadas</p>
              </div>
            </div>
          </Card>
        )}
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{workers.length}</p>
              <p className="text-sm text-muted-foreground">Trabajadores Activos</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="tasks" className="w-full">
        <TabsList>
          <TabsTrigger value="tasks">Tareas</TabsTrigger>
          <TabsTrigger value="workers">Trabajadores</TabsTrigger>
        </TabsList>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4 mt-4">
          {/* Filter */}
          <Card className="p-4">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-muted-foreground" />
                  <Label>Filtrar por asignado:</Label>
                </div>
                <Select value={filterAssignee} onValueChange={setFilterAssignee}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Todos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    {workers.map((worker) => (
                      <SelectItem key={worker.id} value={worker.id}>
                        {worker.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {filterAssignee !== 'all' && (
                  <Button variant="ghost" size="sm" onClick={() => setFilterAssignee('all')}>
                    <X className="w-4 h-4 mr-1" />
                    Limpiar
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-muted-foreground" />
                <Label htmlFor="show-completed" className="cursor-pointer">
                  Ver completadas
                </Label>
                <Switch
                  id="show-completed"
                  checked={showCompleted}
                  onCheckedChange={setShowCompleted}
                />
              </div>
            </div>
          </Card>

          {/* Tasks List */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">
                {showCompleted ? `Todas las Tareas (${tasks.length})` : `Tareas Abiertas (${tasks.length})`}
              </h3>
              <Button onClick={() => setIsCreateTaskModalOpen(true)}>
                <ClipboardList className="w-4 h-4 mr-2" />
                Nueva Tarea
              </Button>
            </div>
            <div className="space-y-3">
              {tasks.length === 0 ? (
                <p className="text-muted-foreground py-8 text-center">
                  {showCompleted ? 'No hay tareas' : 'No hay tareas abiertas'}
                </p>
              ) : (
                tasks.map((task) => (
                  <TaskCard
                      key={task.id}
                    task={task}
                    workers={workers}
                    onTaskUpdated={loadTasks}
                    onStatusChange={handleStatusChange}
                    onAssigneeChange={handleAssigneeChange}
                    showCompletedInfo={true}
                  />
                ))
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Workers Tab */}
        <TabsContent value="workers" className="space-y-4 mt-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Trabajadores ({allWorkers.length})</h3>
              <Button size="sm" onClick={() => setIsWorkerDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-1" />
                Agregar
              </Button>
            </div>
            <div className="space-y-3">
              {allWorkers.length === 0 ? (
                <p className="text-muted-foreground py-8 text-center">
                  No hay trabajadores registrados
                </p>
              ) : (
                allWorkers.map((worker) => (
                  <div
                    key={worker.id}
                    className={`border rounded-lg p-4 flex items-center justify-between ${
                      !worker.active ? 'opacity-50 bg-muted/30' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-primary font-medium">
                          {worker.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium">{worker.name}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          {worker.role && <span>{worker.role}</span>}
                          {worker.role && worker.department && <span>•</span>}
                          {worker.department && <span>{worker.department}</span>}
                        </div>
                        {worker.email && (
                          <p className="text-sm text-muted-foreground">{worker.email}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={worker.active ? 'default' : 'secondary'}>
                        {worker.active ? 'Activo' : 'Inactivo'}
                      </Badge>
                      {worker.active && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteWorker(worker.id)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Task Modal */}
      <CreateTaskModal
        open={isCreateTaskModalOpen}
        onOpenChange={setIsCreateTaskModalOpen}
        onTaskCreated={loadTasks}
      />
    </div>
  );
}

