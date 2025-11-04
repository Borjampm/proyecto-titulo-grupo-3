/**
 * Header de la aplicación
 * 
 * Incluye navegación, notificaciones y menú de usuario con logout
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Bell, Menu, X, LogOut, User, Settings } from 'lucide-react';
import { toast } from 'sonner';

interface HeaderProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

const roleLabels: Record<string, string> = {
  coordinator: 'Coordinador de Estadía',
  'social-worker': 'Trabajador Social',
  analyst: 'Analista de Operaciones',
  chief: 'Jefe de Servicio',
  'clinical-service': 'Servicio Clínico',
};

export function Header({ sidebarOpen, onToggleSidebar }: HeaderProps) {
  const { user, logout } = useAuth();
  const [notificationCount] = useState(3); // Simulado - conectar con API real

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Sesión cerrada correctamente');
    } catch (error) {
      toast.error('Error al cerrar sesión');
    }
  };

  // Obtener iniciales del nombre
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const roleLabel = user?.role ? roleLabels[user.role] || user.role : '';

  return (
    <header className="bg-white border-b sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left side - Logo and title */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            className="lg:hidden"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
          <div>
            <h1>Sistema de Gestión de Estadía</h1>
            <p className="text-muted-foreground">UC CHRISTUS</p>
          </div>
        </div>

        {/* Right side - Notifications and user menu */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <Button variant="outline" size="icon" className="relative">
            <Bell className="w-5 h-5" />
            {notificationCount > 0 && (
              <Badge className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center p-0 bg-red-600">
                {notificationCount}
              </Badge>
            )}
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-3 px-3">
                <Avatar>
                  <AvatarFallback>{user ? getInitials(user.name) : 'U'}</AvatarFallback>
                </Avatar>
                <div className="text-left hidden sm:block">
                  <p>{user?.name || 'Usuario'}</p>
                  <p className="text-muted-foreground">{roleLabel}</p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Mi Cuenta</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 w-4 h-4" />
                Perfil
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 w-4 h-4" />
                Configuración
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                <LogOut className="mr-2 w-4 h-4" />
                Cerrar Sesión
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
