import { useEffect, useState } from 'react';
import { Card } from './ui/card';
import { Users, AlertTriangle, TrendingUp, Clock, Activity } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { Alert, AlertDescription } from './ui/alert';
import { getDashboardStats, getAllAlerts, getClinicalEpisodes } from '../lib/api-fastapi';
import { DashboardStats, Alert as AlertType, Patient } from '../types';

interface DashboardProps {
  onNavigateToPatients?: (filters: { sortBy: string; socialScoreRange: [number, number] }) => void;
}

export function Dashboard({ onNavigateToPatients }: DashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<AlertType[]>([]);
  const [urgentPatients, setUrgentPatients] = useState<Patient[]>([]);
  const [allPatients, setAllPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, alertsData, urgentPatientsData, allPatientsData] = await Promise.all([
        getDashboardStats(),
        getAllAlerts(),
        getClinicalEpisodes({ riskLevel: 'high', pageSize: 5 }),
        getClinicalEpisodes({ pageSize: 100 }),
      ]);
      
      setStats(statsData);
      setRecentAlerts(alertsData.slice(0, 5));
      setUrgentPatients(urgentPatientsData.data);
      setAllPatients(allPatientsData.data);
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
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Total Casos</p>
              <p className="mt-1">{stats.totalPatients}</p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Alto Riesgo</p>
              <p className="mt-1 text-red-600">{stats.highRisk}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-muted-foreground">Riesgo Medio</p>
              <p className="mt-1 text-yellow-600">{stats.mediumRisk}</p>
            </div>
            <Activity className="w-8 h-8 text-yellow-600" />
          </div>
        </Card>

        <Card className="p-4">
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
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [11, 20] })}
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
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [5, 10] })}
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
            onClick={() => onNavigateToPatients?.({ sortBy: 'social-score', socialScoreRange: [0, 4] })}
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
                <div key={patient.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p>{patient.name}</p>
                    <p className="text-muted-foreground">{patient.service}</p>
                  </div>
                  <div className="text-right">
                    <RiskBadge level={patient.riskLevel} />
                    <p className="text-muted-foreground mt-1">
                      {patient.daysInStay} días ({patient.daysInStay - patient.expectedDays > 0 ? '+' : ''}{patient.daysInStay - patient.expectedDays})
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recent Alerts */}
        <Card className="p-6">
          <h3 className="mb-4">Alertas Recientes</h3>
          <div className="space-y-3">
            {recentAlerts.length === 0 ? (
              <p className="text-muted-foreground">No hay alertas recientes</p>
            ) : (
              recentAlerts.map(alert => {
                const patient = allPatients.find(p => p.id === alert.patientId);
                const alertConfig = {
                  'stay-deviation': { icon: TrendingUp, color: 'text-orange-600' },
                  'social-risk': { icon: Users, color: 'text-red-600' },
                  'financial-risk': { icon: AlertTriangle, color: 'text-yellow-600' }
                };
                const config = alertConfig[alert.type];
                const Icon = config.icon;

                return (
                  <Alert key={alert.id} className="border-l-4" style={{ borderLeftColor: alert.severity === 'high' ? '#dc2626' : '#eab308' }}>
                    <Icon className={`w-4 h-4 ${config.color}`} />
                    <AlertDescription>
                      <p>{patient?.name}</p>
                      <p className="text-muted-foreground">{alert.message}</p>
                    </AlertDescription>
                  </Alert>
                );
              })
            )}
          </div>
        </Card>
      </div>

      {/* Distribution by Service */}
      <Card className="p-6">
        <h3 className="mb-4">Distribución por Servicio</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from(new Set(allPatients.map(p => p.service))).map(service => {
            const count = allPatients.filter(p => p.service === service).length;
            const highRiskCount = allPatients.filter(p => p.service === service && p.riskLevel === 'high').length;
            
            return (
              <div key={service} className="border rounded-lg p-4">
                <p className="text-muted-foreground">{service}</p>
                <p className="mt-2">{count} pacientes</p>
                {highRiskCount > 0 && (
                  <p className="text-red-600 mt-1">{highRiskCount} alto riesgo</p>
                )}
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
