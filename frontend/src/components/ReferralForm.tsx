import { useState, useEffect, useMemo } from 'react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Send, CheckCircle, UserPlus, Search } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { CreatePatientDialog } from './CreatePatientDialog';
import { getAllPatients, createReferral } from '../lib/api-fastapi';
import { PatientOption } from '../types';

const services = [
  'Medicina Interna',
  'Cirugía',
  'Cardiología',
  'Traumatología',
  'Geriatría',
  'Neurología',
  'Pediatría',
  'Ginecología'
];

export function ReferralForm() {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patientDialogOpen, setPatientDialogOpen] = useState(false);
  const [allPatients, setAllPatients] = useState<PatientOption[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(null);
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);
  
  const [formData, setFormData] = useState({
    service: '',
    diagnosis: '',
    expectedDays: '',
    socialFactors: '',
    clinicalNotes: '',
    submittedBy: ''
  });

  useEffect(() => {
    loadPatients();
  }, []);

  const calculateAge = (birthDate: string): number => {
    const birth = new Date(birthDate);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  };

  const loadPatients = async () => {
    try {
      const response = await getAllPatients();
      const patientOptions: PatientOption[] = response.map((p: any) => ({
        id: p.id,
        name: `${p.first_name} ${p.last_name}`,
        rut: p.rut,
        age: calculateAge(p.birth_date),
      }));
      setAllPatients(patientOptions);
    } catch (err) {
      console.error('Error loading patients:', err);
    }
  };

  const filteredPatients = useMemo(() => {
    if (searchTerm.length < 2) {
      return [];
    }
    
    const search = searchTerm.toLowerCase();
    return allPatients.filter(p => 
      p.name.toLowerCase().includes(search) ||
      p.rut?.toLowerCase().includes(search)
    );
  }, [searchTerm, allPatients]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPatient) {
      setError('Debe seleccionar un paciente');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createReferral({
        patientId: selectedPatient.id,
        service: formData.service,
        diagnosis: formData.diagnosis,
        expectedDays: parseInt(formData.expectedDays),
        socialFactors: formData.socialFactors,
        clinicalNotes: formData.clinicalNotes,
        submittedBy: formData.submittedBy,
      });

      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setSelectedPatient(null);
        setFormData({
          service: '',
          diagnosis: '',
          expectedDays: '',
          socialFactors: '',
          clinicalNotes: '',
          submittedBy: ''
        });
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear la derivación');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePatientCreated = (patient: PatientOption) => {
    setSelectedPatient(patient);
    setAllPatients(prev => [patient, ...prev]);
  };

  const handlePatientSearch = (value: string) => {
    setSearchTerm(value);
    setShowPatientDropdown(true);
  };

  const handlePatientSelect = (patient: PatientOption) => {
    setSelectedPatient(patient);
    setShowPatientDropdown(false);
    setSearchTerm('');
  };

  if (submitted) {
    return (
      <div className="space-y-6">
        <h2>Derivación de Paciente</h2>
        <Card className="p-12">
          <div className="text-center">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h3 className="mb-2">Derivación Enviada Exitosamente</h3>
            <p className="text-muted-foreground mb-6">
              El paciente ha sido derivado al área de Gestión de Estadía
            </p>
            <Button onClick={() => setSubmitted(false)}>
              Enviar Otra Derivación
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2>Derivación de Paciente</h2>
        <p className="text-muted-foreground mt-1">
          Formulario para enviar pacientes al área de Gestión de Estadía
        </p>
      </div>

      <Alert>
        <AlertDescription>
          Complete todos los campos requeridos. La información será revisada por el equipo de gestión de estadía.
        </AlertDescription>
      </Alert>

      <form onSubmit={handleSubmit}>
        <Card className="p-6">
          <div className="space-y-6">
            <div>
              <h3>Selección de Paciente</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Busque un paciente existente o cree uno nuevo
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="patient">Paciente *</Label>
              {selectedPatient ? (
                <div className="flex items-center gap-2">
                  <div className="flex-1 p-3 border rounded-md bg-muted">
                    <p className="font-medium">{selectedPatient.name}</p>
                    {selectedPatient.rut && (
                      <p className="text-sm text-muted-foreground">RUT: {selectedPatient.rut}</p>
                    )}
                    <p className="text-sm text-muted-foreground">Edad: {selectedPatient.age} años</p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setSelectedPatient(null)}
                  >
                    Cambiar
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="patient"
                      value={searchTerm}
                      onChange={(e) => handlePatientSearch(e.target.value)}
                      onFocus={() => setShowPatientDropdown(true)}
                      placeholder="Buscar por nombre o RUT..."
                      className="pl-9"
                    />
                    {showPatientDropdown && filteredPatients.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
                        {filteredPatients.map((patient) => (
                          <button
                            key={patient.id}
                            type="button"
                            className="w-full text-left px-4 py-2 hover:bg-muted"
                            onClick={() => handlePatientSelect(patient)}
                          >
                            <p className="font-medium">{patient.name}</p>
                            {patient.rut && (
                              <p className="text-sm text-muted-foreground">RUT: {patient.rut}</p>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setPatientDialogOpen(true)}
                    className="w-full"
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Crear Nuevo Paciente
                  </Button>
                </div>
              )}
            </div>

            <div className="border-t pt-6">
              <h3>Información de la Derivación</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="service">Servicio Derivante *</Label>
                <Select value={formData.service} onValueChange={(value) => handleChange('service', value)} required>
                  <SelectTrigger id="service">
                    <SelectValue placeholder="Seleccione un servicio" />
                  </SelectTrigger>
                  <SelectContent>
                    {services.map(service => (
                      <SelectItem key={service} value={service}>{service}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="expectedDays">Días Esperados de Estadía *</Label>
                <Input
                  id="expectedDays"
                  type="number"
                  value={formData.expectedDays}
                  onChange={(e) => handleChange('expectedDays', e.target.value)}
                  required
                  placeholder="Ej: 5"
                  min="1"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="diagnosis">Diagnóstico Principal *</Label>
              <Input
                id="diagnosis"
                value={formData.diagnosis}
                onChange={(e) => handleChange('diagnosis', e.target.value)}
                required
                placeholder="Ej: Neumonía comunitaria"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="clinicalNotes">Notas Clínicas</Label>
              <Textarea
                id="clinicalNotes"
                value={formData.clinicalNotes}
                onChange={(e) => handleChange('clinicalNotes', e.target.value)}
                rows={4}
                placeholder="Resumen clínico, tratamiento actual, pronóstico..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="socialFactors">Factores Sociales Detectados</Label>
              <Textarea
                id="socialFactors"
                value={formData.socialFactors}
                onChange={(e) => handleChange('socialFactors', e.target.value)}
                rows={4}
                placeholder="Situación familiar, red de apoyo, condiciones de vivienda, dificultades para alta..."
              />
              <p className="text-sm text-muted-foreground">
                Indique si el paciente vive solo, tiene dificultades de movilidad, falta de red de apoyo, etc.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="submittedBy">Derivado por (nombre del profesional) *</Label>
              <Input
                id="submittedBy"
                value={formData.submittedBy}
                onChange={(e) => handleChange('submittedBy', e.target.value)}
                required
                placeholder="Ej: Dr. Juan Pérez"
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setSelectedPatient(null);
                  setFormData({
                    service: '',
                    diagnosis: '',
                    expectedDays: '',
                    socialFactors: '',
                    clinicalNotes: '',
                    submittedBy: ''
                  });
                }}
                disabled={loading}
              >
                Limpiar Formulario
              </Button>
              <Button type="submit" disabled={loading || !selectedPatient}>
                <Send className="w-4 h-4 mr-2" />
                {loading ? 'Enviando...' : 'Enviar Derivación'}
              </Button>
            </div>
          </div>
        </Card>
      </form>

      <CreatePatientDialog
        open={patientDialogOpen}
        onOpenChange={setPatientDialogOpen}
        onPatientCreated={handlePatientCreated}
      />
    </div>
  );
}
