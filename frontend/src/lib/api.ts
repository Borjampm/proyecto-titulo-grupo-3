/**
 * Servicio de API para conectar con el backend
 * 
 * Este archivo contiene todas las funciones necesarias para comunicarse
 * con tu API backend. Cuando tu backend esté listo, simplemente actualiza
 * la URL en /lib/config.ts y cambia USE_MOCK_DATA a false.
 */

import config from './config';
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
  ApiResponse,
  PaginatedResponse,
  PatientFilters,
  ExcelImportResult,
} from '../types';

// Importar datos mock para fallback
import {
  mockPatients,
  mockAlerts,
  mockTasks,
  mockDocuments,
  mockTimelineEvents,
  mockDashboardStats,
} from './mockData';

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
    this.token = this.getStoredToken();
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
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
        throw new Error(error.message || 'Error en la petición');
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

  async put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
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
    
    const headers: HeadersInit = {};
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
// AUTENTICACIÓN
// =============================================================================

/**
 * POST /auth/login
 * Inicia sesión con email y contraseña
 */
export async function login(email: string, password: string): Promise<AuthResponse> {
  if (config.USE_MOCK_DATA) {
    // Mock response
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

  const response = await apiClient.post<ApiResponse<AuthResponse>>('/auth/login', {
    email,
    password,
  });

  if (response.success && response.data) {
    apiClient.setToken(response.data.token);
    return response.data;
  }

  throw new Error(response.error || 'Error al iniciar sesión');
}

/**
 * POST /auth/logout
 * Cierra la sesión actual
 */
export async function logout(): Promise<void> {
  if (config.USE_MOCK_DATA) {
    apiClient.clearToken();
    return;
  }

  await apiClient.post('/auth/logout', {});
  apiClient.clearToken();
}

/**
 * GET /auth/me
 * Obtiene el usuario actualmente autenticado
 */
export async function getCurrentUser(): Promise<User> {
  if (config.USE_MOCK_DATA) {
    return {
      id: '1',
      email: 'usuario@ejemplo.com',
      name: 'Usuario de Prueba',
      role: 'coordinator',
    };
  }

  const response = await apiClient.get<ApiResponse<User>>('/auth/me');
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener usuario');
}

// =============================================================================
// PACIENTES
// =============================================================================

/**
 * GET /patients
 * Obtiene la lista de pacientes con filtros opcionales
 */
export async function getPatients(filters?: PatientFilters): Promise<PaginatedResponse<Patient>> {
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

  const queryParams = new URLSearchParams();
  if (filters?.search) queryParams.append('search', filters.search);
  if (filters?.caseStatus) queryParams.append('caseStatus', filters.caseStatus);
  if (filters?.service) queryParams.append('service', filters.service);
  if (filters?.riskLevel) queryParams.append('riskLevel', filters.riskLevel);
  if (filters?.page) queryParams.append('page', filters.page.toString());
  if (filters?.pageSize) queryParams.append('pageSize', filters.pageSize.toString());

  const endpoint = `/patients${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return apiClient.get<PaginatedResponse<Patient>>(endpoint);
}

/**
 * GET /patients/:id
 * Obtiene un paciente por su ID
 */
export async function getPatient(id: string): Promise<Patient> {
  if (config.USE_MOCK_DATA) {
    const patient = mockPatients.find((p) => p.id === id);
    if (!patient) {
      throw new Error('Paciente no encontrado');
    }
    return patient;
  }

  const response = await apiClient.get<ApiResponse<Patient>>(`/patients/${id}`);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener paciente');
}

/**
 * POST /patients
 * Crea un nuevo paciente
 */
export async function createPatient(patient: Omit<Patient, 'id'>): Promise<Patient> {
  if (config.USE_MOCK_DATA) {
    const newPatient: Patient = {
      ...patient,
      id: 'patient_' + Date.now(),
    };
    mockPatients.push(newPatient);
    return newPatient;
  }

  const response = await apiClient.post<ApiResponse<Patient>>('/patients', patient);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al crear paciente');
}

/**
 * PUT /patients/:id
 * Actualiza un paciente existente
 */
export async function updatePatient(id: string, updates: Partial<Patient>): Promise<Patient> {
  if (config.USE_MOCK_DATA) {
    const index = mockPatients.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error('Paciente no encontrado');
    }
    mockPatients[index] = { ...mockPatients[index], ...updates };
    return mockPatients[index];
  }

  const response = await apiClient.put<ApiResponse<Patient>>(`/patients/${id}`, updates);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al actualizar paciente');
}

/**
 * DELETE /patients/:id
 * Elimina un paciente
 */
export async function deletePatient(id: string): Promise<void> {
  if (config.USE_MOCK_DATA) {
    const index = mockPatients.findIndex((p) => p.id === id);
    if (index !== -1) {
      mockPatients.splice(index, 1);
    }
    return;
  }

  await apiClient.delete(`/patients/${id}`);
}

// =============================================================================
// ALERTAS
// =============================================================================

/**
 * GET /patients/:patientId/alerts
 * Obtiene todas las alertas de un paciente
 */
export async function getPatientAlerts(patientId: string): Promise<Alert[]> {
  if (config.USE_MOCK_DATA) {
    return mockAlerts.filter((a) => a.patientId === patientId);
  }

  const response = await apiClient.get<ApiResponse<Alert[]>>(`/patients/${patientId}/alerts`);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener alertas');
}

/**
 * GET /alerts
 * Obtiene todas las alertas activas del sistema
 */
export async function getAllAlerts(): Promise<Alert[]> {
  if (config.USE_MOCK_DATA) {
    return mockAlerts;
  }

  const response = await apiClient.get<ApiResponse<Alert[]>>('/alerts');
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener alertas');
}

/**
 * POST /alerts/:id/acknowledge
 * Marca una alerta como reconocida/leída
 */
export async function acknowledgeAlert(id: string): Promise<void> {
  if (config.USE_MOCK_DATA) {
    return;
  }

  await apiClient.post(`/alerts/${id}/acknowledge`, {});
}

// =============================================================================
// TAREAS
// =============================================================================

/**
 * GET /patients/:patientId/tasks
 * Obtiene todas las tareas de un paciente
 */
export async function getPatientTasks(patientId: string): Promise<Task[]> {
  if (config.USE_MOCK_DATA) {
    return mockTasks.filter((t) => t.patientId === patientId);
  }

  const response = await apiClient.get<ApiResponse<Task[]>>(`/patients/${patientId}/tasks`);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener tareas');
}

/**
 * GET /tasks
 * Obtiene todas las tareas (opcionalmente filtradas por usuario)
 */
export async function getAllTasks(assignedTo?: string): Promise<Task[]> {
  if (config.USE_MOCK_DATA) {
    if (assignedTo) {
      return mockTasks.filter((t) => t.assignedTo === assignedTo);
    }
    return mockTasks;
  }

  const endpoint = assignedTo ? `/tasks?assignedTo=${assignedTo}` : '/tasks';
  const response = await apiClient.get<ApiResponse<Task[]>>(endpoint);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener tareas');
}

/**
 * POST /patients/:patientId/tasks
 * Crea una nueva tarea para un paciente
 */
export async function createTask(patientId: string, task: Omit<Task, 'id' | 'patientId' | 'createdAt'>): Promise<Task> {
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

  const response = await apiClient.post<ApiResponse<Task>>(`/patients/${patientId}/tasks`, task);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al crear tarea');
}

/**
 * PUT /tasks/:id
 * Actualiza una tarea existente
 */
export async function updateTask(id: string, updates: Partial<Task>): Promise<Task> {
  if (config.USE_MOCK_DATA) {
    const index = mockTasks.findIndex((t) => t.id === id);
    if (index === -1) {
      throw new Error('Tarea no encontrada');
    }
    
    const updatedTask = { ...mockTasks[index], ...updates };
    
    // Si se marca como completada, agregar fecha de completado
    if (updates.status === 'completed' && !updatedTask.completedAt) {
      updatedTask.completedAt = new Date().toISOString();
    }
    
    mockTasks[index] = updatedTask;
    return mockTasks[index];
  }

  const response = await apiClient.put<ApiResponse<Task>>(`/tasks/${id}`, updates);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al actualizar tarea');
}

/**
 * DELETE /tasks/:id
 * Elimina una tarea
 */
export async function deleteTask(id: string): Promise<void> {
  if (config.USE_MOCK_DATA) {
    const index = mockTasks.findIndex((t) => t.id === id);
    if (index !== -1) {
      mockTasks.splice(index, 1);
    }
    return;
  }

  await apiClient.delete(`/tasks/${id}`);
}

// =============================================================================
// DOCUMENTOS
// =============================================================================

/**
 * GET /patients/:patientId/documents
 * Obtiene todos los documentos de un paciente
 */
export async function getPatientDocuments(patientId: string): Promise<Document[]> {
  if (config.USE_MOCK_DATA) {
    return mockDocuments.filter((d) => d.patientId === patientId);
  }

  const response = await apiClient.get<ApiResponse<Document[]>>(`/patients/${patientId}/documents`);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener documentos');
}

/**
 * POST /patients/:patientId/documents
 * Sube un documento para un paciente
 */
export async function uploadDocument(patientId: string, file: File, uploadedBy: string): Promise<Document> {
  if (config.USE_MOCK_DATA) {
    const newDocument: Document = {
      id: 'doc_' + Date.now(),
      patientId,
      name: file.name,
      type: file.type,
      uploadedBy,
      uploadedAt: new Date().toISOString(),
      url: URL.createObjectURL(file),
    };
    mockDocuments.push(newDocument);
    return newDocument;
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('uploadedBy', uploadedBy);

  const response = await apiClient.uploadFile<ApiResponse<Document>>(
    `/patients/${patientId}/documents`,
    formData
  );
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al subir documento');
}

/**
 * DELETE /documents/:id
 * Elimina un documento
 */
export async function deleteDocument(id: string): Promise<void> {
  if (config.USE_MOCK_DATA) {
    const index = mockDocuments.findIndex((d) => d.id === id);
    if (index !== -1) {
      mockDocuments.splice(index, 1);
    }
    return;
  }

  await apiClient.delete(`/documents/${id}`);
}

/**
 * GET /documents/:id/download
 * Descarga un documento
 */
export async function downloadDocument(id: string): Promise<Blob> {
  if (config.USE_MOCK_DATA) {
    throw new Error('Descarga de documentos no disponible en modo demo');
  }

  const url = `${config.BACKEND_URL}/documents/${id}/download`;
  const token = localStorage.getItem('auth_token');
  
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { headers });
  
  if (!response.ok) {
    throw new Error('Error al descargar documento');
  }

  return await response.blob();
}

// =============================================================================
// TIMELINE / HISTORIAL
// =============================================================================

/**
 * GET /patients/:patientId/timeline
 * Obtiene la línea de tiempo completa de un paciente
 */
export async function getPatientTimeline(patientId: string): Promise<TimelineEvent[]> {
  if (config.USE_MOCK_DATA) {
    return mockTimelineEvents
      .filter((e) => e.patientId === patientId)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  const response = await apiClient.get<ApiResponse<TimelineEvent[]>>(`/patients/${patientId}/timeline`);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener línea de tiempo');
}

// =============================================================================
// DASHBOARD / ESTADÍSTICAS
// =============================================================================

/**
 * GET /dashboard/stats
 * Obtiene las estadísticas del dashboard
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  if (config.USE_MOCK_DATA) {
    return mockDashboardStats;
  }

  const response = await apiClient.get<ApiResponse<DashboardStats>>('/dashboard/stats');
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener estadísticas');
}

// =============================================================================
// DERIVACIONES
// =============================================================================

/**
 * POST /referrals
 * Crea una nueva derivación desde servicios clínicos
 */
export async function createReferral(referral: ReferralForm): Promise<Patient> {
  if (config.USE_MOCK_DATA) {
    const newPatient: Patient = {
      id: 'patient_' + Date.now(),
      name: referral.patientName,
      age: referral.age,
      admissionDate: referral.admissionDate,
      service: referral.service,
      responsible: referral.submittedBy,
      diagnosis: referral.diagnosis,
      expectedDays: referral.expectedDays,
      daysInStay: 0,
      riskLevel: 'low',
      socialRisk: referral.socialFactors.length > 0,
      financialRisk: false,
      status: 'active',
      caseStatus: 'open',
      grg: 'GRD-000',
    };
    mockPatients.push(newPatient);
    return newPatient;
  }

  const response = await apiClient.post<ApiResponse<Patient>>('/referrals', referral);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al crear derivación');
}

// =============================================================================
// USUARIOS
// =============================================================================

/**
 * GET /users
 * Obtiene la lista de usuarios del sistema
 */
export async function getUsers(role?: string): Promise<User[]> {
  if (config.USE_MOCK_DATA) {
    const mockUsers: User[] = [
      { id: '1', email: 'coordinador@hospital.cl', name: 'Ana Vargas', role: 'coordinator' },
      { id: '2', email: 'social@hospital.cl', name: 'Patricia Ruiz', role: 'social-worker' },
      { id: '3', email: 'analista@hospital.cl', name: 'Carlos Méndez', role: 'analyst' },
      { id: '4', email: 'jefe@hospital.cl', name: 'Dr. Roberto Silva', role: 'chief' },
      { id: '5', email: 'dr.perez@hospital.cl', name: 'Dr. Pérez', role: 'clinical-service', service: 'Medicina Interna' },
    ];

    if (role) {
      return mockUsers.filter((u) => u.role === role);
    }
    return mockUsers;
  }

  const endpoint = role ? `/users?role=${role}` : '/users';
  const response = await apiClient.get<ApiResponse<User[]>>(endpoint);
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener usuarios');
}

// =============================================================================
// IMPORTACIÓN DE DATOS DESDE EXCEL
// =============================================================================

/**
 * POST /import/excel
 * Importa datos de pacientes desde un archivo Excel/CSV
 */
export async function importPatientsFromExcel(file: File): Promise<ExcelImportResult> {
  if (config.USE_MOCK_DATA) {
    // Simulación de importación
    return {
      success: true,
      imported: 5,
      errors: [],
    };
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.uploadFile<ApiResponse<ExcelImportResult>>(
    '/import/excel',
    formData
  );
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al importar datos');
}

// =============================================================================
// SERVICIOS CLÍNICOS
// =============================================================================

/**
 * GET /services
 * Obtiene la lista de servicios clínicos disponibles
 */
export async function getClinicalServices(): Promise<string[]> {
  if (config.USE_MOCK_DATA) {
    return [
      'Medicina Interna',
      'Cirugía',
      'Cardiología',
      'Traumatología',
      'Geriatría',
      'Neurología',
      'Pediatría',
      'Oncología',
      'Urgencias',
    ];
  }

  const response = await apiClient.get<ApiResponse<string[]>>('/services');
  
  if (response.success && response.data) {
    return response.data;
  }

  throw new Error(response.error || 'Error al obtener servicios');
}

// Exportar el cliente API para uso avanzado si se necesita
export { apiClient };
