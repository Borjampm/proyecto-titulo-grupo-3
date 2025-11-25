import { useState, useEffect } from 'react';
import { Patient, RiskLevel, PatientFilters } from '../types';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { RiskBadge } from './RiskBadge';
import { Badge } from './ui/badge';
import { Search, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Label } from './ui/label';
import { getClinicalEpisodes, getClinicalServices } from '../lib/api-fastapi';

interface PatientListProps {
  onSelectPatient: (patient: Patient) => void;
  initialSortBy?: string;
  initialSocialScoreRange?: [number, number];
}

export function PatientList({ 
  onSelectPatient,
  initialSortBy = 'none',
  initialSocialScoreRange = [0, 20]
}: PatientListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterService, setFilterService] = useState<string>('all');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [filterCaseStatus, setFilterCaseStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>(initialSortBy);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [socialScoreRange, setSocialScoreRange] = useState<[number, number]>(initialSocialScoreRange);
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
      
      const response = await getClinicalEpisodes(filters);
      setPatients(response.data);
    } catch (error) {
      console.error('Error loading patients:', error);
    } finally {
      setLoading(false);
    }
  };

  // Apply sorting
  const sortedPatients = [...patients].sort((a, b) => {
    if (sortBy === 'social-score') {
      // Sort by social score descending (highest first), nulls last
      const scoreA = a.socialScore ?? -1;
      const scoreB = b.socialScore ?? -1;
      return scoreB - scoreA;
    }
    return 0; // No sorting
  });

  const filteredPatients = sortedPatients.filter(patient => {
    // Filter by social score range if customized
    if (socialScoreRange[0] === 0 && socialScoreRange[1] === 20) return true;
    
    const score = patient.socialScore;
    if (score === null || score === undefined) return false; // Exclude patients without score when filtering
    
    return score >= socialScoreRange[0] && score <= socialScoreRange[1];
  });

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
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
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

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger>
              <SelectValue placeholder="Ordenar por" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Sin ordenar</SelectItem>
              <SelectItem value="social-score">Puntaje Social</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="mt-4 border-t pt-4">
          <Button 
            variant="ghost" 
            className="flex items-center gap-2 text-sm text-muted-foreground p-0 h-auto hover:bg-transparent hover:text-foreground"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            Opciones avanzadas
          </Button>
          
          {showAdvanced && (
            <div className="mt-4 p-4 bg-muted/30 rounded-lg">
              <div className="max-w-md">
                <div className="flex justify-between mb-2">
                  <Label>Rango de Alerta Social</Label>
                  <span className="text-sm text-muted-foreground">
                    {socialScoreRange[0]} - {socialScoreRange[1]}
                  </span>
                </div>
                <Slider
                  defaultValue={[0, 20]}
                  value={[socialScoreRange[0], socialScoreRange[1]]}
                  max={20}
                  step={1}
                  onValueChange={(val) => setSocialScoreRange([val[0], val[1]])}
                  className="py-4"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Filtrar pacientes basado en su puntaje de riesgo social (0-20)
                </p>
              </div>
            </div>
          )}
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
              <TableHead>Alertas Sociales</TableHead>
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
                      {patient.socialScore !== null && patient.socialScore !== undefined ? (
                        <Badge 
                          variant="outline" 
                          className={
                            patient.socialScore > 10 
                              ? 'bg-red-50 text-red-700 border-red-300' 
                              : patient.socialScore >= 6 
                                ? 'bg-yellow-50 text-yellow-700 border-yellow-300'
                                : 'bg-green-50 text-green-700 border-green-300'
                          }
                        >
                          {patient.socialScore}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
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
