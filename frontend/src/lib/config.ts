/**
 * Configuración de la aplicación
 * 
 * INSTRUCCIONES PARA CONECTAR TU BACKEND:
 * 1. Cambia BACKEND_URL por la URL de tu API deployada
 * 2. Si tu API requiere autenticación por token, el sistema lo manejará automáticamente
 * 3. Para desarrollo local, usa: http://localhost:3000/api (o el puerto que uses)
 */

export const config = {
  // URL base de tu backend API FastAPI
  BACKEND_URL: 'https://proyecto-titulo-grupo-3.onrender.com',
  
  // Tiempo de timeout para las peticiones (en milisegundos)
  REQUEST_TIMEOUT: 30000,
  
  // Habilitar modo de desarrollo (usa datos mock si el backend no está disponible)
  USE_MOCK_DATA: true, // ✅ Usando backend FastAPI real
  
  // Usar autenticación mock (hasta que se implemente en el backend)
  USE_MOCK_AUTH: true, // ✅ Autenticación mock temporal
  
  // Tamaño máximo de archivos (en bytes) - 10MB
  MAX_FILE_SIZE: 10 * 1024 * 1024,
  
  // Formatos de archivo permitidos para documentos
  ALLOWED_DOCUMENT_TYPES: [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv'
  ],
};

export default config;
