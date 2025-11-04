import { useState } from 'react';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Send, CheckCircle } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';

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
  const [formData, setFormData] = useState({
    patientName: '',
    age: '',
    service: '',
    diagnosis: '',
    admissionDate: '',
    expectedDays: '',
    socialFactors: '',
    clinicalNotes: '',
    submittedBy: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would send to backend
    console.log('Form submitted:', formData);
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      setFormData({
        patientName: '',
        age: '',
        service: '',
        diagnosis: '',
        admissionDate: '',
        expectedDays: '',
        socialFactors: '',
        clinicalNotes: '',
        submittedBy: ''
      });
    }, 3000);
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
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
            <h3>Información del Paciente</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="patientName">Nombre Completo del Paciente *</Label>
                <Input
                  id="patientName"
                  value={formData.patientName}
                  onChange={(e) => handleChange('patientName', e.target.value)}
                  required
                  placeholder="Ej: María González"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="age">Edad *</Label>
                <Input
                  id="age"
                  type="number"
                  value={formData.age}
                  onChange={(e) => handleChange('age', e.target.value)}
                  required
                  placeholder="Ej: 68"
                />
              </div>

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
                <Label htmlFor="admissionDate">Fecha de Ingreso *</Label>
                <Input
                  id="admissionDate"
                  type="date"
                  value={formData.admissionDate}
                  onChange={(e) => handleChange('admissionDate', e.target.value)}
                  required
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
              <Label htmlFor="expectedDays">Días Esperados de Estadía (según GRD/protocolo)</Label>
              <Input
                id="expectedDays"
                type="number"
                value={formData.expectedDays}
                onChange={(e) => handleChange('expectedDays', e.target.value)}
                placeholder="Ej: 5"
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
              <p className="text-muted-foreground">
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

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setFormData({
                patientName: '',
                age: '',
                service: '',
                diagnosis: '',
                admissionDate: '',
                expectedDays: '',
                socialFactors: '',
                clinicalNotes: '',
                submittedBy: ''
              })}>
                Limpiar Formulario
              </Button>
              <Button type="submit">
                <Send className="w-4 h-4 mr-2" />
                Enviar Derivación
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
