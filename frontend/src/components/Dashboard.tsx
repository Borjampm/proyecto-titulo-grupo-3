import { useEffect, useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { Users, AlertTriangle, TrendingUp, Clock, Activity, ClipboardList, Circle, Calendar } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { getDashboardStats, getClinicalEpisodes, getAllTasks, getAllAlerts, getClinicalEpisode } from '../lib/api-fastapi';
import { DashboardStats, Patient, Task, Alert } from '../types';

interface DashboardProps {
  onNavigateToPatients?: (filters: { sortBy?: string; socialScoreRange?: [number, number]; caseStatus?: string; riskLevel?: string }) => void;
  onSelectPatient?: (patient: Patient) => void;
}

export function Dashboard({ onNavigateToPatients, onSelectPatient }: DashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingTasks, setPendingTasks] = useState<Task[]>([]);
  const [totalOpenTasks, setTotalOpenTasks] = useState(0);
  const [urgentPatients, setUrgentPatients] = useState<Patient[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, urgentPatientsData, tasksData, alertsData] = await Promise.all([
        getDashboardStats(),
        getClinicalEpisodes({ 
          caseStatus: 'open',
          sortByOverstayProbability: true,
          pageSize: 5 
        }),
        getAllTasks({ openOnly: true, orderByDueDate: true }),
        getAllAlerts(),
      ]);
      
      setStats(statsData);
      setActiveAlerts(alertsData);
      // Filter to only open cases and limit to 5
      const openUrgentPatients = urgentPatientsData.data
        .filter(p => p.caseStatus === 'open')
        .slice(0, 5);
      setUrgentPatients(openUrgentPatients);
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

  const handleAlertClick = async (alert: Alert) => {
    try {
      const episode = await getClinicalEpisode(alert.patientId);
      onSelectPatient?.(episode);
    } catch (error) {
      console.error('Error loading episode for alert:', error);
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
        <Tooltip>
          <TooltipTrigger asChild>
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
          </TooltipTrigger>
          <TooltipContent>
            <p className="leading-relaxed">
              Cantidad de casos que están abiertos según los coordinadores de estadía.
              <br />
              Se puede cambiar su estado en la sección de Gestión de Casos.
            </p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Card 
              className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => onNavigateToPatients?.({ caseStatus: 'open', riskLevel: 'high' })}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground leading-tight">Alto riesgo de prolongar su estadía</p>
                  <p className="mt-1 text-red-600">{stats.highRisk}</p>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </Card>
          </TooltipTrigger>
          <TooltipContent>
            <p className="leading-relaxed">
              Cantidad de casos en los que el modelo predictivo dió que hay un 75% de probabilidad o más
              <br />
              de que alarguen su estadía.
            </p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Card 
              className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => onNavigateToPatients?.({ caseStatus: 'open', riskLevel: 'medium' })}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground leading-tight">Riesgo medio de prolongar su estadía</p>
                  <p className="mt-1 text-yellow-600">{stats.mediumRisk}</p>
                </div>
                <Activity className="w-8 h-8 text-yellow-600" />
              </div>
            </Card>
          </TooltipTrigger>
          <TooltipContent>
            <p className="leading-relaxed">
              Cantidad de casos en los que el modelo predictivo dió que hay un 50% de probabilidad o más
              <br />
              de que alarguen su estadía.
            </p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
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
          </TooltipTrigger>
          <TooltipContent>
            <p className="leading-relaxed">
              Cantidad de casos en los que ya se desvío la estadía por sobre lo previsto.
            </p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground">Promedio Días</p>
                  <p className="mt-1">{stats.averageStayDays.toFixed(1)}</p>
                </div>
                <Clock className="w-8 h-8 text-purple-600" />
              </div>
            </Card>
          </TooltipTrigger>
          <TooltipContent>
            <p className="leading-relaxed">
              Cantidad promedio de días de estadía.
            </p>
          </TooltipContent>
        </Tooltip>
      </div>

      {/* Social Risk Statistics */}
      <div>
        <h3 className="text-lg font-medium mb-4">Indicadores de Riesgo Social</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Tooltip>
            <TooltipTrigger asChild>
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
            </TooltipTrigger>
            <TooltipContent>
              <p className="leading-relaxed">
                Cantidad de casos en los que el Score Social arrojó que son de alto riesgo.
              </p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
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
            </TooltipTrigger>
            <TooltipContent>
              <p className="leading-relaxed">
                Cantidad de casos en los que el Score Social arrojó que son de riesgo medio.
              </p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
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
            </TooltipTrigger>
            <TooltipContent>
              <p className="leading-relaxed">
                Cantidad de casos en los que el Score Social arrojó que son de riesgo bajo.
              </p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Urgent Patients */}
        <Card className="p-6">
          <div className="mb-4">
            <h3 className="mb-2">Pacientes Urgentes</h3>
            <p className="text-sm text-muted-foreground">
              Los 5 pacientes con mayor probabilidad de prolongar su estadía según el modelo predictivo
            </p>
          </div>
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
                    <p className="text-xs text-muted-foreground mt-1">
                      {patient.overstayProbability !== null && patient.overstayProbability !== undefined ? (
                        <>Probabilidad: {(patient.overstayProbability * 100).toFixed(1)}%</>
                      ) : (
                        <>Probabilidad: No calculada</>
                      )}
                    </p>
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
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-5 h-5 text-primary" />
                <h3>Tareas Pendientes</h3>
              </div>
              <Badge variant="secondary">{totalOpenTasks} abiertas</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Las 5 tareas con fecha límite más cercana a hoy
            </p>
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

      {/* Active Alerts - Full Width */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h3>Alertas Activas</h3>
          </div>
          <Badge variant="secondary">{activeAlerts.length} alertas</Badge>
        </div>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {activeAlerts.length === 0 ? (
            <p className="text-muted-foreground">No hay alertas activas</p>
          ) : (
            activeAlerts.map(alert => (
              <div 
                key={alert.id} 
                className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => handleAlertClick(alert)}
              >
                <AlertTriangle className={`w-5 h-5 mt-0.5 shrink-0 ${
                  alert.severity === 'high' ? 'text-red-600' :
                  alert.severity === 'medium' ? 'text-yellow-600' :
                  'text-blue-600'
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge 
                      variant="outline"
                      className={
                        alert.type === 'stay-deviation' 
                          ? 'bg-orange-50 text-orange-700 border-orange-300'
                          : alert.type === 'predicted-overstay'
                            ? 'bg-blue-50 text-blue-700 border-blue-300'
                            : 'bg-purple-50 text-purple-700 border-purple-300'
                      }
                    >
                      {alert.type === 'stay-deviation' ? 'Desviación de Estadía' : 
                       alert.type === 'predicted-overstay' ? 'Predicción de Sobrestadía' :
                       'Riesgo Social'}
                    </Badge>
                    <Badge 
                      variant="outline"
                      className={
                        alert.severity === 'high' ? 'bg-red-50 text-red-700 border-red-200' :
                        alert.severity === 'medium' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                        'bg-blue-50 text-blue-700 border-blue-200'
                      }
                    >
                      {alert.severity === 'high' ? 'Alta' : alert.severity === 'medium' ? 'Media' : 'Baja'}
                    </Badge>
                  </div>
                  <p className="font-medium text-sm">{alert.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs font-semibold text-gray-700">
                      {alert.patientName || 'Paciente desconocido'}
                    </p>
                    <span className="text-xs text-muted-foreground">•</span>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.createdAt).toLocaleString('es-ES')}
                    </p>
                    {alert.createdBy && (
                      <>
                        <span className="text-xs text-muted-foreground">•</span>
                        <p className="text-xs text-muted-foreground">{alert.createdBy}</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      
    </div>
  );
}
