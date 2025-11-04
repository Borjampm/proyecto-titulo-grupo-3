export type RiskLevel = 'low' | 'medium' | 'high';
export type PatientStatus = 'active' | 'pending-discharge' | 'discharged';
export type CaseStatus = 'open' | 'closed';
export type UserRole = 'coordinator' | 'social-worker' | 'analyst' | 'chief' | 'clinical-service';

export interface Patient {
  id: string;
  rut?: string; // RUT del paciente
  name: string;
  age: number;
  admissionDate: string;
  dischargeDate?: string; // Fecha de alta si existe
  service: string;
  responsible: string;
  bed?: string; // Número de cama
  prevision?: string; // Previsión de salud (FONASA, ISAPRE, etc.)
  contactNumber?: string; // Número de contacto
  daysInStay: number;
  expectedDays: number;
  riskLevel: RiskLevel;
  socialRisk: boolean;
  financialRisk: boolean;
  status: PatientStatus;
  caseStatus: CaseStatus;
  grg: string;
  diagnosis: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface Alert {
  id: string;
  patientId: string;
  type: 'stay-deviation' | 'social-risk' | 'financial-risk';
  severity: RiskLevel;
  message: string;
  createdAt: string;
}

export interface ReferralForm {
  patientName: string;
  age: number;
  service: string;
  diagnosis: string;
  admissionDate: string;
  expectedDays: number;
  socialFactors: string;
  clinicalNotes: string;
  submittedBy: string;
}

export interface DashboardStats {
  totalPatients: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
  averageStayDays: number;
  deviations: number;
}

export type TaskStatus = 'pending' | 'in-progress' | 'completed';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface Task {
  id: string;
  patientId: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignedTo: string;
  createdBy: string;
  createdAt: string;
  completedAt?: string;
  dueDate?: string;
}

export interface Document {
  id: string;
  patientId: string;
  name: string;
  type: string;
  uploadedBy: string;
  uploadedAt: string;
  url: string;
}

export type TimelineEventType = 'task-created' | 'task-completed' | 'task-updated' | 'document' | 'alert' | 'admission' | 'status-change';

export interface TimelineEvent {
  id: string;
  patientId: string;
  type: TimelineEventType;
  timestamp: string;
  author: string;
  role?: UserRole;
  title: string;
  description: string;
  relatedId?: string;
  metadata?: {
    taskStatus?: TaskStatus;
    taskPriority?: TaskPriority;
    documentType?: string;
    alertType?: string;
    severity?: RiskLevel;
  };
}

// Tipos adicionales para la API

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  service?: string; // Para usuarios de servicios clínicos
  createdAt?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export interface PatientFilters {
  search?: string;
  caseStatus?: CaseStatus;
  service?: string;
  riskLevel?: RiskLevel;
  page?: number;
  pageSize?: number;
}

export interface UploadedFile {
  file: File;
  patientId?: string;
}

export interface ExcelImportResult {
  success: boolean;
  imported: number;
  errors: string[];
  patients?: Patient[];
}
