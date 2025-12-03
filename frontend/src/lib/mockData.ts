import { Patient, Alert, DashboardStats, Task, Document, TimelineEvent } from '../types';

export const mockPatients: Patient[] = [
  {
    id: '1',
    name: 'María González',
    age: 68,
    admissionDate: '2025-10-15',
    service: 'Medicina Interna',
    responsible: 'Dr. Pérez',
    daysInStay: 8,
    expectedDays: 5,
    riskLevel: 'high',
    socialRisk: true,
    financialRisk: false,
    socialScore: 12,
    status: 'active',
    caseStatus: 'open',
    grg: 'GRD-193',
    diagnosis: 'Neumonía comunitaria'
  },
  {
    id: '2',
    name: 'Juan Rodríguez',
    age: 45,
    admissionDate: '2025-10-20',
    service: 'Cirugía',
    responsible: 'Dra. Silva',
    daysInStay: 3,
    expectedDays: 4,
    riskLevel: 'low',
    socialRisk: false,
    financialRisk: false,
    socialScore: 3,
    status: 'active',
    caseStatus: 'open',
    grg: 'GRD-468',
    diagnosis: 'Apendicitis aguda'
  },
  {
    id: '3',
    name: 'Ana Martínez',
    age: 72,
    admissionDate: '2025-10-18',
    service: 'Cardiología',
    responsible: 'Dr. López',
    daysInStay: 5,
    expectedDays: 6,
    riskLevel: 'medium',
    socialRisk: true,
    financialRisk: true,
    socialScore: 8,
    status: 'active',
    caseStatus: 'open',
    grg: 'GRD-121',
    diagnosis: 'Insuficiencia cardíaca'
  },
  {
    id: '4',
    name: 'Pedro Sánchez',
    age: 55,
    admissionDate: '2025-10-21',
    service: 'Traumatología',
    responsible: 'Dra. Torres',
    daysInStay: 2,
    expectedDays: 3,
    riskLevel: 'low',
    socialRisk: false,
    financialRisk: false,
    socialScore: 2,
    status: 'active',
    caseStatus: 'closed',
    grg: 'GRD-209',
    diagnosis: 'Fractura de cadera'
  },
  {
    id: '5',
    name: 'Carmen Díaz',
    age: 80,
    admissionDate: '2025-10-12',
    service: 'Geriatría',
    responsible: 'Dr. Ramírez',
    daysInStay: 11,
    expectedDays: 7,
    riskLevel: 'high',
    socialRisk: true,
    financialRisk: false,
    socialScore: 15,
    status: 'pending-discharge',
    caseStatus: 'open',
    grg: 'GRD-089',
    diagnosis: 'Delirium + deterioro funcional'
  },
  {
    id: '6',
    name: 'Luis Hernández',
    age: 62,
    admissionDate: '2025-10-19',
    service: 'Neurología',
    responsible: 'Dra. Morales',
    daysInStay: 4,
    expectedDays: 5,
    riskLevel: 'medium',
    socialRisk: false,
    financialRisk: true,
    socialScore: 6,
    status: 'active',
    caseStatus: 'closed',
    grg: 'GRD-014',
    diagnosis: 'ACV isquémico'
  }
];

export const mockAlerts: Alert[] = [
  {
    id: 'a1',
    patientId: '1',
    type: 'stay-deviation',
    severity: 'high',
    message: 'Estadía supera en 3 días lo esperado según GRD',
    createdAt: '2025-10-22T08:00:00'
  },
  {
    id: 'a2',
    patientId: '1',
    type: 'social-risk',
    severity: 'high',
    message: 'Factores sociales detectados: vive sola, sin red de apoyo',
    createdAt: '2025-10-22T10:35:00'
  },
  {
    id: 'a3',
    patientId: '5',
    type: 'stay-deviation',
    severity: 'high',
    message: 'Estadía supera en 4 días lo esperado según GRD',
    createdAt: '2025-10-23T08:00:00'
  },
  {
    id: 'a4',
    patientId: '5',
    type: 'social-risk',
    severity: 'high',
    message: 'Alta complejidad social: familia no puede asumir cuidados',
    createdAt: '2025-10-23T11:25:00'
  },
  {
    id: 'a6',
    patientId: '3',
    type: 'predicted-overstay',
    severity: 'medium',
    message: 'Predicción de sobrestadía: 65% probabilidad',
    createdAt: '2025-10-24T08:30:00'
  }
];

export const mockDashboardStats: DashboardStats = {
  totalPatients: 6,
  highRisk: 2,
  mediumRisk: 2,
  lowRisk: 2,
  highSocialRisk: 2,
  mediumSocialRisk: 2,
  lowSocialRisk: 2,
  averageStayDays: 5.5,
  deviations: 2
};

export const mockTasks: Task[] = [
  {
    id: 't1',
    patientId: '1',
    title: 'Contactar centro de día',
    description: 'Gestionar derivación a centro de día para seguimiento post-alta',
    status: 'in-progress',
    priority: 'high',
    assignedTo: 'Patricia Ruiz',
    createdBy: 'Patricia Ruiz',
    createdAt: '2025-10-22T10:35:00',
    dueDate: '2025-10-25T00:00:00'
  },
  {
    id: 't2',
    patientId: '1',
    title: 'Evaluación final médica',
    description: 'Revisión antes del alta, confirmar finalización de antibióticos',
    status: 'pending',
    priority: 'medium',
    assignedTo: 'Dr. Pérez',
    createdBy: 'Ana Vargas',
    createdAt: '2025-10-22T16:00:00',
    dueDate: '2025-10-25T00:00:00'
  },
  {
    id: 't3',
    patientId: '1',
    title: 'Preparar informe de alta',
    description: 'Documentar proceso de estadía y recomendaciones',
    status: 'completed',
    priority: 'low',
    assignedTo: 'Ana Vargas',
    createdBy: 'Ana Vargas',
    createdAt: '2025-10-21T09:00:00',
    completedAt: '2025-10-23T14:20:00'
  },
  {
    id: 't4',
    patientId: '3',
    title: 'Gestionar fondo solidario',
    description: 'Solicitar cobertura adicional para medicamentos ambulatorios',
    status: 'in-progress',
    priority: 'high',
    assignedTo: 'Patricia Ruiz',
    createdBy: 'Ana Vargas',
    createdAt: '2025-10-21T09:10:00',
    dueDate: '2025-10-24T00:00:00'
  },
  {
    id: 't5',
    patientId: '5',
    title: 'Búsqueda de residencia temporal',
    description: 'Contactar ELEAM y opciones de residencia para adultos mayores',
    status: 'in-progress',
    priority: 'high',
    assignedTo: 'Patricia Ruiz',
    createdBy: 'Patricia Ruiz',
    createdAt: '2025-10-23T11:30:00',
    dueDate: '2025-10-26T00:00:00'
  }
];

export const mockDocuments: Document[] = [
  {
    id: 'd1',
    patientId: '1',
    name: 'Informe_Social_Inicial.pdf',
    type: 'application/pdf',
    uploadedBy: 'Patricia Ruiz',
    uploadedAt: '2025-10-16T09:00:00',
    url: '#'
  },
  {
    id: 'd2',
    patientId: '1',
    name: 'Resultados_Laboratorio.pdf',
    type: 'application/pdf',
    uploadedBy: 'Dr. Pérez',
    uploadedAt: '2025-10-17T11:30:00',
    url: '#'
  },
  {
    id: 'd3',
    patientId: '1',
    name: 'Radiografía_Tórax.jpg',
    type: 'image/jpeg',
    uploadedBy: 'Dr. Pérez',
    uploadedAt: '2025-10-15T14:20:00',
    url: '#'
  },
  {
    id: 'd4',
    patientId: '3',
    name: 'Solicitud_Fondo_Solidario.pdf',
    type: 'application/pdf',
    uploadedBy: 'Ana Vargas',
    uploadedAt: '2025-10-21T10:15:00',
    url: '#'
  },
  {
    id: 'd5',
    patientId: '5',
    name: 'Evaluación_Funcional.pdf',
    type: 'application/pdf',
    uploadedBy: 'Dr. Ramírez',
    uploadedAt: '2025-10-13T08:45:00',
    url: '#'
  }
];

export const mockTimelineEvents: TimelineEvent[] = [
  // Patient 1 - María González
  {
    id: 'te1',
    patientId: '1',
    type: 'admission',
    timestamp: '2025-10-15T08:00:00',
    author: 'Sistema',
    title: 'Ingreso al hospital',
    description: 'Paciente ingresada en Medicina Interna por neumonía comunitaria'
  },
  {
    id: 'te2',
    patientId: '1',
    type: 'document',
    timestamp: '2025-10-15T14:20:00',
    author: 'Dr. Pérez',
    role: 'clinical-service',
    title: 'Documento cargado: Radiografía_Tórax.jpg',
    description: 'Imagen de radiografía de tórax',
    relatedId: 'd3',
    metadata: { documentType: 'image/jpeg' }
  },
  {
    id: 'te3',
    patientId: '1',
    type: 'document',
    timestamp: '2025-10-16T09:00:00',
    author: 'Patricia Ruiz',
    role: 'social-worker',
    title: 'Documento cargado: Informe_Social_Inicial.pdf',
    description: 'Evaluación social inicial del paciente',
    relatedId: 'd1',
    metadata: { documentType: 'application/pdf' }
  },
  {
    id: 'te4',
    patientId: '1',
    type: 'document',
    timestamp: '2025-10-17T11:30:00',
    author: 'Dr. Pérez',
    role: 'clinical-service',
    title: 'Documento cargado: Resultados_Laboratorio.pdf',
    description: 'Resultados de análisis de laboratorio',
    relatedId: 'd2',
    metadata: { documentType: 'application/pdf' }
  },
  {
    id: 'te5',
    patientId: '1',
    type: 'task-created',
    timestamp: '2025-10-21T09:00:00',
    author: 'Ana Vargas',
    role: 'coordinator',
    title: 'Tarea creada: Preparar informe de alta',
    description: 'Documentar proceso de estadía y recomendaciones',
    relatedId: 't3',
    metadata: { taskPriority: 'low', taskStatus: 'pending' }
  },
  {
    id: 'te6',
    patientId: '1',
    type: 'alert',
    timestamp: '2025-10-22T08:00:00',
    author: 'Sistema',
    title: 'Alerta: Desvío de estadía',
    description: 'Estadía supera en 3 días lo esperado según GRD',
    relatedId: 'a1',
    metadata: { severity: 'high', alertType: 'stay-deviation' }
  },
  {
    id: 'te8',
    patientId: '1',
    type: 'alert',
    timestamp: '2025-10-22T10:35:00',
    author: 'Sistema',
    title: 'Alerta: Riesgo social',
    description: 'Factores sociales detectados: vive sola, sin red de apoyo',
    relatedId: 'a2',
    metadata: { severity: 'high', alertType: 'social-risk' }
  },
  {
    id: 'te9',
    patientId: '1',
    type: 'task-created',
    timestamp: '2025-10-22T10:35:00',
    author: 'Patricia Ruiz',
    role: 'social-worker',
    title: 'Tarea creada: Contactar centro de día',
    description: 'Gestionar derivación a centro de día para seguimiento post-alta',
    relatedId: 't1',
    metadata: { taskPriority: 'high', taskStatus: 'pending' }
  },
  {
    id: 'te10',
    patientId: '1',
    type: 'task-created',
    timestamp: '2025-10-22T16:00:00',
    author: 'Ana Vargas',
    role: 'coordinator',
    title: 'Tarea creada: Evaluación final médica',
    description: 'Revisión antes del alta, confirmar finalización de antibióticos',
    relatedId: 't2',
    metadata: { taskPriority: 'medium', taskStatus: 'pending' }
  },
  {
    id: 'te11',
    patientId: '1',
    type: 'task-completed',
    timestamp: '2025-10-23T14:20:00',
    author: 'Ana Vargas',
    role: 'coordinator',
    title: 'Tarea completada: Preparar informe de alta',
    description: 'Informe de alta finalizado y revisado',
    relatedId: 't3',
    metadata: { taskPriority: 'low', taskStatus: 'completed' }
  },
  // Patient 3 - Ana Martínez
  {
    id: 'te12',
    patientId: '3',
    type: 'admission',
    timestamp: '2025-10-18T10:30:00',
    author: 'Sistema',
    title: 'Ingreso al hospital',
    description: 'Paciente ingresada en Cardiología por insuficiencia cardíaca'
  },
  {
    id: 'te13',
    patientId: '3',
    type: 'alert',
    timestamp: '2025-10-21T09:05:00',
    author: 'Sistema',
    title: 'Alerta: Riesgo financiero',
    description: 'Cobertura financiera insuficiente detectada',
    relatedId: 'a5',
    metadata: { severity: 'medium', alertType: 'financial-risk' }
  },
  {
    id: 'te16',
    patientId: '3',
    type: 'task-created',
    timestamp: '2025-10-21T09:10:00',
    author: 'Ana Vargas',
    role: 'coordinator',
    title: 'Tarea creada: Gestionar fondo solidario',
    description: 'Solicitar cobertura adicional para medicamentos ambulatorios',
    relatedId: 't4',
    metadata: { taskPriority: 'high', taskStatus: 'pending' }
  },
  {
    id: 'te17',
    patientId: '3',
    type: 'document',
    timestamp: '2025-10-21T10:15:00',
    author: 'Ana Vargas',
    role: 'coordinator',
    title: 'Documento cargado: Solicitud_Fondo_Solidario.pdf',
    description: 'Solicitud de cobertura adicional',
    relatedId: 'd4',
    metadata: { documentType: 'application/pdf' }
  },
  // Patient 5 - Carmen Díaz
  {
    id: 'te16',
    patientId: '5',
    type: 'admission',
    timestamp: '2025-10-12T07:15:00',
    author: 'Sistema',
    title: 'Ingreso al hospital',
    description: 'Paciente ingresada en Geriatría por delirium y deterioro funcional'
  },
  {
    id: 'te17',
    patientId: '5',
    type: 'document',
    timestamp: '2025-10-13T08:45:00',
    author: 'Dr. Ramírez',
    role: 'clinical-service',
    title: 'Documento cargado: Evaluación_Funcional.pdf',
    description: 'Evaluación del estado funcional del paciente',
    relatedId: 'd5',
    metadata: { documentType: 'application/pdf' }
  },
  {
    id: 'te18',
    patientId: '5',
    type: 'alert',
    timestamp: '2025-10-23T08:00:00',
    author: 'Sistema',
    title: 'Alerta: Desvío de estadía',
    description: 'Estadía supera en 4 días lo esperado según GRD',
    relatedId: 'a3',
    metadata: { severity: 'high', alertType: 'stay-deviation' }
  },
  {
    id: 'te19',
    patientId: '5',
    type: 'alert',
    timestamp: '2025-10-23T11:25:00',
    author: 'Sistema',
    title: 'Alerta: Riesgo social alto',
    description: 'Alta complejidad social: familia no puede asumir cuidados',
    relatedId: 'a4',
    metadata: { severity: 'high', alertType: 'social-risk' }
  },
  {
    id: 'te20',
    patientId: '5',
    type: 'task-created',
    timestamp: '2025-10-23T11:30:00',
    author: 'Patricia Ruiz',
    role: 'social-worker',
    title: 'Tarea creada: Búsqueda de residencia temporal',
    description: 'Contactar ELEAM y opciones de residencia para adultos mayores',
    relatedId: 't5',
    metadata: { taskPriority: 'high', taskStatus: 'pending' }
  },
  {
    id: 'te21',
    patientId: '5',
    type: 'status-change',
    timestamp: '2025-10-23T16:00:00',
    author: 'Dr. Ramírez',
    role: 'clinical-service',
    title: 'Estado cambiado a: Pendiente Alta',
    description: 'Condición médica estable, pendiente resolución de situación social'
  }
];
