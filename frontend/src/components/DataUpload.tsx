import { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { importPatientsFromExcel } from '../lib/api-fastapi';
import { toast } from 'sonner';

export function DataUpload() {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [fileName, setFileName] = useState('');
  const [uploadResult, setUploadResult] = useState<{ imported: number; errors: string[] } | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setUploadStatus('loading');
      
      try {
        const result = await importPatientsFromExcel(file);
        setUploadResult({ imported: result.imported, errors: result.errors });
        setUploadStatus('success');
        toast.success(`${result.imported} pacientes importados exitosamente`);
        
        if (result.errors.length > 0) {
          result.errors.forEach(error => toast.error(error));
        }
        
        setTimeout(() => setUploadStatus('idle'), 5000);
      } catch (error) {
        console.error('Error uploading file:', error);
        setUploadStatus('error');
        toast.error('Error al importar el archivo');
        setTimeout(() => setUploadStatus('idle'), 3000);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2>Carga de Datos</h2>
        <p className="text-muted-foreground mt-1">
          Importar archivos Excel o CSV con información de pacientes
        </p>
      </div>

      {uploadStatus === 'success' && uploadResult && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Archivo "{fileName}" cargado exitosamente. {uploadResult.imported} registros procesados.
          </AlertDescription>
        </Alert>
      )}

      {uploadStatus === 'loading' && (
        <Alert className="border-blue-200 bg-blue-50">
          <AlertDescription className="text-blue-800">
            Procesando archivo "{fileName}"...
          </AlertDescription>
        </Alert>
      )}

      {uploadStatus === 'error' && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="w-4 h-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Error al procesar el archivo "{fileName}". Por favor, verifica el formato del archivo.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="mb-4">Cargar Archivo</h3>
          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <FileSpreadsheet className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">
              Arrastra un archivo Excel o CSV aquí
            </p>
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <Button 
              variant="outline" 
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              <Upload className="w-4 h-4 mr-2" />
              Seleccionar Archivo
            </Button>
          </div>
          <p className="text-muted-foreground mt-4">
            Formatos aceptados: .xlsx, .xls, .csv
          </p>
        </Card>

        <Card className="p-6">
          <h3 className="mb-4">Formato Esperado</h3>
          <p className="text-muted-foreground mb-4">
            El archivo debe contener las siguientes columnas:
          </p>
          <ul className="space-y-2 text-muted-foreground">
            <li>• Nombre del paciente</li>
            <li>• Edad</li>
            <li>• Fecha de ingreso</li>
            <li>• Servicio</li>
            <li>• Diagnóstico</li>
            <li>• GRD</li>
            <li>• Días esperados de estadía</li>
            <li>• Médico responsable</li>
          </ul>
          <Button variant="link" className="mt-4 p-0">
            Descargar plantilla de ejemplo
          </Button>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="mb-4">Historial de Cargas</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5 text-green-600" />
              <div>
                <p>pacientes_octubre_2025.xlsx</p>
                <p className="text-muted-foreground">23 de octubre, 2025 - 14:30</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-green-600">45 registros</p>
              <p className="text-muted-foreground">Procesado</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5 text-green-600" />
              <div>
                <p>base_pacientes_semana41.csv</p>
                <p className="text-muted-foreground">20 de octubre, 2025 - 09:15</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-green-600">38 registros</p>
              <p className="text-muted-foreground">Procesado</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5 text-green-600" />
              <div>
                <p>actualizacion_pacientes.xlsx</p>
                <p className="text-muted-foreground">18 de octubre, 2025 - 16:45</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-green-600">52 registros</p>
              <p className="text-muted-foreground">Procesado</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
