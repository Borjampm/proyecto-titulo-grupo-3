/**
 * Adaptador de API para conectar con el backend FastAPI
 * 
 * Este archivo adapta los endpoints y modelos de FastAPI al formato
 * que espera el frontend de la aplicación.
 * 
 * IMPORTANTE: Usa autenticación MOCK hasta que se implemente en el backend.
 */

import config from './config';
import {
  mockPatients,
  mockAlerts,
  mockTasks,
  mockDocuments,
  mockTimelineEvents,
  mockDashboardStats,
} from './mockData';
import {
  Patient,
  Alert,
  Task,
  Document,
  TimelineEvent,
  DashboardStats,
  ReferralForm,
  User,
  AuthResponse,
  PaginatedResponse,
  PatientFilters,
  ExcelImportResult,
} from '../types';

// =============================================================================
// UTILIDADES
// =============================================================================

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private token: string | null = null;

  constructor() {
    this.baseUrl = config.BACKEND_URL;
    this.timeout = config.REQUEST_TIMEOUT;
    // No acceder a localStorage durante la inicialización (puede ejecutarse en el servidor)
    this.token = null;
  }

  private getStoredToken(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    return localStorage.getItem('auth_token');
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // Obtener token si no está establecido (para requests en el cliente)
    if (!this.token && typeof window !== 'undefined') {
      this.token = this.getStoredToken();
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          message: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(error.message || error.detail || 'Error en la petición');
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('La petición ha excedido el tiempo de espera');
        }
        throw error;
      }
      throw new Error('Error desconocido en la petición');
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async patch<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async uploadFile<T>(endpoint: string, formData: FormData): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // Obtener token si no está establecido (para requests en el cliente)
    if (!this.token && typeof window !== 'undefined') {
      this.token = this.getStoredToken();
    }

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          message: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(error.message || 'Error en la carga de archivo');
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('La carga del archivo ha excedido el tiempo de espera');
        }
        throw error;
      }
      throw new Error('Error desconocido al cargar el archivo');
    }
  }
}

const apiClient = new ApiClient();

// =============================================================================
// FUNCIONES DE TRANSFORMACIÓN
// =============================================================================

/**
 * Calcula la edad a partir de la fecha de nacimiento
 */
function calculateAge(birthDate: string): number {
  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  return age;
}

/**
 * Calcula días de estadía
 */
function calculateDaysInStay(admissionDate: string, dischargeDate?: string | null): number {
  const admission = new Date(admissionDate);
  const end = dischargeDate ? new Date(dischargeDate) : new Date();
  const diffTime = Math.abs(end.getTime() - admission.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
}

/**
 * Mapea TaskStatus de FastAPI a status del frontend
 */
function mapTaskStatus(status: string): 'pending' | 'in-progress' | 'completed' {
  const statusMap: { [key: string]: 'pending' | 'in-progress' | 'completed' } = {
    'pending': 'pending',
    'in_progress': 'in-progress',
    'completed': 'completed',
    'cancelled': 'completed', // Tratamos cancelled como completed
    'overdue': 'pending', // Tratamos overdue como pending
  };
  return statusMap[status] || 'pending';
}

/**
 * Mapea status del frontend a TaskStatus de FastAPI
 */
function mapTaskStatusToBackend(status: string): string {
  const statusMap: { [key: string]: string } = {
    'pending': 'pending',
    'in-progress': 'in_progress',
    'completed': 'completed',
  };
  return statusMap[status] || 'pending';
}

/**
 * Mapea prioridad numérica (1-5) a texto
 */
function mapPriority(priority: number): 'low' | 'medium' | 'high' {
  if (priority <= 2) return 'low';
  if (priority <= 3) return 'medium';
  return 'high';
}

/**
 * Mapea prioridad de texto a numérica
 */
function mapPriorityToBackend(priority: string): number {
  const priorityMap: { [key: string]: number } = {
    'low': 2,
    'medium': 3,
    'high': 5,
  };
  return priorityMap[priority] || 3;
}

/**
 * Transforma un ClinicalEpisode de FastAPI a Patient del frontend
 */
function transformClinicalEpisodeToPatient(episode: any): Patient {
  const patient = episode.patient || {};
  const age = patient.birth_date ? calculateAge(patient.birth_date) : 0;
  const daysInStay = calculateDaysInStay(episode.admission_at, episode.discharge_at);

  // Determinar nivel de riesgo basado en días de estadía
  let riskLevel: 'low' | 'medium' | 'high' = 'low';
  if (daysInStay > 10) {
    riskLevel = 'high';
  } else if (daysInStay > 5) {
    riskLevel = 'medium';
  }

  // Determinar estado del caso
  const caseStatus: 'open' | 'closed' =
    episode.status === 'active' ? 'open' : 'closed';

  // Determinar estado del paciente
  let status: 'active' | 'pending-discharge' | 'discharged' = 'active';
  if (episode.status === 'discharged') {
    status = 'discharged';
  } else if (episode.expected_discharge) {
    const expectedDate = new Date(episode.expected_discharge);
    const today = new Date();
    const daysUntilDischarge = Math.ceil((expectedDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (daysUntilDischarge <= 2) {
      status = 'pending-discharge';
    }
  }

  // Obtener el puntaje social más reciente si está disponible
  const socialScore = episode.latest_social_score?.score ?? null;
  const socialScoreReason = episode.latest_social_score?.no_score_reason ?? null;

  return {
    id: episode.id,
    patientId: episode.patient_id,
    name: `${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Sin nombre',
    age: age,
    rut: patient.rut || '',
    bed: episode.bed_id || undefined,
    service: 'Medicina Interna', // TODO: Obtener del episodio cuando esté disponible
    admissionDate: episode.admission_at,
    dischargeDate: episode.discharge_at || undefined,
    diagnosis: 'N/A', // TODO: Obtener del episodio cuando esté disponible
    grg: 'N/A', // TODO: Obtener del episodio cuando esté disponible
    daysInStay: daysInStay,
    expectedDays: episode.expected_discharge ?
      Math.ceil((new Date(episode.expected_discharge).getTime() - new Date(episode.admission_at).getTime()) / (1000 * 60 * 60 * 24)) :
      7, // Default 7 días
    responsible: 'N/A', // TODO: Obtener del episodio cuando esté disponible
    prevision: undefined,
    contactNumber: undefined,
    riskLevel: riskLevel,
    socialRisk: socialScore !== null && socialScore > 10, // Alto riesgo social si score > 10
    financialRisk: false, // TODO: Implementar cuando esté disponible
    socialScore: socialScore,
    socialScoreReason: socialScoreReason,
    status: status,
    caseStatus: caseStatus,
    createdAt: episode.created_at,
    updatedAt: episode.updated_at,
  } as any;
}

/**
 * Transforma un TaskInstance de FastAPI a Task del frontend
 */
function transformTaskInstanceToTask(taskInstance: any, episodeId?: string): Task {
  return {
    id: taskInstance.id,
    patientId: episodeId || taskInstance.episode_id,
    title: taskInstance.title,
    description: taskInstance.description || '',
    status: mapTaskStatus(taskInstance.status),
    priority: mapPriority(taskInstance.priority),
    assignedTo: 'Sin asignar', // TODO: Implementar cuando esté disponible
    createdBy: 'Sistema', // TODO: Implementar cuando esté disponible
    createdAt: taskInstance.created_at,
    dueDate: taskInstance.due_date || undefined,
    completedAt: taskInstance.status === 'completed' ? taskInstance.updated_at : undefined,
  };
}

/**
 * Transforma eventos del historial de FastAPI a TimelineEvent del frontend
 */
function transformHistoryEventToTimelineEvent(event: any, episodeId: string): TimelineEvent {
  let type: TimelineEvent['type'] = 'admission';
  let title = event.description;
  let description = '';

  // Mapear tipos de eventos
  switch (event.event_type) {
    case 'patient_admission':
      type = 'admission';
      title = 'Ingreso del paciente';
      description = event.description;
      break;
    case 'document_uploaded':
      type = 'document';
      title = 'Documento subido';
      description = event.metadata?.file_name || event.description;
      break;
    case 'task_created':
      type = 'task-created';
      title = 'Tarea creada';
      description = event.metadata?.task_title || event.description;
      break;
    case 'task_updated':
      type = 'task-completed';
      title = 'Tarea actualizada';
      description = event.description;
      break;
    default:
      type = 'status-change';
  }

  return {
    id: `${episodeId}_${event.event_date}`,
    patientId: episodeId,
    type: type,
    timestamp: event.event_date,
    author: event.metadata?.user_name || 'Sistema',
    role: 'coordinator',
    title: title,
    description: description,
    relatedId: event.metadata?.related_id,
    metadata: event.metadata,
  };
}

// =============================================================================
// AUTENTICACIÓN (MOCK)
// =============================================================================

/**
 * POST /auth/login (MOCK)
 * Inicia sesión con email y contraseña
 * NOTA: Esto es temporal hasta que se implemente autenticación en el backend
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
  // Simulación de delay de red
  await new Promise(resolve => setTimeout(resolve, 500));

  const mockUser: User = {
    id: '1',
    email: email,
    name: 'Usuario de Prueba',
    role: 'coordinator',
  };

  const mockToken = 'mock_token_' + Date.now();
  apiClient.setToken(mockToken);

  return {
    user: mockUser,
    token: mockToken,
  };
}

/**
 * POST /auth/logout (MOCK)
 * Cierra la sesión actual
 */
export async function logout(): Promise<void> {
  apiClient.clearToken();
}

/**
 * GET /auth/me (MOCK)
 * Obtiene el usuario actualmente autenticado
 */
export async function getCurrentUser(): Promise<User> {
  return {
    id: '1',
    email: 'usuario@ejemplo.com',
    name: 'Usuario de Prueba',
    role: 'coordinator',
  };
}

// =============================================================================
// PACIENTES / EPISODIOS CLÍNICOS
// =============================================================================

/**
 * GET /clinical-episodes/
 * Obtiene la lista de episodios clínicos (pacientes) con filtros
 */
export async function getClinicalEpisodes(filters?: PatientFilters): Promise<PaginatedResponse<Patient>> {
  if (config.USE_MOCK_DATA) {
    let filteredPatients = [...mockPatients];

    // Aplicar filtros
    if (filters?.search) {
      const search = filters.search.toLowerCase();
      filteredPatients = filteredPatients.filter(
        (p) =>
          p.name.toLowerCase().includes(search) ||
          p.rut?.toLowerCase().includes(search) ||
          p.diagnosis.toLowerCase().includes(search)
      );
    }

    if (filters?.caseStatus) {
      filteredPatients = filteredPatients.filter((p) => p.caseStatus === filters.caseStatus);
    }

    if (filters?.service) {
      filteredPatients = filteredPatients.filter((p) => p.service === filters.service);
    }

    if (filters?.riskLevel) {
      filteredPatients = filteredPatients.filter((p) => p.riskLevel === filters.riskLevel);
    }

    // Ordenar: casos abiertos primero, luego por nivel de riesgo
    filteredPatients.sort((a, b) => {
      if (a.caseStatus === 'open' && b.caseStatus === 'closed') return -1;
      if (a.caseStatus === 'closed' && b.caseStatus === 'open') return 1;

      const riskOrder = { high: 0, medium: 1, low: 2 };
      return riskOrder[a.riskLevel] - riskOrder[b.riskLevel];
    });

    const page = filters?.page || 1;
    const pageSize = filters?.pageSize || 20;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const paginatedData = filteredPatients.slice(start, end);

    return {
      success: true,
      data: paginatedData,
      pagination: {
        page,
        pageSize,
        total: filteredPatients.length,
        totalPages: Math.ceil(filteredPatients.length / pageSize),
      },
    };
  }

  const params = new URLSearchParams();

  // Búsqueda
  if (filters?.search) {
    params.append('search', filters.search);
  }

  // Paginación
  params.append('page', (filters?.page || 1).toString());
  params.append('page_size', (filters?.pageSize || 20).toString());

  // Incluir datos del paciente
  params.append('include', 'patient,social_score');

  const endpoint = `/clinical-episodes/?${params.toString()}`;
  const response = await apiClient.get<any>(endpoint);

  // Transformar episodios a pacientes del frontend
  let patients = response.data.map(transformClinicalEpisodeToPatient);

  // Aplicar filtros del lado del cliente (temporalmente)
  if (filters?.caseStatus) {
    patients = patients.filter((p: Patient) => p.caseStatus === filters.caseStatus);
  }

  if (filters?.service) {
    patients = patients.filter((p: Patient) => p.service === filters.service);
  }

  if (filters?.riskLevel) {
    patients = patients.filter((p: Patient) => p.riskLevel === filters.riskLevel);
  }

  // Ordenar: casos abiertos primero, luego por nivel de riesgo
  patients.sort((a: Patient, b: Patient) => {
    if (a.caseStatus === 'open' && b.caseStatus === 'closed') return -1;
    if (a.caseStatus === 'closed' && b.caseStatus === 'open') return 1;

    const riskOrder = { high: 0, medium: 1, low: 2 };
    return riskOrder[a.riskLevel] - riskOrder[b.riskLevel];
  });

  return {
    success: true,
    data: patients,
    pagination: {
      page: response.page,
      pageSize: response.page_size,
      total: response.total,
      totalPages: response.total_pages,
    },
  };
}

/**
 * GET /clinical-episodes/{episode_id}
 * Obtiene un episodio clínico (paciente) por su ID
 */
export async function getClinicalEpisode(id: string): Promise<Patient> {
  if (config.USE_MOCK_DATA) {
    const patient = mockPatients.find((p) => p.id === id);
    if (!patient) {
      throw new Error('Paciente no encontrado');
    }
    return patient;
  }

  const endpoint = `/clinical-episodes/${id}?include=patient`;
  const episode = await apiClient.get<any>(endpoint);

  return transformClinicalEpisodeToPatient(episode);
}

/**
 * GET /patients/
 * Obtiene todos los pacientes del sistema
 */
export async function getAllPatients(): Promise<any[]> {
  const endpoint = '/patients/';
  return await apiClient.get<any[]>(endpoint);
}

/**
 * POST /patients/
 * Crea un nuevo paciente
 */
export async function createPatient(patientData: {
  medical_identifier: string;
  first_name: string;
  last_name: string;
  rut: string;
  birth_date: string;
  gender: string;
}): Promise<any> {
  const endpoint = '/patients/';
  return await apiClient.post<any>(endpoint, patientData);
}

/**
 * PUT /clinical-episodes/{episode_id}
 * Actualiza un episodio clínico
 */
export async function updateClinicalEpisode(id: string, updates: Partial<Patient>): Promise<Patient> {
  // TODO: Implementar cuando el backend soporte actualizar episodios
  throw new Error('Actualizar paciente no está disponible aún');
}

/**
 * DELETE /clinical-episodes/{episode_id}
 * Elimina un episodio clínico
 */
export async function deleteClinicalEpisode(id: string): Promise<void> {
  // TODO: Implementar cuando el backend soporte eliminar episodios
  throw new Error('Eliminar paciente no está disponible aún');
}

// =============================================================================
// ALERTAS
// =============================================================================

/**
 * GET /patients/:patientId/alerts
 * Obtiene todas las alertas de un paciente
 * NOTA: No implementado en el backend aún
 */
export async function getPatientAlerts(patientId: string): Promise<Alert[]> {
  if (config.USE_MOCK_DATA) {
    return mockAlerts.filter((a) => a.patientId === patientId);
  }
  // TODO: Implementar cuando el backend tenga alertas
  return [];
}

/**
 * GET /alerts
 * Obtiene todas las alertas activas del sistema
 * NOTA: No implementado en el backend aún
 */
export async function getAllAlerts(): Promise<Alert[]> {
  if (config.USE_MOCK_DATA) {
    return mockAlerts;
  }
  // TODO: Implementar cuando el backend tenga alertas
  return [];
}

/**
 * POST /alerts/:id/acknowledge
 * Marca una alerta como reconocida/leída
 */
export async function acknowledgeAlert(id: string): Promise<void> {
  // TODO: Implementar cuando el backend tenga alertas
}

// =============================================================================
// TAREAS
// =============================================================================

/**
 * GET /task-instances/episode/{episode_id}
 * Obtiene todas las tareas de un episodio (paciente)
 */
export async function getPatientTasks(patientId: string): Promise<Task[]> {
  if (config.USE_MOCK_DATA) {
    return mockTasks.filter((t) => t.patientId === patientId);
  }

  const endpoint = `/task-instances/episode/${patientId}`;
  const taskInstances = await apiClient.get<any[]>(endpoint);

  return taskInstances.map(ti => transformTaskInstanceToTask(ti, patientId));
}

/**
 * GET /tasks
 * Obtiene todas las tareas (opcionalmente filtradas por usuario)
 */
export async function getAllTasks(assignedTo?: string): Promise<Task[]> {
  // TODO: El backend no tiene este endpoint global aún
  return [];
}

/**
 * POST /task-instances/
 * Crea una nueva tarea para un episodio
 */
export async function createTask(
  patientId: string,
  task: Omit<Task, 'id' | 'patientId' | 'createdAt'>
): Promise<Task> {
  if (config.USE_MOCK_DATA) {
    const newTask: Task = {
      ...task,
      id: 'task_' + Date.now(),
      patientId,
      createdAt: new Date().toISOString(),
    };
    mockTasks.push(newTask);
    return newTask;
  }

  const taskCreate = {
    episode_id: patientId,
    task_definition_id: '00000000-0000-0000-0000-000000000000', // TODO: Obtener ID real
    title: task.title,
    description: task.description || null,
    due_date: task.dueDate || null,
    priority: mapPriorityToBackend(task.priority),
    status: mapTaskStatusToBackend(task.status),
  };

  const created = await apiClient.post<any>('/task-instances/', taskCreate);

  return transformTaskInstanceToTask(created, patientId);
}

/**
 * PATCH /task-instances/{task_id}
 * Actualiza una tarea existente
 */
export async function updateTask(id: string, updates: Partial<Task>): Promise<Task> {
  const taskUpdate: any = {};

  if (updates.title !== undefined) taskUpdate.title = updates.title;
  if (updates.description !== undefined) taskUpdate.description = updates.description;
  if (updates.dueDate !== undefined) taskUpdate.due_date = updates.dueDate;
  if (updates.priority !== undefined) taskUpdate.priority = mapPriorityToBackend(updates.priority);
  if (updates.status !== undefined) taskUpdate.status = mapTaskStatusToBackend(updates.status);

  const updated = await apiClient.patch<any>(`/task-instances/${id}`, taskUpdate);

  return transformTaskInstanceToTask(updated);
}

/**
 * DELETE /task-instances/{task_id}
 * Elimina una tarea
 */
export async function deleteTask(id: string): Promise<void> {
  await apiClient.delete(`/task-instances/${id}`);
}

// =============================================================================
// DOCUMENTOS
// =============================================================================

/**
 * GET /patients/:patientId/documents
 * Obtiene todos los documentos de un paciente
 * NOTA: No implementado en el backend aún
 */
export async function getPatientDocuments(patientId: string): Promise<Document[]> {
  if (config.USE_MOCK_DATA) {
    return mockDocuments.filter((d) => d.patientId === patientId);
  }
  // TODO: Implementar cuando el backend tenga documentos
  return [];
}

/**
 * POST /patients/:patientId/documents
 * Sube un documento para un paciente
 */
export async function uploadDocument(
  patientId: string,
  file: File,
  uploadedBy: string
): Promise<Document> {
  // TODO: Implementar cuando el backend tenga documentos
  throw new Error('Subir documentos no está disponible aún');
}

/**
 * DELETE /documents/:id
 * Elimina un documento
 */
export async function deleteDocument(id: string): Promise<void> {
  // TODO: Implementar cuando el backend tenga documentos
  throw new Error('Eliminar documentos no está disponible aún');
}

/**
 * GET /documents/:id/download
 * Descarga un documento
 */
export async function downloadDocument(id: string): Promise<Blob> {
  // TODO: Implementar cuando el backend tenga documentos
  throw new Error('Descargar documentos no está disponible aún');
}

// =============================================================================
// TIMELINE / HISTORIAL
// =============================================================================

/**
 * GET /clinical-episodes/{episode_id}/history
 * Obtiene la línea de tiempo completa de un episodio (paciente)
 */
export async function getPatientTimeline(patientId: string): Promise<TimelineEvent[]> {
  if (config.USE_MOCK_DATA) {
    return mockTimelineEvents
      .filter((e) => e.patientId === patientId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  const endpoint = `/clinical-episodes/${patientId}/history`;
  const response = await apiClient.get<any>(endpoint);

  const events = response.events.map((e: any) =>
    transformHistoryEventToTimelineEvent(e, patientId)
  );

  // Ordenar por timestamp descendente (más reciente primero)
  events.sort((a: TimelineEvent, b: TimelineEvent) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return events;
}

// =============================================================================
// DASHBOARD / ESTADÍSTICAS
// =============================================================================

/**
 * GET /dashboard/stats
 * Obtiene las estadísticas del dashboard
 * NOTA: No implementado en el backend aún - retorna datos calculados
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  if (config.USE_MOCK_DATA) {
    return mockDashboardStats;
  }

  // Obtener todos los episodios para calcular estadísticas
  const response = await getClinicalEpisodes({ page: 1, pageSize: 100 });
  const patients = response.data;

  const totalPatients = patients.length;
  const highRiskPatients = patients.filter(p => p.riskLevel === 'high').length;
  const mediumRiskPatients = patients.filter(p => p.riskLevel === 'medium').length;
  const lowRiskPatients = patients.filter(p => p.riskLevel === 'low').length;

  // Calcular promedio de días de estadía
  const totalDays = patients.reduce((sum, p) => sum + p.daysInStay, 0);
  const averageStayDays = totalPatients > 0 ? Math.round(totalDays / totalPatients) : 0;

  // Calcular desviaciones (pacientes con días de estadía mayor a los esperados)
  const deviations = patients.filter(p => p.daysInStay > p.expectedDays).length;

  // Calcular estadísticas de riesgo social
  const highSocialRisk = patients.filter(p => (p.socialScore ?? -1) > 10).length;
  const mediumSocialRisk = patients.filter(p => (p.socialScore ?? -1) >= 6 && (p.socialScore ?? -1) <= 10).length;
  const lowSocialRisk = patients.filter(p => p.socialScore !== null && p.socialScore !== undefined && p.socialScore <= 5).length;

  return {
    totalPatients,
    highRisk: highRiskPatients,
    mediumRisk: mediumRiskPatients,
    lowRisk: lowRiskPatients,
    highSocialRisk,
    mediumSocialRisk,
    lowSocialRisk,
    averageStayDays,
    deviations,
  };
}

// =============================================================================
// DERIVACIONES
// =============================================================================

/**
 * POST /clinical-episodes/referrals
 * Crea una nueva derivación desde servicios clínicos
 */
export async function createReferral(referral: ReferralForm): Promise<Patient> {
  const referralCreate = {
    patient_id: referral.patientId,
    service: referral.service,
    diagnosis: referral.diagnosis,
    expected_days: referral.expectedDays,
    social_factors: referral.socialFactors || null,
    clinical_notes: referral.clinicalNotes || null,
    submitted_by: referral.submittedBy,
    admission_at: referral.admissionDate || new Date().toISOString(),
  };

  const endpoint = '/clinical-episodes/referrals';
  const response = await apiClient.post<any>(endpoint, referralCreate);

  return transformClinicalEpisodeToPatient(response);
}

// =============================================================================
// USUARIOS
// =============================================================================

/**
 * GET /users
 * Obtiene la lista de usuarios del sistema
 */
export async function getUsers(role?: string): Promise<User[]> {
  // TODO: Implementar cuando el backend tenga usuarios
  return [
    { id: '1', email: 'coordinador@hospital.cl', name: 'Ana Vargas', role: 'coordinator' },
    { id: '2', email: 'social@hospital.cl', name: 'Patricia Ruiz', role: 'social-worker' },
  ];
}

// =============================================================================
// IMPORTACIÓN DE DATOS DESDE EXCEL
// =============================================================================

/**
 * POST /excel/upload-patients
 * Importa datos de pacientes desde un archivo Excel (Default type)
 */
export async function importPatientsFromExcel(file: File): Promise<ExcelImportResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.uploadFile<any>('/excel/upload-patients', formData);

  return {
    success: response.status === 'success',
    imported: response.patients_processed || 0,
    errors: response.errors || [],
  };
}

/**
 * POST /excel/upload-social-scores
 * Importa datos de social scores desde un archivo Excel (Score Social type)
 * 
 * Expects a file with "Data Casos" sheet containing:
 * - Episodio / Estadía: Episode identifier
 * - Puntaje: The social score (can be null)
 * - Fecha Asignación: Recorded date
 * - Encuestadora: Person who recorded
 * - Motivo: Reason if score is null
 */
export async function importSocialScoresFromExcel(file: File): Promise<ExcelImportResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.uploadFile<any>('/excel/upload-social-scores', formData);

  return {
    success: response.status === 'success',
    imported: response.scores_processed || 0,
    errors: response.errors || [],
  };
}

// =============================================================================
// SERVICIOS CLÍNICOS
// =============================================================================

/**
 * GET /services
 * Obtiene la lista de servicios clínicos disponibles
 */
export async function getClinicalServices(): Promise<string[]> {
  // TODO: Implementar cuando el backend tenga servicios
  return [
    'Medicina Interna',
    'Cirugía',
    'Cardiología',
    'Traumatología',
    'Geriatría',
    'Neurología',
  ];
}

// Exportar el cliente API para uso avanzado si se necesita
export { apiClient };
