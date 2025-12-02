import { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { importSocialScoresFromExcel, importBedsFromExcel, importGestionEstadiaFromExcel, importGrdFromExcel, importGrdNormsFromExcel } from '../lib/api-fastapi';
import { toast } from 'sonner';

type ExcelFileType = 'score_social' | 'beds' | 'gestion_estadia' | 'grd' | 'grd_norms';

export function DataUpload() {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [fileName, setFileName] = useState('');
  const [uploadResult, setUploadResult] = useState<{ 
    imported: number; 
    errors: string[]; 
    missingCount?: number; 
    missingIds?: string[];
    debugDbIds?: string[];
    debugFileIds?: string[];
  } | null>(null);
  const [fileType, setFileType] = useState<ExcelFileType>('score_social');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setUploadStatus('loading');
      
      try {
        // Use different endpoint based on file type
        let result;
        let successMessage: string;
        
        switch (fileType) {
          case 'score_social':
            result = await importSocialScoresFromExcel(file);
            successMessage = `${result.imported} registros de score social importados exitosamente`;
            break;
          case 'beds':
            result = await importBedsFromExcel(file);
            successMessage = `${result.imported} camas importadas exitosamente`;
            break;
          case 'gestion_estadia':
            result = await importGestionEstadiaFromExcel(file);
            successMessage = `${result.imported} registros de gestión estadía importados exitosamente`;
            break;
          case 'grd':
            result = await importGrdFromExcel(file);
            successMessage = `${result.imported} episodios actualizados con datos GRD`;
            break;
          case 'grd_norms':
            result = await importGrdNormsFromExcel(file);
            successMessage = `${result.imported} normas GRD procesadas (${(result as any).created} creadas, ${(result as any).updated} actualizadas)`;
            break;
        }
        
        setUploadResult({ 
          imported: result.imported, 
          errors: result.errors,
          missingCount: result.missingCount,
          missingIds: result.missingIds,
          debugDbIds: (result as any).debugDbIds,
          debugFileIds: (result as any).debugFileIds,
        });
        setUploadStatus('success');
        toast.success(successMessage);
        
        if (result.missingCount && result.missingCount > 0) {
          toast.warning(`${result.missingCount} registros no se pudieron asociar a episodios existentes`);
        }
        
        if (result.errors.length > 0) {
          result.errors.forEach(error => toast.error(error));
        }
        
        setTimeout(() => setUploadStatus('idle'), 10000);
      } catch (error) {
        console.error('Error uploading file:', error);
        setUploadResult(null);
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
          Importar archivos Excel con información del hospital
        </p>
      </div>

      {uploadStatus === 'success' && uploadResult && (
        <div className="space-y-4">
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Archivo &quot;{fileName}&quot; cargado exitosamente. {uploadResult.imported} registros procesados.
            </AlertDescription>
          </Alert>
          
          {uploadResult.missingCount !== undefined && uploadResult.missingCount > 0 && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertCircle className="w-4 h-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                <p className="font-medium mb-1">
                  Advertencia: {uploadResult.missingCount} registros no se pudieron asociar a ningún episodio existente.
                </p>
                <p className="text-sm mb-2">
                  Estos registros fueron ignorados porque el identificador de episodio no coincide con ningún paciente en el sistema.
                </p>
                {uploadResult.missingIds && uploadResult.missingIds.length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-sm font-medium hover:underline">
                      Ver IDs no encontrados ({uploadResult.missingIds.length})
                    </summary>
                    <div className="mt-2 text-xs bg-yellow-100 p-2 rounded max-h-32 overflow-y-auto">
                      {uploadResult.missingIds.map((id, index) => (
                        <span key={id}>
                          {id}{index < uploadResult.missingIds!.length - 1 ? ', ' : ''}
                        </span>
                      ))}
                    </div>
                  </details>
                )}
                {(uploadResult.debugDbIds || uploadResult.debugFileIds) && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-sm font-medium hover:underline">
                      Ver información de debug
                    </summary>
                    <div className="mt-2 text-xs bg-yellow-100 p-2 rounded space-y-2">
                      {uploadResult.debugDbIds && uploadResult.debugDbIds.length > 0 && (
                        <div>
                          <strong>IDs en la base de datos (muestra):</strong>
                          <div className="font-mono">{uploadResult.debugDbIds.join(', ')}</div>
                        </div>
                      )}
                      {uploadResult.debugFileIds && uploadResult.debugFileIds.length > 0 && (
                        <div>
                          <strong>IDs en el archivo Excel (muestra):</strong>
                          <div className="font-mono">{uploadResult.debugFileIds.join(', ')}</div>
                        </div>
                      )}
                    </div>
                  </details>
                )}
              </AlertDescription>
            </Alert>
          )}
        </div>
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
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Tipo de archivo</label>
            <Select value={fileType} onValueChange={(value: ExcelFileType) => setFileType(value)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecciona el tipo de archivo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="score_social">Score Social</SelectItem>
                <SelectItem value="beds">Camas</SelectItem>
                <SelectItem value="gestion_estadia">Gestión Estadía</SelectItem>
                <SelectItem value="grd">GRD (Días Esperados)</SelectItem>
                <SelectItem value="grd_norms">Normas GRD (normas_eeuu)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <FileSpreadsheet className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground mb-4">
              {fileType === 'grd_norms' ? 'Arrastra un archivo Excel o CSV aquí' : 'Arrastra un archivo Excel aquí'}
            </p>
            <input
              type="file"
              accept={fileType === 'grd_norms' ? '.xlsx,.xls,.xlsm,.csv' : '.xlsx,.xls,.xlsm'}
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
            Formatos aceptados: {fileType === 'grd_norms' ? '.xlsx, .xls, .xlsm, .csv' : '.xlsx, .xls, .xlsm'}
          </p>
        </Card>

        <Card className="p-6">
          <h3 className="mb-4">Formato Esperado</h3>
          {fileType === 'score_social' && (
            <>
              <p className="text-muted-foreground mb-4">
                El archivo debe contener una hoja &quot;Data Casos&quot; con las siguientes columnas:
              </p>
              <ul className="space-y-2 text-muted-foreground">
                <li>• <strong>Episodio / Estadía</strong> - Identificador del episodio</li>
                <li>• <strong>Puntaje</strong> - Score social (puede ser vacío)</li>
                <li>• <strong>Fecha Asignación</strong> - Fecha de registro</li>
                <li>• <strong>Encuestadora</strong> - Persona que registró</li>
                <li>• <strong>Motivo</strong> - Razón si no hay puntaje</li>
              </ul>
              <p className="text-muted-foreground mt-4 text-sm">
                Los registros sin puntaje se mostrarán como N/A con su motivo correspondiente.
              </p>
            </>
          )}
          {fileType === 'beds' && (
            <>
              <p className="text-muted-foreground mb-4">
                El archivo debe contener una hoja &quot;Camas&quot; con información de camas hospitalarias.
              </p>
              <ul className="space-y-2 text-muted-foreground">
                <li>• Información de camas del hospital</li>
                <li>• Ubicación y servicio asociado</li>
                <li>• Estado de disponibilidad</li>
              </ul>
              <p className="text-muted-foreground mt-4 text-sm">
                Archivo esperado: &quot;Camas NWP1&quot; con hoja &quot;Camas&quot;.
              </p>
            </>
          )}
          {fileType === 'gestion_estadia' && (
            <>
              <p className="text-muted-foreground mb-4">
                El archivo debe contener una hoja &quot;UCCC&quot; con datos de pacientes y episodios.
              </p>
              <ul className="space-y-2 text-muted-foreground">
                <li>• Datos de pacientes</li>
                <li>• Información de episodios clínicos</li>
                <li>• Registros de estadía hospitalaria</li>
              </ul>
              <p className="text-muted-foreground mt-4 text-sm">
                Formatos aceptados: .xlsx, .xls, .xlsm
              </p>
            </>
          )}
          {fileType === 'grd' && (
            <>
              <p className="text-muted-foreground mb-4">
                El archivo &quot;resultado prediccion&quot; debe contener las siguientes columnas:
              </p>
              <ul className="space-y-2 text-muted-foreground">
                <li>• <strong>Episodio</strong> - Identificador del episodio</li>
                <li>• <strong>IR GRD CODE</strong> - Código GRD con formato: &quot;ID - Nombre&quot;</li>
              </ul>
              <p className="text-muted-foreground mt-4 text-sm">
                Ejemplo de IR GRD CODE: &quot;51013 - PH TRASPLANTE CARDÍACO Y/O PULMONAR W/MCC&quot;
              </p>
              <p className="text-muted-foreground mt-2 text-sm">
                El sistema extraerá el ID del GRD, buscará los días esperados en las normas GRD y actualizará los episodios.
              </p>
            </>
          )}
          {fileType === 'grd_norms' && (
            <>
              <p className="text-muted-foreground mb-4">
                El archivo debe contener las normas GRD (normas_eeuu) con las siguientes columnas:
              </p>
              <ul className="space-y-2 text-muted-foreground">
                <li>• <strong>GRD</strong> - Código identificador del GRD</li>
                <li>• <strong>Est Media</strong> - Días esperados de estadía (estancia media)</li>
              </ul>
              <p className="text-muted-foreground mt-4 text-sm">
                Este archivo carga las normas de referencia que definen cuántos días debería durar la estadía para cada GRD según estándares de EE.UU.
              </p>
              <p className="text-muted-foreground mt-2 text-sm font-medium">
                Formatos aceptados: Excel (.xlsx, .xls, .xlsm) o CSV (.csv)
              </p>
            </>
          )}
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
