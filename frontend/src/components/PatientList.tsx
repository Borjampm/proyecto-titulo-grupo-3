import { useState, useEffect } from 'react';
import { Patient, RiskLevel, PatientFilters } from '../types';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { RiskBadge } from './RiskBadge';
import { Badge } from './ui/badge';
import { Search, Filter } from 'lucide-react';
import { Button } from './ui/button';
import { getPatients, getClinicalServices } from '../lib/api-fastapi';

interface PatientListProps {
  onSelectPatient: (patient: Patient) => void;
}

export function PatientList({ onSelectPatient }: PatientListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterService, setFilterService] = useState<string>('all');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [filterCaseStatus, setFilterCaseStatus] = useState<string>('all');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [services, setServices] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadServices();
  }, []);

  useEffect(() => {
    loadPatients();
  }, [searchTerm, filterService, filterRisk, filterCaseStatus]);

  const loadServices = async () => {
    try {
      const servicesData = await getClinicalServices();
      setServices(servicesData);
    } catch (error) {
      console.error('Error loading services:', error);
    }
  };

  const loadPatients = async () => {
    try {
      setLoading(true);
      const filters: PatientFilters = {};
      
      if (searchTerm) filters.search = searchTerm;
      if (filterService !== 'all') filters.service = filterService;
      if (filterRisk !== 'all') filters.riskLevel = filterRisk as any;
      if (filterCaseStatus !== 'all') filters.caseStatus = filterCaseStatus as any;
      
      const response = await getPatients(filters);
      setPatients(response.data);
    } catch (error) {
      console.error('Error loading patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients;

  return (
    <div className="space-y-6">
      <div>
        <h2>Gestión de Casos</h2>
        <p className="text-muted-foreground mt-1">
          Lista completa de pacientes en gestión de estadía
        </p>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nombre o diagnóstico..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          <Select value={filterCaseStatus} onValueChange={setFilterCaseStatus}>
            <SelectTrigger>
              <SelectValue placeholder="Estado del caso" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los casos</SelectItem>
              <SelectItem value="open">Casos Abiertos</SelectItem>
              <SelectItem value="closed">Casos Cerrados</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={filterService} onValueChange={setFilterService}>
            <SelectTrigger>
              <SelectValue placeholder="Todos los servicios" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los servicios</SelectItem>
              {services.map(service => (
                <SelectItem key={service} value={service}>{service}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterRisk} onValueChange={setFilterRisk}>
            <SelectTrigger>
              <SelectValue placeholder="Todos los riesgos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los riesgos</SelectItem>
              <SelectItem value="high">Alto Riesgo</SelectItem>
              <SelectItem value="medium">Riesgo Medio</SelectItem>
              <SelectItem value="low">Bajo Riesgo</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Card>

      {/* Patient Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Paciente</TableHead>
              <TableHead>Edad</TableHead>
              <TableHead>Servicio</TableHead>
              <TableHead>Diagnóstico</TableHead>
              <TableHead>Días Estadía</TableHead>
              <TableHead>Desvío</TableHead>
              <TableHead>Nivel Riesgo</TableHead>
              <TableHead>Estado Caso</TableHead>
              <TableHead>Alertas</TableHead>
              <TableHead>Acción</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center text-muted-foreground py-8">
                  Cargando pacientes...
                </TableCell>
              </TableRow>
            ) : filteredPatients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center text-muted-foreground py-8">
                  No se encontraron pacientes
                </TableCell>
              </TableRow>
            ) : (
              filteredPatients.map(patient => {
                const deviation = patient.daysInStay - patient.expectedDays;
                
                return (
                  <TableRow key={patient.id} className="cursor-pointer hover:bg-muted/50">
                    <TableCell>
                      <p>{patient.name}</p>
                      <p className="text-muted-foreground">{patient.grg}</p>
                    </TableCell>
                    <TableCell>{patient.age}</TableCell>
                    <TableCell>{patient.service}</TableCell>
                    <TableCell className="max-w-xs truncate">{patient.diagnosis}</TableCell>
                    <TableCell>
                      {patient.daysInStay} / {patient.expectedDays}
                    </TableCell>
                    <TableCell>
                      <span className={deviation > 0 ? 'text-red-600' : 'text-green-600'}>
                        {deviation > 0 ? '+' : ''}{deviation}
                      </span>
                    </TableCell>
                    <TableCell>
                      <RiskBadge level={patient.riskLevel} />
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant="outline" 
                        className={
                          patient.caseStatus === 'open' 
                            ? 'bg-green-50 text-green-700 border-green-300' 
                            : 'bg-gray-50 text-gray-700 border-gray-300'
                        }
                      >
                        {patient.caseStatus === 'open' ? 'Abierto' : 'Cerrado'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {patient.socialRisk && (
                          <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-300">
                            Social
                          </Badge>
                        )}
                        {patient.financialRisk && (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
                            Financiero
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => onSelectPatient(patient)}
                      >
                        Ver Detalle
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </Card>

      {!loading && (
        <div className="flex items-center justify-between text-muted-foreground">
          <p>
            Mostrando {filteredPatients.length} pacientes
          </p>
        </div>
      )}
    </div>
  );
}
