/**
 * Pantalla de carga
 * 
 * Se muestra mientras se verifica la autenticación
 */

import { Activity } from 'lucide-react';

export function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center">
        <div className="inline-flex items-center justify-center mb-4">
          <div className="bg-primary text-primary-foreground p-4 rounded-full animate-pulse">
            <Activity className="w-12 h-12" />
          </div>
        </div>
        <h2 className="text-xl font-semibold mb-2">Cargando...</h2>
        <p className="text-muted-foreground">Verificando autenticación</p>
      </div>
    </div>
  );
}
