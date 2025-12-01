import { Patient, Alert, TimelineEvent, Task, Document as DocumentType, WorkerSimple } from '../types';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { RiskBadge } from './RiskBadge';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Timeline } from './Timeline';
import { ArrowLeft, Calendar, User, Building, FileText, AlertTriangle, Upload, Clock, ClipboardList, CheckCircle2, Circle, UserCircle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { 
  getPatientAlerts, 
  getPatientTimeline, 
  getPatientTasks,
  getPatientDocuments,
  createTask,
  updateTask,
  getWorkersSimple
} from '../lib/api-fastapi';
import { toast } from 'sonner';

interface PatientDetailProps {
  patient: Patient;
  onBack: () => void;
}

export function PatientDetail({ patient, onBack }: PatientDetailProps) {
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium', assignedToId: '', dueDate: '' });
  const [patientAlerts, setPatientAlerts] = useState<Alert[]>([]);
  const [patientTimelineEvents, setPatientTimelineEvents] = useState<TimelineEvent[]>([]);
  const [patientTasks, setPatientTasks] = useState<Task[]>([]);
  const [patientDocuments, setPatientDocuments] = useState<DocumentType[]>([]);
  const [workers, setWorkers] = useState<WorkerSimple[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAssignee, setFilterAssignee] = useState<string>('all');

  useEffect(() => {
    console.log('Episode ID:', patient.id);
    loadPatientData();
  }, [patient.id]);

  const loadPatientData = async () => {
    try {
      setLoading(true);
      const [alerts, timeline, tasks, documents, workersData] = await Promise.all([
        getPatientAlerts(patient.id),
        getPatientTimeline(patient.id),
        getPatientTasks(patient.id),
        getPatientDocuments(patient.id),
        getWorkersSimple(),
      ]);
      
      setPatientAlerts(alerts);
      setPatientTimelineEvents(timeline);
      setPatientTasks(tasks);
      setPatientDocuments(documents);
      setWorkers(workersData);
    } catch (error) {
      console.error('Error loading patient data:', error);
      toast.error('Error al cargar datos del paciente');
    } finally {
      setLoading(false);
    }
  };

  const handleAddTask = async () => {
    if (newTask.title.trim()) {
      try {
        const selectedWorker = workers.find(w => w.id === newTask.assignedToId);
        await createTask(patient.id, {
          title: newTask.title,
          description: newTask.description,
          priority: newTask.priority as any,
          status: 'pending',
          assignedTo: selectedWorker?.name || 'Sin asignar',
          assignedToId: newTask.assignedToId || undefined,
          dueDate: newTask.dueDate || undefined,
          createdBy: 'Usuario actual',
        });
        
        toast.success('Tarea creada exitosamente');
        setNewTask({ title: '', description: '', priority: 'medium', assignedToId: '', dueDate: '' });
        loadPatientData(); // Recargar datos
      } catch (error) {
        console.error('Error creating task:', error);
        toast.error('Error al crear la tarea');
      }
    }
  };

  // Filter tasks by assignee
  const filteredTasks = filterAssignee === 'all' 
    ? patientTasks 
    : patientTasks.filter(t => t.assignedToId === filterAssignee);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={onBack}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex-1">
          <h2>{patient.name}</h2>
          <p className="text-muted-foreground mt-1">
            Detalle completo del paciente y gestión de estadía
          </p>
        </div>
        <RiskBadge level={patient.riskLevel} />
      </div>

      {/* Patient Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <User className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Edad</p>
              <p>{patient.age} años</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Building className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Servicio</p>
              <p>{patient.service}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">Ingreso</p>
              <p>{new Date(patient.admissionDate).toLocaleDateString('es-ES')}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-muted-foreground" />
            <div>
              <p className="text-muted-foreground">GRD</p>
              <p>{patient.grg}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Stay Information */}
      <Card className="p-6">
        <h3 className="mb-4">Información de Estadía</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-muted-foreground">Diagnóstico Principal</p>
            <p className="mt-1">{patient.diagnosis}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Médico Responsable</p>
            <p className="mt-1">{patient.responsible}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Estado Paciente</p>
            <Badge className="mt-1" variant={patient.status === 'active' ? 'default' : 'secondary'}>
              {patient.status === 'active' ? 'Activo' : patient.status === 'pending-discharge' ? 'Pendiente Alta' : 'Alta'}
            </Badge>
          </div>
          <div>
            <p className="text-muted-foreground">Estado del Caso</p>
            <Badge 
              className="mt-1" 
              variant="outline"
              style={{
                backgroundColor: patient.caseStatus === 'open' ? 'rgb(240 253 244)' : 'rgb(249 250 251)',
                color: patient.caseStatus === 'open' ? 'rgb(21 128 61)' : 'rgb(55 65 81)',
                borderColor: patient.caseStatus === 'open' ? 'rgb(134 239 172)' : 'rgb(209 213 219)'
              }}
            >
              {patient.caseStatus === 'open' ? 'Abierto' : 'Cerrado'}
            </Badge>
          </div>
        </div>

        <Separator className="my-4" />

        <div className={`grid grid-cols-1 ${patient.expectedDays !== null ? 'md:grid-cols-4' : 'md:grid-cols-1'} gap-6`}>
          <div>
            <p className="text-muted-foreground">Días de Estadía</p>
            <p className="mt-1">{patient.daysInStay} días</p>
          </div>
          {patient.expectedDays !== null && (
            <>
              <div>
                <p className="text-muted-foreground">Días Esperados (GRD)</p>
                <p className="mt-1">{patient.expectedDays} días</p>
              </div>
              <div>
                <p className="text-muted-foreground">Fecha Alta Esperada</p>
                <p className="mt-1">
                  {new Date(new Date(patient.admissionDate).getTime() + patient.expectedDays * 24 * 60 * 60 * 1000).toLocaleDateString('es-ES')}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Desvío</p>
                <p className={`mt-1 ${patient.daysInStay - patient.expectedDays > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {patient.daysInStay - patient.expectedDays > 0 ? '+' : ''}
                  {patient.daysInStay - patient.expectedDays} días
                </p>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Alerts */}
      {patientAlerts.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-4">Alertas Activas</h3>
          <div className="space-y-3">
            {patientAlerts.map(alert => (
              <div key={alert.id} className="flex items-start gap-3 p-3 border rounded-lg bg-orange-50 border-orange-200">
                <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
                <div className="flex-1">
                  <p>{alert.message}</p>
                  <p className="text-muted-foreground mt-1">
                    {new Date(alert.createdAt).toLocaleString('es-ES')}
                  </p>
                </div>
                <RiskBadge level={alert.severity} showIcon={false} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Social Score Section */}
      <Card className="p-6">
        <h3 className="mb-4">Score Social</h3>
        {patient.socialScore !== null && patient.socialScore !== undefined ? (
          <div className="flex items-center gap-4">
            <div className={`text-3xl font-bold ${
              patient.socialScore > 10 
                ? 'text-red-600' 
                : patient.socialScore >= 6 
                  ? 'text-yellow-600'
                  : 'text-green-600'
            }`}>
              {patient.socialScore}
            </div>
            <div>
              <Badge 
                variant="outline" 
                className={
                  patient.socialScore > 10 
                    ? 'bg-red-50 text-red-700 border-red-300' 
                    : patient.socialScore >= 6 
                      ? 'bg-yellow-50 text-yellow-700 border-yellow-300'
                      : 'bg-green-50 text-green-700 border-green-300'
                }
              >
                {patient.socialScore > 10 ? 'Alto Riesgo' : patient.socialScore >= 6 ? 'Riesgo Medio' : 'Bajo Riesgo'}
              </Badge>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-gray-500" />
              <span className="font-medium text-gray-700">Score Social no disponible</span>
            </div>
            {patient.socialScoreReason ? (
              <p className="text-sm text-gray-600">
                <strong>Motivo:</strong> {patient.socialScoreReason}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                No se ha registrado un score social para este paciente.
              </p>
            )}
          </div>
        )}
      </Card>

      {/* Risk Factors */}
      <Card className="p-6">
        <h3 className="mb-4">Factores de Riesgo</h3>
        <div className="flex flex-wrap gap-3 mb-4">
          {patient.socialRisk && (
            <Badge className="bg-orange-100 text-orange-800 border-orange-300" variant="outline">
              Riesgo Social Detectado
            </Badge>
          )}
          {patient.financialRisk && (
            <Badge className="bg-blue-100 text-blue-800 border-blue-300" variant="outline">
              Riesgo Financiero
            </Badge>
          )}
          {patient.expectedDays !== null && patient.daysInStay > patient.expectedDays && (
            <Badge className="bg-red-100 text-red-800 border-red-300" variant="outline">
              Desvío de Estadía
            </Badge>
          )}
        </div>
        
        {!patient.socialRisk && !patient.financialRisk && (patient.expectedDays === null || patient.daysInStay <= patient.expectedDays) && (
          <p className="text-muted-foreground">No se han detectado factores de riesgo críticos</p>
        )}
      </Card>

      {/* Tabs for Timeline, Tasks and Documents */}
      <Tabs defaultValue="timeline" className="w-full">
        <TabsList>
          <TabsTrigger value="timeline">Línea de Tiempo</TabsTrigger>
          <TabsTrigger value="tasks">Tareas</TabsTrigger>
          <TabsTrigger value="documents">Documentos</TabsTrigger>
        </TabsList>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4 mt-4">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3>Línea de Tiempo Completa</h3>
                <p className="text-muted-foreground mt-1">
                  Historial completo de acciones, tareas y documentos
                </p>
              </div>
              <Badge variant="secondary">
                {patientTimelineEvents.length} eventos
              </Badge>
            </div>
            <Timeline events={patientTimelineEvents} />
          </Card>
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4 mt-4">
          <Card className="p-6">
            <h4 className="mb-4">Crear Nueva Tarea</h4>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="task-title">Título de la Tarea *</Label>
                  <Input
                    id="task-title"
                    value={newTask.title}
                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                    placeholder="Ej: Contactar familiar"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="task-assigned">Asignar a</Label>
                  <Select 
                    value={newTask.assignedToId || 'unassigned'} 
                    onValueChange={(value) => setNewTask({ ...newTask, assignedToId: value === 'unassigned' ? '' : value })}
                  >
                    <SelectTrigger id="task-assigned">
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
              </div>
              <div className="space-y-2">
                <Label htmlFor="task-description">Descripción</Label>
                <Textarea
                  id="task-description"
                  value={newTask.description}
                  onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                  placeholder="Describe los detalles de la tarea..."
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="task-priority">Prioridad</Label>
                  <Select value={newTask.priority} onValueChange={(value) => setNewTask({ ...newTask, priority: value })}>
                    <SelectTrigger id="task-priority">
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
                  <Label htmlFor="task-duedate">Fecha de Vencimiento</Label>
                  <Input
                    id="task-duedate"
                    type="date"
                    value={newTask.dueDate}
                    onChange={(e) => setNewTask({ ...newTask, dueDate: e.target.value })}
                  />
                </div>
              </div>
              <Button onClick={handleAddTask}>
                <ClipboardList className="w-4 h-4 mr-2" />
                Crear Tarea
              </Button>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h4>Tareas Activas</h4>
              <div className="flex items-center gap-2">
                <Label className="text-sm text-muted-foreground">Filtrar:</Label>
                <Select value={filterAssignee} onValueChange={setFilterAssignee}>
                  <SelectTrigger className="w-[150px]">
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
              </div>
            </div>
            <div className="space-y-3">
              {filteredTasks.filter(t => t.status !== 'completed').length === 0 ? (
                <p className="text-muted-foreground">No hay tareas activas</p>
              ) : (
                filteredTasks.filter(t => t.status !== 'completed').map(task => (
                  <div key={task.id} className="border rounded-lg p-4">
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
                        {task.description && (
                          <p className="text-muted-foreground mb-2">{task.description}</p>
                        )}
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge 
                            variant="outline"
                            className={
                              task.priority === 'high' ? 'bg-red-50 text-red-700 border-red-200' :
                              task.priority === 'medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                              'bg-blue-50 text-blue-700 border-blue-200'
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
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        <Select 
                          value={task.status} 
                          onValueChange={async (value) => {
                            try {
                              await updateTask(task.id, { status: value as any });
                              toast.success('Estado de tarea actualizado');
                              loadPatientData();
                            } catch (error) {
                              console.error('Error updating task status:', error);
                              toast.error('Error al actualizar estado de la tarea');
                            }
                          }}
                        >
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
                          onValueChange={async (value) => {
                            try {
                              await updateTask(task.id, { assignedToId: value === 'unassigned' ? undefined : value });
                              toast.success('Asignación actualizada');
                              loadPatientData();
                            } catch (error) {
                              console.error('Error updating task assignee:', error);
                              toast.error('Error al actualizar asignación');
                            }
                          }}
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
                ))
              )}
            </div>
          </Card>

          <Card className="p-6">
            <h4 className="mb-4">Tareas Completadas</h4>
            <div className="space-y-3">
              {filteredTasks.filter(t => t.status === 'completed').length === 0 ? (
                <p className="text-muted-foreground">No hay tareas completadas</p>
              ) : (
                filteredTasks.filter(t => t.status === 'completed').map(task => (
                  <div key={task.id} className="border rounded-lg p-4 bg-green-50/50">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="mb-1">{task.title}</h4>
                        {task.description && (
                          <p className="text-muted-foreground mb-2">{task.description}</p>
                        )}
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>Completada el {task.completedAt ? new Date(task.completedAt).toLocaleDateString('es-ES') : 'N/A'}</span>
                          {task.assignedTo && task.assignedTo !== 'Sin asignar' && (
                            <>
                              <span>•</span>
                              <span>Por: {task.assignedTo}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="mt-4 space-y-4">
          <Card className="p-6">
            <h4 className="mb-4">Cargar Nuevo Documento</h4>
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                Arrastra archivos aquí o haz clic para cargar
              </p>
              <Button variant="outline">Seleccionar Archivos</Button>
            </div>
          </Card>

          <Card className="p-6">
            <h4 className="mb-4">Documentos Cargados</h4>
            <div className="space-y-3">
              {patientDocuments.length === 0 ? (
                <p className="text-muted-foreground">No hay documentos disponibles</p>
              ) : (
                patientDocuments.map(doc => (
                  <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-blue-600" />
                      <div>
                        <p>{doc.name}</p>
                        <p className="text-muted-foreground">
                          Subido por {doc.uploadedBy} • {new Date(doc.uploadedAt).toLocaleDateString('es-ES')}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      Ver
                    </Button>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
