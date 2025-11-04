/**
 * Servicio para procesar archivos Excel/CSV
 * 
 * Este servicio maneja la lectura y procesamiento de archivos Excel/CSV
 * para importar datos de pacientes al sistema.
 */

import { Patient } from '../types';
import * as XLSX from 'xlsx';

export interface ExcelParseResult {
  patients: Partial<Patient>[];
  errors: string[];
  warnings: string[];
}

/**
 * Parsea un archivo Excel o CSV y extrae datos de pacientes
 */
export async function parseExcelFile(file: File): Promise<ExcelParseResult> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        if (!data) {
          reject(new Error('No se pudo leer el archivo'));
          return;
        }

        const workbook = XLSX.read(data, { type: 'binary' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<Record<string, any>>(firstSheet);

        const result = processExcelRows(rows);
        resolve(result);
      } catch (error) {
        reject(error instanceof Error ? error : new Error('Error al procesar el archivo'));
      }
    };

    reader.onerror = () => {
      reject(new Error('Error al leer el archivo'));
    };

    reader.readAsBinaryString(file);
  });
}

/**
 * Procesa las filas del Excel y las convierte en objetos Patient
 */
function processExcelRows(rows: Record<string, any>[]): ExcelParseResult {
  const patients: Partial<Patient>[] = [];
  const errors: string[] = [];
  const warnings: string[] = [];

  rows.forEach((row, index) => {
    const rowNumber = index + 2; // +2 porque Excel empieza en 1 y tiene header

    try {
      // Mapeo de columnas (ajusta según tu Excel)
      // Estas son las columnas esperadas según tu modelo de datos
      const patient: Partial<Patient> = {
        rut: cleanString(row['RUT'] || row['rut']),
        name: cleanString(row['Nombre'] || row['nombre'] || row['name']),
        age: parseNumber(row['Edad'] || row['edad'] || row['age']),
        bed: cleanString(row['Cama'] || row['cama'] || row['bed']),
        service: cleanString(row['Servicio'] || row['servicio'] || row['service']),
        admissionDate: parseDate(row['Fecha Ingreso'] || row['fecha_ingreso'] || row['admissionDate']),
        diagnosis: cleanString(row['Diagnóstico'] || row['diagnostico'] || row['diagnosis']),
        grg: cleanString(row['GRD'] || row['grg'] || row['GRG']),
        expectedDays: parseNumber(row['Días Esperados'] || row['dias_esperados'] || row['expectedDays']),
        responsible: cleanString(row['Médico Responsable'] || row['medico_responsable'] || row['responsible']),
        prevision: cleanString(row['Previsión'] || row['prevision']),
        contactNumber: cleanString(row['Contacto'] || row['contacto'] || row['contactNumber']),
      };

      // Validaciones básicas
      const validationErrors = validatePatient(patient, rowNumber);
      
      if (validationErrors.length > 0) {
        errors.push(...validationErrors);
      } else {
        // Calcular campos derivados
        if (patient.admissionDate) {
          patient.daysInStay = calculateDaysInStay(patient.admissionDate);
        }

        // Valores por defecto
        patient.status = 'active';
        patient.caseStatus = 'open';
        patient.riskLevel = 'low';
        patient.socialRisk = false;
        patient.financialRisk = false;

        patients.push(patient);
      }
    } catch (error) {
      errors.push(`Fila ${rowNumber}: Error al procesar - ${error instanceof Error ? error.message : 'Error desconocido'}`);
    }
  });

  if (patients.length === 0 && errors.length > 0) {
    errors.unshift('No se pudo importar ningún paciente. Verifica el formato del archivo.');
  }

  return { patients, errors, warnings };
}

/**
 * Valida que un paciente tenga los campos mínimos requeridos
 */
function validatePatient(patient: Partial<Patient>, rowNumber: number): string[] {
  const errors: string[] = [];

  if (!patient.name || patient.name.trim() === '') {
    errors.push(`Fila ${rowNumber}: Falta el nombre del paciente`);
  }

  if (!patient.age || patient.age < 0 || patient.age > 150) {
    errors.push(`Fila ${rowNumber}: Edad inválida (${patient.age})`);
  }

  if (!patient.admissionDate) {
    errors.push(`Fila ${rowNumber}: Falta la fecha de ingreso`);
  }

  if (!patient.service || patient.service.trim() === '') {
    errors.push(`Fila ${rowNumber}: Falta el servicio clínico`);
  }

  if (!patient.diagnosis || patient.diagnosis.trim() === '') {
    errors.push(`Fila ${rowNumber}: Falta el diagnóstico`);
  }

  return errors;
}

/**
 * Limpia y normaliza strings
 */
function cleanString(value: any): string | undefined {
  if (value === null || value === undefined) return undefined;
  const str = String(value).trim();
  return str === '' ? undefined : str;
}

/**
 * Parsea números de manera segura
 */
function parseNumber(value: any): number | undefined {
  if (value === null || value === undefined || value === '') return undefined;
  const num = Number(value);
  return isNaN(num) ? undefined : num;
}

/**
 * Parsea fechas de Excel
 */
function parseDate(value: any): string | undefined {
  if (!value) return undefined;

  // Si ya es una fecha en formato ISO
  if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
    return value;
  }

  // Si es un número de Excel (días desde 1900-01-01)
  if (typeof value === 'number') {
    const date = XLSX.SSF.parse_date_code(value);
    return `${date.y}-${String(date.m).padStart(2, '0')}-${String(date.d).padStart(2, '0')}`;
  }

  // Intentar parsear como fecha
  try {
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0];
    }
  } catch {
    // Ignorar error
  }

  return undefined;
}

/**
 * Calcula los días de estadía desde la fecha de ingreso
 */
function calculateDaysInStay(admissionDate: string): number {
  const admission = new Date(admissionDate);
  const today = new Date();
  const diffTime = Math.abs(today.getTime() - admission.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
}

/**
 * Valida el formato del archivo
 */
export function validateFileFormat(file: File): { valid: boolean; error?: string } {
  const validExtensions = ['.xlsx', '.xls', '.csv'];
  const fileName = file.name.toLowerCase();
  const hasValidExtension = validExtensions.some((ext) => fileName.endsWith(ext));

  if (!hasValidExtension) {
    return {
      valid: false,
      error: 'Formato de archivo no válido. Use Excel (.xlsx, .xls) o CSV (.csv)',
    };
  }

  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'El archivo es demasiado grande. Máximo 10MB',
    };
  }

  return { valid: true };
}

/**
 * Genera un template Excel vacío con las columnas esperadas
 */
export function generateExcelTemplate(): void {
  const headers = [
    'RUT',
    'Nombre',
    'Edad',
    'Cama',
    'Servicio',
    'Fecha Ingreso',
    'Diagnóstico',
    'GRD',
    'Días Esperados',
    'Médico Responsable',
    'Previsión',
    'Contacto',
  ];

  const ws = XLSX.utils.aoa_to_sheet([headers]);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Pacientes');

  XLSX.writeFile(wb, 'template_pacientes.xlsx');
}

/**
 * Exporta pacientes a Excel
 */
export function exportPatientsToExcel(patients: Patient[]): void {
  const data = patients.map((p) => ({
    RUT: p.rut || '',
    Nombre: p.name,
    Edad: p.age,
    Cama: p.bed || '',
    Servicio: p.service,
    'Fecha Ingreso': p.admissionDate,
    'Fecha Alta': p.dischargeDate || '',
    Diagnóstico: p.diagnosis,
    GRD: p.grg,
    'Días en Estadía': p.daysInStay,
    'Días Esperados': p.expectedDays,
    'Médico Responsable': p.responsible,
    Previsión: p.prevision || '',
    Contacto: p.contactNumber || '',
    'Nivel de Riesgo': p.riskLevel,
    'Estado del Caso': p.caseStatus,
    Estado: p.status,
  }));

  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Pacientes');

  const date = new Date().toISOString().split('T')[0];
  XLSX.writeFile(wb, `pacientes_${date}.xlsx`);
}
