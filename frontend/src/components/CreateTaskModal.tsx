import { useState, useEffect, useMemo } from 'react';
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
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command';
import { Check, ChevronsUpDown, Search, ClipboardList } from 'lucide-react';
import { cn } from './ui/utils';
import { Patient, WorkerSimple } from '../types';
import { createTask, getWorkersSimple, getClinicalEpisodes } from '../lib/api-fastapi';
import { toast } from 'sonner';

interface CreateTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  episodeId?: string; // Si está presente, no muestra el selector de paciente
  onTaskCreated: () => void;
}

export function CreateTaskModal({
  open,
  onOpenChange,
  episodeId,
  onTaskCreated,
}: CreateTaskModalProps) {
  const [loading, setLoading] = useState(false);
  const [workers, setWorkers] = useState<WorkerSimple[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [patientSearchOpen, setPatientSearchOpen] = useState(false);
  const [patientSearch, setPatientSearch] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    assignedToId: '',
    dueDate: '',
  });

  // Cargar trabajadores cuando se abre el modal
  useEffect(() => {
    if (open) {
      loadWorkers();
      if (!episodeId) {
        loadPatients();
      } else {
        // Si hay episodeId, no necesitamos cargar pacientes
        setSelectedPatient(null);
      }
    }
  }, [open, episodeId]);

  // Resetear formulario cuando se cierra el modal
  useEffect(() => {
    if (!open) {
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        assignedToId: '',
        dueDate: '',
      });
      setSelectedPatient(null);
      setPatientSearch('');
    }
  }, [open]);

  const loadWorkers = async () => {
    try {
      const workersData = await getWorkersSimple();
      setWorkers(workersData);
    } catch (error) {
      console.error('Error loading workers:', error);
      toast.error('Error al cargar trabajadores');
    }
  };

  const loadPatients = async () => {
    try {
      setLoadingPatients(true);
      // Cargar solo casos abiertos para crear tareas
      const response = await getClinicalEpisodes({
        caseStatus: 'open',
        pageSize: 100,
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Error loading patients:', error);
      toast.error('Error al cargar pacientes');
    } finally {
      setLoadingPatients(false);
    }
  };

  const filteredPatients = useMemo(() => {
    if (!patientSearch) {
      return patients.slice(0, 50); // Limitar a 50 para mejor rendimiento
    }
    const search = patientSearch.toLowerCase();
    return patients
      .filter(
        (p) =>
          p.name.toLowerCase().includes(search) ||
          p.id.toLowerCase().includes(search) ||
          p.rut?.toLowerCase().includes(search)
      )
      .slice(0, 50);
  }, [patientSearch, patients]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validar que se haya seleccionado un paciente si no hay episodeId
    if (!episodeId && !selectedPatient) {
      toast.error('Debe seleccionar un paciente');
      return;
    }

    if (!formData.title.trim()) {
      toast.error('El título es requerido');
      return;
    }

    try {
      setLoading(true);

      const targetEpisodeId = episodeId || selectedPatient?.id;
      if (!targetEpisodeId) {
        toast.error('Error: No se pudo determinar el episodio');
        return;
      }

      const selectedWorker = workers.find((w) => w.id === formData.assignedToId);

      await createTask(targetEpisodeId, {
        title: formData.title.trim(),
        description: formData.description.trim() || undefined,
        priority: formData.priority,
        status: 'pending',
        assignedTo: selectedWorker?.name || 'Sin asignar',
        assignedToId: formData.assignedToId || undefined,
        dueDate: formData.dueDate || undefined,
        createdBy: 'Usuario actual',
      });

      toast.success('Tarea creada exitosamente');
      onTaskCreated();
      onOpenChange(false);
    } catch (error: any) {
      console.error('Error creating task:', error);
      toast.error(error.message || 'Error al crear la tarea');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  // Formatear el display del paciente: "Nombre - Episodio ID"
  const getPatientDisplay = (patient: Patient) => {
    return `${patient.name} - ${patient.id}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Crear Nueva Tarea</DialogTitle>
          <DialogDescription>
            {episodeId
              ? 'Crea una nueva tarea para este paciente. Los campos marcados con * son obligatorios.'
              : 'Crea una nueva tarea. Selecciona un paciente y completa los datos. Los campos marcados con * son obligatorios.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {/* Selector de Paciente - Solo si no hay episodeId */}
            {!episodeId && (
              <div className="space-y-2">
                <Label htmlFor="patient-select">
                  Paciente *
                </Label>
                <Popover open={patientSearchOpen} onOpenChange={setPatientSearchOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      role="combobox"
                      aria-expanded={patientSearchOpen}
                      className="w-full justify-between"
                    >
                      {selectedPatient ? (
                        getPatientDisplay(selectedPatient)
                      ) : (
                        <span className="text-muted-foreground">Seleccionar paciente...</span>
                      )}
                      <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-full p-0" align="start">
                    <Command>
                      <CommandInput
                        placeholder="Buscar por nombre, RUT o ID de episodio..."
                        value={patientSearch}
                        onValueChange={setPatientSearch}
                      />
                      <CommandList>
                        <CommandEmpty>
                          {loadingPatients
                            ? 'Cargando pacientes...'
                            : 'No se encontraron pacientes'}
                        </CommandEmpty>
                        <CommandGroup>
                          {filteredPatients.map((patient) => (
                            <CommandItem
                              key={patient.id}
                              value={`${patient.name} ${patient.id} ${patient.rut || ''}`}
                              onSelect={() => {
                                setSelectedPatient(patient);
                                setPatientSearchOpen(false);
                              }}
                            >
                              <Check
                                className={cn(
                                  'mr-2 h-4 w-4',
                                  selectedPatient?.id === patient.id
                                    ? 'opacity-100'
                                    : 'opacity-0'
                                )}
                              />
                              <div className="flex flex-col">
                                <span>{getPatientDisplay(patient)}</span>
                                {patient.rut && (
                                  <span className="text-xs text-muted-foreground">
                                    RUT: {patient.rut}
                                  </span>
                                )}
                              </div>
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="create-task-title">
                  Título de la Tarea *
                </Label>
                <Input
                  id="create-task-title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Ej: Contactar familiar"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-task-assigned">Asignar a</Label>
                <Select
                  value={formData.assignedToId || 'unassigned'}
                  onValueChange={(value) =>
                    setFormData({ ...formData, assignedToId: value === 'unassigned' ? '' : value })
                  }
                >
                  <SelectTrigger id="create-task-assigned">
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
              <Label htmlFor="create-task-description">Descripción</Label>
              <Textarea
                id="create-task-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe los detalles de la tarea..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="create-task-priority">Prioridad</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value: 'low' | 'medium' | 'high') =>
                    setFormData({ ...formData, priority: value })
                  }
                >
                  <SelectTrigger id="create-task-priority">
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
                <Label htmlFor="create-task-duedate">Fecha de Vencimiento</Label>
                <Input
                  id="create-task-duedate"
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
              {loading ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Creando...
                </>
              ) : (
                <>
                  <ClipboardList className="w-4 h-4 mr-2" />
                  Crear Tarea
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

