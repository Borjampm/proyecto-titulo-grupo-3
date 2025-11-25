"use client";

import { useState } from 'react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { LoginPage } from '../components/LoginPage';
import { LoadingScreen } from '../components/LoadingScreen';
import { Header } from '../components/Header';
import { Dashboard } from '../components/Dashboard';
import { PatientList } from '../components/PatientList';
import { PatientDetail } from '../components/PatientDetail';
import { ReferralForm } from '../components/ReferralForm';
import { DataUpload } from '../components/DataUpload';
import { Patient } from '../types';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Upload
} from 'lucide-react';
import { cn } from '../components/ui/utils';
import { Toaster } from '../components/ui/sonner';

// Importar el adaptador de FastAPI
import * as apiFastAPI from '../lib/api-fastapi';

type View = 'dashboard' | 'patients' | 'referral' | 'upload';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [patientListFilters, setPatientListFilters] = useState<{
    sortBy?: string;
    socialScoreRange?: [number, number];
  }>({});

  // Mostrar pantalla de carga mientras se verifica la autenticación
  if (isLoading) {
    return <LoadingScreen />;
  }

  // Si no está autenticado, mostrar página de login
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const navigation = [
    { id: 'dashboard' as View, name: 'Panel de Control', icon: LayoutDashboard },
    { id: 'patients' as View, name: 'Gestión de Casos', icon: Users },
    { id: 'referral' as View, name: 'Derivar Paciente', icon: FileText },
    { id: 'upload' as View, name: 'Carga de Datos', icon: Upload },
  ];

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
  };

  const handleBackToList = () => {
    setSelectedPatient(null);
  };

  const handleNavigateToPatients = (filters: { sortBy: string; socialScoreRange: [number, number] }) => {
    setPatientListFilters(filters);
    setCurrentView('patients');
  };

  const renderContent = () => {
    if (selectedPatient) {
      return <PatientDetail patient={selectedPatient} onBack={handleBackToList} />;
    }

    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigateToPatients={handleNavigateToPatients} />;
      case 'patients':
        return (
          <PatientList 
            onSelectPatient={handleSelectPatient} 
            initialSortBy={patientListFilters.sortBy}
            initialSocialScoreRange={patientListFilters.socialScoreRange}
            key={JSON.stringify(patientListFilters)}
          />
        );
      case 'referral':
        return <ReferralForm />;
      case 'upload':
        return <DataUpload />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <Header sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={cn(
            'bg-white border-r h-[calc(100vh-73px)] sticky top-[73px] transition-all duration-300',
            sidebarOpen ? 'w-64' : 'w-0 lg:w-64',
            'lg:block',
            !sidebarOpen && 'hidden'
          )}
        >
          <nav className="p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id && !selectedPatient;
              
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentView(item.id);
                    setSelectedPatient(null);
                    setSidebarOpen(false);
                    if (item.id === 'patients') {
                      setPatientListFilters({});
                    }
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted text-foreground'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8 max-w-[1600px] mx-auto w-full">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
    </AuthProvider>
  );
}
