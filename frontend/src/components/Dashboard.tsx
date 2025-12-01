import { useEffect, useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Users, AlertTriangle, TrendingUp, Clock, Activity, ClipboardList, Circle, Calendar } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { getDashboardStats, getClinicalEpisodes, getAllTasks } from '../lib/api-fastapi';
import { DashboardStats, Patient, Task } from '../types';

interface DashboardProps {
  onNavigateToPatients?: (filters: { sortBy?: string; socialScoreRange?: [number, number]; caseStatus?: string; riskLevel?: string }) => void;
  onSelectPatient?: (patient: Patient) => void;
}

export function Dashboard({ onNavigateToPatients, onSelectPatient }: DashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
  const [totalOpenTasks, setTotalOpenTasks] = useState(0);
  const [urgentPatients, setUrgentPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, urgentPatientsData, tasksData] = await Promise.all([
        getDashboardStats(),
        getClinicalEpisodes({ riskLevel: 'high', pageSize: 5 }),
        getAllTasks({ openOnly: true, orderByDueDate: true }),
      ]);
      
      setStats(statsData);
      setUrgentPatients(urgentPatientsData.data);
      // Filter pending tasks and limit to 5 for display
      const pending = tasksData.filter(t => t.status === 'pending');
      setPendingTasks(pending.slice(0, 5));
      setTotalOpenTasks(tasksData.length);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Cargando dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2>Panel de Control - Gestión de Estadía</h2>
        <p className="text-muted-foreground mt-1">
          Resumen de pacientes activos y alertas del sistema
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigateToPatients?.({ caseStatus: 'open' })}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Casos Abiertos</p>
              <p className="mt-1">{stats.totalPatients}</p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </Card>

        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigateToPatients?.({ caseStatus: 'open', riskLevel: 'high' })}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Alto Riesgo</p>
              <p className="mt-1 text-red-600">{stats.highRisk}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </Card>

        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigateToPatients?.({ caseStatus: 'open', riskLevel: 'medium' })}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Riesgo Medio</p>
              <p className="mt-1 text-yellow-600">{stats.mediumRisk}</p>
            </div>
            <Activity className="w-8 h-8 text-yellow-600" />
          </div>
        </Card>

        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigateToPatients?.({ caseStatus: 'open', sortBy: 'deviation' })}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Desviaciones</p>
              <p className="mt-1">{stats.deviations}</p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Promedio Días</p>
              <p className="mt-1">{stats.averageStayDays.toFixed(1)}</p>
            </div>
            <Clock className="w-8 h-8 text-purple-600" />
          </div>
        </Card>
      </div>

      {/* Social Risk Statistics */}
      <div>
        <h3 className="text-lg font-medium mb-4">Indicadores de Riesgo Social</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card 
            className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [11, 20], caseStatus: 'open' })}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-muted-foreground">Riesgo Social Alto</p>
                <p className="mt-1 text-red-600">{stats.highSocialRisk}</p>
              </div>
              <Users className="w-8 h-8 text-red-600" />
            </div>
          </Card>

          <Card 
            className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [6, 10], caseStatus: 'open' })}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-muted-foreground">Riesgo Social Medio</p>
                <p className="mt-1 text-yellow-600">{stats.mediumSocialRisk}</p>
              </div>
              <Users className="w-8 h-8 text-yellow-600" />
            </div>
          </Card>

          <Card 
            className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [0, 5], caseStatus: 'open' })}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-muted-foreground">Riesgo Social Bajo</p>
                <p className="mt-1 text-green-600">{stats.lowSocialRisk}</p>
              </div>
              <Users className="w-8 h-8 text-green-600" />
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Urgent Patients */}
        <Card className="p-6">
          <h3 className="mb-4">Pacientes Urgentes</h3>
          <div className="space-y-3">
            {urgentPatients.length === 0 ? (
              <p className="text-muted-foreground">No hay pacientes de alto riesgo</p>
            ) : (
              urgentPatients.map(patient => (
                <div 
                  key={patient.id} 
                  className="flex items-center justify-between p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => onSelectPatient?.(patient)}
                >
                  <div>
                    <p>{patient.name}</p>
                    <p className="text-muted-foreground">{patient.service}</p>
                  </div>
                  <div className="text-right">
                    <RiskBadge level={patient.riskLevel} />
                    <p className="text-muted-foreground mt-1">
                      {patient.daysInStay} días
                      {patient.expectedDays !== null && (
                        <> ({patient.daysInStay - patient.expectedDays > 0 ? '+' : ''}{patient.daysInStay - patient.expectedDays})</>
                      )}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Pending Tasks */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-primary" />
              <h3>Tareas Pendientes</h3>
            </div>
            <Badge variant="secondary">{totalOpenTasks} abiertas</Badge>
          </div>
          <div className="space-y-3">
            {pendingTasks.length === 0 ? (
              <p className="text-muted-foreground">No hay tareas pendientes</p>
            ) : (
              pendingTasks.map(task => {
                const isOverdue = task.dueDate && new Date(task.dueDate) < new Date();
                return (
                  <div 
                    key={task.id} 
                    className="flex items-start gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <Circle className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{task.title}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <Badge 
                          variant="outline"
                          className={
                            task.priority === 'high' ? 'bg-red-50 text-red-700 border-red-200' :
                            task.priority === 'medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                            'bg-blue-50 text-blue-700 border-blue-200'
                          }
                        >
                          {task.priority === 'high' ? 'Alta' : task.priority === 'medium' ? 'Media' : 'Baja'}
                        </Badge>
                        {task.assignedTo && task.assignedTo !== 'Sin asignar' && (
                          <span className="text-xs text-muted-foreground">{task.assignedTo}</span>
                        )}
                        {task.dueDate && (
                          <span className={`text-xs flex items-center gap-1 ${isOverdue ? 'text-red-600' : 'text-muted-foreground'}`}>
                            <Calendar className="w-3 h-3" />
                            {new Date(task.dueDate).toLocaleDateString('es-ES')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </Card>
      </div>

      
    </div>
  );
}
