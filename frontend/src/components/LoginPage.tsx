/**
 * Página de Login
 * 
 * Formulario de inicio de sesión para el sistema
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      toast.success('Sesión iniciada correctamente');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al iniciar sesión';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#F0F4F8' }}>
      <Card className="w-full max-w-md shadow-lg bg-white border-0">
        <CardHeader className="space-y-1 pb-4">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-black text-white p-3 rounded-full w-14 h-14 flex items-center justify-center">
              <span className="text-2xl font-bold">N</span>
            </div>
          </div>
          <CardTitle className="text-center font-bold text-black text-xl leading-tight">Gestión de Estadía Hospitalaria</CardTitle>
          <CardDescription className="text-center text-gray-600 mt-2">
            Ingrese sus credenciales para acceder al sistema
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-black font-normal text-sm">Correo Electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="usuario@hospital.cl"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="email"
                className="bg-gray-50 border-gray-300 text-gray-900 placeholder:text-gray-500"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-black font-normal text-sm">Contraseña</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="current-password"
                  className="pr-10 bg-gray-50 border-gray-300 text-gray-900 placeholder:text-gray-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button 
              type="submit" 
              className="w-full bg-black text-white hover:bg-gray-800 font-bold h-10" 
              disabled={isLoading}
              style={{ backgroundColor: '#000000' }}
            >
              {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>
          </form>

          {/* Información de demo - Remover en producción */}
          <div className="mt-6 p-4 rounded-lg" style={{ backgroundColor: '#F8F8F8' }}>
            <p className="text-sm font-bold mb-2 text-black">Usuarios de Demostración:</p>
            <div className="space-y-1 text-xs text-black font-normal">
              <p>• coordinador@hospital.cl - Coordinador de Estadía</p>
              <p>• social@hospital.cl - Trabajador Social</p>
              <p>• analista@hospital.cl - Analista de Operaciones</p>
              <p>• jefe@hospital.cl - Jefe de Servicio</p>
              <p>• doctor@hospital.cl - Servicio Clínico</p>
              <p className="mt-2 italic">Contraseña: cualquier valor (modo demo)</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
