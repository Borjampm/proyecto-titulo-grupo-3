"""
Excel data uploader for populating the database with patient and bed information.

This module handles uploading data from Excel files:
- "Camas NWP1 24-09-2025 1235.xlsx" -> beds table
- "Score Social.xlsx" -> patients, patient_information, clinical_episodes, and clinical_episode_information tables
"""

import asyncio
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models.bed import Bed
from app.models.patient import Patient
from app.models.patient_information import PatientInformation
from app.models.clinical_episode import ClinicalEpisode, EpisodeStatus
from app.models.clinical_episode_information import (
    ClinicalEpisodeInformation,
    EpisodeInfoType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Names for realistic placeholder data
FIRST_NAMES = [
    "María", "José", "Carlos", "Juan", "Pedro", "Luis", "Francisco", "Jorge", 
    "Manuel", "Antonio", "Alejandro", "Roberto", "Miguel", "Ricardo", "Andrés",
    "Pablo", "Sergio", "Fernando", "Diego", "Gabriel", "Cristián", "Rodrigo",
    "Marcelo", "Daniel", "Felipe", "Jaime", "Claudio", "Eduardo", "Mauricio",
    "Raúl", "Carmen", "Ana", "Rosa", "Isabel", "Patricia", "Gloria", "Lucía",
    "Teresa", "Marta", "Silvia", "Elena", "Verónica", "Claudia", "Carolina",
    "Francisca", "Javiera", "Camila", "Daniela", "Valentina", "Constanza"
]

LAST_NAMES = [
    "González", "Muñoz", "Rodríguez", "García", "Martínez", "López", "Hernández",
    "Pérez", "Fernández", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera",
    "Gómez", "Díaz", "Contreras", "Rojas", "Silva", "Sepúlveda", "Morales",
    "Vargas", "Castillo", "Núñez", "Guzmán", "Vega", "Reyes", "Espinoza",
    "Jara", "Figueroa", "Álvarez", "Poblete", "Valdés", "Navarro", "Campos"
]


def calculate_rut_verifier(rut_number: int) -> str:
    """
    Calculate the verification digit for a RUT.
    
    Args:
        rut_number: The RUT number without verification digit
        
    Returns:
        The verification digit (0-9 or K)
    """
    multiplier = 2
    sum_value = 0
    
    while rut_number > 0:
        sum_value += (rut_number % 10) * multiplier
        rut_number //= 10
        multiplier += 1
        if multiplier > 7:
            multiplier = 2
    
    remainder = sum_value % 11
    verifier = 11 - remainder
    
    if verifier == 11:
        return "0"
    elif verifier == 10:
        return "K"
    else:
        return str(verifier)


def generate_rut(seed: str) -> str:
    """
    Generate a valid RUT based on a seed string.
    
    Args:
        seed: A string to generate consistent RUT (e.g., episode ID)
        
    Returns:
        A valid RUT in format "XX.XXX.XXX-X"
    """
    # Generate a number from seed (between 5,000,000 and 25,000,000 for realistic RUTs)
    seed_hash = hash(seed)
    rut_number = 5000000 + (abs(seed_hash) % 20000000)
    
    # Calculate verification digit
    verifier = calculate_rut_verifier(rut_number)
    
    # Format with dots and dash
    rut_str = f"{rut_number:,}".replace(",", ".")
    return f"{rut_str}-{verifier}"


def get_name(seed: str) -> tuple[str, str]:
    """
    Get a consistent name based on a seed string.
    
    Args:
        seed: A string to generate consistent name (e.g., episode ID)
        
    Returns:
        Tuple of (first_name, last_name)
    """
    seed_hash = abs(hash(seed))
    first_name_idx = seed_hash % len(FIRST_NAMES)
    last_name_idx = (seed_hash // len(FIRST_NAMES)) % len(LAST_NAMES)
    
    first_name = FIRST_NAMES[first_name_idx]
    last_name = LAST_NAMES[last_name_idx]
    
    return first_name, last_name


class ExcelUploader:
    """Handles uploading data from Excel files to the database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ==================== BED DATA UPLOAD ====================

    async def upload_beds_from_excel(self, excel_path: str | Path) -> int:
        """
        Upload bed data from "Camas" sheet in the Excel file.

        Args:
            excel_path: Path to the "Camas NWP1 24-09-2025 1235.xlsx" file

        Returns:
            Number of beds uploaded
        """
        logger.info(f"Reading beds data from {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name="Camas")
            logger.info(f"Found {len(df)} rows in Camas sheet")

            beds_created = 0

            for idx, row in df.iterrows():
                try:
                    bed_data = self._parse_bed_row(row)
                    if bed_data:
                        await self._create_or_update_bed(bed_data)
                        beds_created += 1
                except Exception as e:
                    logger.error(f"Error processing bed row {idx}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"Successfully uploaded {beds_created} beds")
            return beds_created

        except Exception as e:
            logger.error(f"Error uploading beds: {e}")
            await self.db.rollback()
            raise

    def _parse_bed_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse a bed row from the Excel file.

        Expected columns from "Camas NWP1 24-09-2025 1235.xlsx":
        - CAMA: Bed/room identifier
        - CAMA_BLOQUEADA: Whether bed is blocked/unavailable
        - HABITACION: Room number (used as identifier)
        
        Missing data is allowed and will use defaults.
        """
        try:
            # Use CAMA as the room identifier, fallback to HABITACION if not available
            room_raw = row.get("CAMA")
            if pd.isna(room_raw) or str(room_raw).strip() == "":
                # Try CAMA as fallback
                room_raw = row.get("HABITACION")
            
            room = str(room_raw).strip() if not pd.isna(room_raw) else ""
            
            # Only skip if room is completely empty or 'nan'
            if not room or room == "" or room.lower() == "nan":
                logger.warning(f"Skipping row with missing room/bed information")
                return None

            # Parse blocked status - if CAMA_BLOQUEADA exists, use it
            # Blocked bed = not available
            blocked_raw = row.get("CAMA_BLOQUEADA")
            if pd.isna(blocked_raw):
                # Default: bed is not blocked (is available)
                available = True
            else:
                # If CAMA_BLOQUEADA has any value, bed is blocked (not available)
                blocked_str = str(blocked_raw).strip().upper()
                # Check if it's actually blocked (not empty, not "NO", etc.)
                available = blocked_str in ["", "NO", "N", "FALSE", "0"]

            # Active status - default to True
            # You can add logic here if there's a field indicating inactive beds
            active = True

            return {
                "room": room,
                "active": active,
                "available": available,
            }

        except Exception as e:
            logger.error(f"Error parsing bed row: {e}")
            return None

    async def _create_or_update_bed(self, bed_data: Dict[str, Any]) -> Bed:
        """Create or update a bed in the database."""
        # Check if bed with this room already exists
        stmt = select(Bed).where(Bed.room == bed_data["room"])
        result = await self.db.execute(stmt)
        existing_bed = result.scalar_one_or_none()

        if existing_bed:
            # Update existing bed
            existing_bed.active = bed_data["active"]
            existing_bed.available = bed_data["available"]
            logger.info(f"Updated bed: {bed_data['room']}")
            return existing_bed
        else:
            # Create new bed
            bed = Bed(**bed_data)
            self.db.add(bed)
            logger.info(f"Created bed: {bed_data['room']}")
            return bed

    # ==================== PATIENT DATA UPLOAD ====================

    async def upload_patients_from_excel(self, excel_path: str | Path) -> int:
        """
        Upload patient data from "Data Casos" sheet in the Score Social Excel file.

        This method creates:
        - Patients
        - Patient Information
        - Clinical Episodes
        - Clinical Episode Information

        Args:
            excel_path: Path to the "Score Social.xlsx" file

        Returns:
            Number of patients uploaded
        """
        logger.info(f"Reading patient data from {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name="Data Casos")
            logger.info(f"Found {len(df)} rows in Data Casos sheet")

            patients_created = 0

            for idx, row in df.iterrows():
                try:
                    await self._process_patient_row(row, idx)
                    patients_created += 1
                except Exception as e:
                    logger.error(f"Error processing patient row {idx}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"Successfully uploaded {patients_created} patients")
            return patients_created

        except Exception as e:
            logger.error(f"Error uploading patients: {e}")
            await self.db.rollback()
            raise

    async def _process_patient_row(self, row: pd.Series, row_idx: int) -> None:
        """Process a single patient row from the Excel file."""
        # Parse patient data
        patient_data = self._parse_patient_data(row)
        if not patient_data:
            return

        # Create or get patient
        patient = await self._create_or_get_patient(patient_data)

        # Create patient information
        patient_info_data = self._parse_patient_information(row)
        if patient_info_data:
            await self._create_or_update_patient_information(
                patient.id, patient_info_data
            )

        # Create clinical episode
        episode_data = self._parse_clinical_episode_data(row)
        episode = await self._create_clinical_episode(patient.id, episode_data)

        # Create clinical episode information records
        episode_info_records = self._parse_clinical_episode_information(row)
        for info_record in episode_info_records:
            await self._create_clinical_episode_information(episode.id, info_record)

        logger.info(
            f"Processed patient {patient.medical_identifier} with episode {episode.id}"
        )

    def _parse_patient_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse patient basic data from Excel row.

        Expected columns from "Score Social.xlsx":
        - RUT: Patient's RUT (may be empty for anonymous data) - Used as medical_identifier
        - Nombre: Patient's full name (may be empty for anonymous data)
        - Episodio / Estadía: Episode identifier (stored separately in episode data)
        - Fecha de nacimiento: Birth date
        
        If RUT and Nombre are present, they are used. If empty (anonymous data), 
        we generate realistic placeholder data:
        - Valid RUT with proper verification digit (used as medical_identifier)
        - Common first and last names
        - Consistent data based on episode ID (same episode always generates same name/RUT)
        
        Example with real data: RUT "12.345.678-5", Nombre "Juan Pérez" → Used as-is
        Example with anonymous: Empty fields → Generated "María González", "18.234.567-8"
        """
        try:
            # Get episode identifier to use as seed for generating consistent placeholder data
            episodio_raw = row.get("Episodio / Estadía")
            
            # Only skip if episodio is completely missing (we need it for seed generation)
            if pd.isna(episodio_raw):
                logger.warning("Skipping row with missing Episodio / Estadía")
                return None
            
            episodio_str = str(episodio_raw).strip()
            if not episodio_str or episodio_str == "" or episodio_str.lower() == "nan":
                logger.warning("Skipping row with empty Episodio / Estadía")
                return None
            
            # Check if RUT exists in the data - RUT is the medical_identifier
            rut_raw = row.get("RUT")
            if pd.isna(rut_raw) or str(rut_raw).strip() == "" or str(rut_raw).strip().lower() == "nan":
                # Generate placeholder RUT using episode as seed for consistency
                rut = generate_rut(episodio_str)
                medical_identifier = rut  # Generated RUT is the medical identifier
            else:
                # Use the real RUT from the data
                rut = str(rut_raw).strip()
                medical_identifier = rut  # Real RUT is the medical identifier
            
            # Check if Nombre exists in the data
            nombre_raw = row.get("Nombre")
            if pd.isna(nombre_raw) or str(nombre_raw).strip() == "" or str(nombre_raw).strip().lower() == "nan":
                # Generate placeholder name using episode as seed
                first_name, last_name = get_name(episodio_str)
            else:
                # Use the real name from the data
                nombre = str(nombre_raw).strip()
                # Try to split name into first and last
                name_parts = nombre.split(None, 1)  # Split on first whitespace
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[1]
                else:
                    first_name = nombre
                    last_name = ""
            
            # Parse birth date - "Fecha de nacimiento"
            birth_date_raw = row.get("Fecha de nacimiento")
            if pd.isna(birth_date_raw):
                # If no birth date, use a default for missing data
                birth_date = date(1970, 1, 1)
            elif isinstance(birth_date_raw, pd.Timestamp):
                birth_date = birth_date_raw.date()
            elif isinstance(birth_date_raw, date):
                birth_date = birth_date_raw
            else:
                try:
                    birth_date = pd.to_datetime(birth_date_raw).date()
                except:
                    birth_date = date(1970, 1, 1)

            # Gender not in this Excel - use default
            gender = "Desconocido"

            return {
                "medical_identifier": medical_identifier,
                "first_name": first_name,
                "last_name": last_name,
                "rut": rut,
                "birth_date": birth_date,
                "gender": gender,
            }

        except Exception as e:
            logger.error(f"Error parsing patient data: {e}")
            return None

    def _parse_patient_information(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse patient information (additional data stored as JSONB).

        This includes all Excel columns not used in the main patient or episode tables.
        Missing data is stored as null to preserve data completeness for analysis.
        
        From Score Social.xlsx columns:
        - Centro Atención, Nombre de la aseguradora, Previsión Homóloga, 
        - Vía de Ingreso, Encuesta, Motivo, Puntaje, Encuestadora, etc.
        """
        try:
            info = {}

            # List of columns that are used elsewhere and should be excluded
            excluded_columns = [
                # Patient basic info
                "RUT", "Nombre", "Fecha de nacimiento",
                # Episode info
                "Episodio / Estadía", "Fe.admisión", "Fecha del alta", 
                "DÍAS PACIENTES ACOSTADOS", "Estado de alta", "Cama",
                "Fecha Asignación", "Año Admisión", "Mes Admisión",
            ]

            # Add all columns as additional info, storing null for missing values
            for col in row.index:
                # Skip columns that are used in other tables
                if col in excluded_columns:
                    continue
                
                # Store all values, including missing ones as null
                value = row[col]
                
                if pd.isna(value):
                    # Store missing data as None/null for analysis
                    info[col] = None
                elif isinstance(value, (pd.Timestamp, datetime, date)):
                    info[col] = value.isoformat()
                elif isinstance(value, (int, float)):
                    # Check if it's NaN for floats
                    if pd.isna(value):
                        info[col] = None
                    else:
                        info[col] = float(value) if isinstance(value, float) else int(value)
                else:
                    # Convert to string, handle empty strings
                    str_value = str(value).strip()
                    info[col] = str_value if str_value and str_value.lower() != 'nan' else None

            # Return info even if empty, as it marks the data was processed
            return info

        except Exception as e:
            logger.error(f"Error parsing patient information: {e}")
            return {}

    def _parse_clinical_episode_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Parse clinical episode data from Excel row.
        
        Expected columns from Score Social.xlsx:
        - Episodio / Estadía: Episode identifier (stored in info records)
        - Fe.admisión: Admission date
        - Fecha del alta: Discharge date
        - Estado de alta: Discharge/episode status
        - Cama: Bed identifier for foreign key lookup
        - Fecha Asignación: Assignment date
        """
        try:
            # Get episode identifier to store in info records
            episodio_raw = row.get("Episodio / Estadía")
            episode_identifier = None
            if not pd.isna(episodio_raw):
                episode_identifier = str(episodio_raw).strip()
            
            # Parse admission date - use "Fe.admisión"
            admission_at_raw = row.get("Fe.admisión")
            if pd.isna(admission_at_raw):
                admission_at = datetime.now()
            elif isinstance(admission_at_raw, pd.Timestamp):
                admission_at = admission_at_raw.to_pydatetime()
            else:
                try:
                    admission_at = pd.to_datetime(admission_at_raw).to_pydatetime()
                except:
                    admission_at = datetime.now()

            # Parse discharge date - "Fecha del alta"
            discharge_raw = row.get("Fecha del alta")
            expected_discharge = None
            discharge_at = None
            if not pd.isna(discharge_raw):
                try:
                    # Handle string dates in DD-MM-YYYY format (e.g., "24-09-2025")
                    if isinstance(discharge_raw, str):
                        # Try parsing DD-MM-YYYY format
                        discharge_dt = pd.to_datetime(discharge_raw, format='%d-%m-%Y', errors='coerce')
                        if pd.isna(discharge_dt):
                            # Fallback to pandas auto-detection
                            discharge_dt = pd.to_datetime(discharge_raw, errors='coerce')
                        
                        if not pd.isna(discharge_dt):
                            discharge_date = discharge_dt.date()
                            discharge_at = discharge_dt.to_pydatetime()
                            expected_discharge = discharge_date
                    elif isinstance(discharge_raw, pd.Timestamp):
                        discharge_date = discharge_raw.date()
                        discharge_at = discharge_raw.to_pydatetime()
                        expected_discharge = discharge_date
                    else:
                        discharge_dt = pd.to_datetime(discharge_raw, errors='coerce')
                        if not pd.isna(discharge_dt):
                            discharge_date = discharge_dt.date()
                            discharge_at = discharge_dt.to_pydatetime()
                            expected_discharge = discharge_date
                except Exception as e:
                    logger.warning(f"Could not parse discharge date '{discharge_raw}': {e}")
                    expected_discharge = None
                    discharge_at = None

            # Parse status - use "Estado de alta"
            status_raw = row.get("Estado de alta")
            status = EpisodeStatus.ACTIVE
            if not pd.isna(status_raw):
                status_str = str(status_raw).strip()
                status_upper = status_str.upper()
                
                # Check for "Alta" or variations
                if "ALTA" in status_upper:
                    status = EpisodeStatus.DISCHARGED
                elif "TRANSFERIDO" in status_upper or "TRANSFER" in status_upper:
                    status = EpisodeStatus.TRANSFERRED
                elif "CANCELADO" in status_upper or "CANCEL" in status_upper:
                    status = EpisodeStatus.CANCELLED
                
                logger.debug(f"Estado de alta: '{status_str}' -> status: {status}")
            else:
                # If there's a discharge date but no status, assume DISCHARGED
                if discharge_at is not None:
                    status = EpisodeStatus.DISCHARGED

            # Get bed identifier for foreign key lookup - use "Cama"
            bed_identifier = row.get("Cama")
            bed_room = None
            if not pd.isna(bed_identifier):
                bed_room_str = str(bed_identifier).strip()
                if bed_room_str and bed_room_str.lower() != 'nan':
                    bed_room = bed_room_str

            return {
                "admission_at": admission_at,
                "expected_discharge": expected_discharge,
                "discharge_at": discharge_at,
                "status": status,
                "bed_room": bed_room,  # Store room name for async bed_id lookup
                "episode_identifier": episode_identifier,  # Store for info records
            }

        except Exception as e:
            logger.error(f"Error parsing clinical episode data: {e}")
            return {
                "admission_at": datetime.now(),
                "status": EpisodeStatus.ACTIVE,
                "bed_room": None,
                "episode_identifier": None,
            }

    def _parse_clinical_episode_information(
        self, row: pd.Series
    ) -> list[Dict[str, Any]]:
        """
        Parse clinical episode information records from Excel row.

        These are additional structured data about the episode.
        Missing data is stored as null to preserve data completeness for analysis.
        
        From Score Social.xlsx columns:
        - Texto libre diagnóstico admisión: Diagnosis
        - Servicio: Service/department
        - Centro Atención: Healthcare center
        - Clasificación Marca 1, 2, 3: Classifications
        - Encuesta, Motivo, Puntaje: Survey information
        """
        records = []

        try:
            # Diagnosis information
            diagnosis = row.get("Texto libre diagnóstico admisión")
            diagnosis_value = str(diagnosis).strip() if not pd.isna(diagnosis) and str(diagnosis).strip().lower() != 'nan' else None
            if diagnosis_value:
                records.append({
                    "info_type": EpisodeInfoType.DIAGNOSIS,
                    "title": "Diagnóstico de Admisión",
                    "value": {"diagnosis": diagnosis_value},
                })

            # Service/Department
            servicio = row.get("Servicio")
            servicio_value = str(servicio).strip() if not pd.isna(servicio) and str(servicio).strip().lower() != 'nan' else None
            if servicio_value:
                records.append({
                    "info_type": EpisodeInfoType.NOTES,
                    "title": "Servicio",
                    "value": {"servicio": servicio_value},
                })

            # Healthcare Center
            centro = row.get("Centro Atención")
            centro_value = str(centro).strip() if not pd.isna(centro) and str(centro).strip().lower() != 'nan' else None
            if centro_value:
                records.append({
                    "info_type": EpisodeInfoType.NOTES,
                    "title": "Centro de Atención",
                    "value": {"centro_atencion": centro_value},
                })

            # Classifications (Marca 1, 2, 3)
            marca1 = row.get("Clasificación Marca 1")
            marca2 = row.get("Clasificación Marca 2")
            marca3 = row.get("Clasificación Marca 3")
            
            if not pd.isna(marca1) or not pd.isna(marca2) or not pd.isna(marca3):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Clasificaciones",
                    "value": {
                        "marca_1": str(marca1).strip() if not pd.isna(marca1) else None,
                        "marca_2": str(marca2).strip() if not pd.isna(marca2) else None,
                        "marca_3": str(marca3).strip() if not pd.isna(marca3) else None,
                    },
                })

            # Insurance/Coverage information
            convenio = row.get("Desc. Convenio")
            aseguradora = row.get("Nombre de la aseguradora")
            prevision = row.get("Previsión Homóloga")
            
            if not pd.isna(convenio) or not pd.isna(aseguradora) or not pd.isna(prevision):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Información de Cobertura",
                    "value": {
                        "convenio": str(convenio).strip() if not pd.isna(convenio) else None,
                        "aseguradora": str(aseguradora).strip() if not pd.isna(aseguradora) else None,
                        "prevision": str(prevision).strip() if not pd.isna(prevision) else None,
                    },
                })

            # Entry path
            via_ingreso = row.get("Vía de Ingreso")
            if not pd.isna(via_ingreso):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Vía de Ingreso",
                    "value": {"via_ingreso": str(via_ingreso).strip()},
                })

            # Survey information
            encuesta = row.get("Encuesta")
            motivo = row.get("Motivo")
            puntaje = row.get("Puntaje")
            encuestadora = row.get("Encuestadora")
            
            if not pd.isna(encuesta) or not pd.isna(motivo) or not pd.isna(puntaje) or not pd.isna(encuestadora):
                puntaje_value = None
                if not pd.isna(puntaje):
                    try:
                        puntaje_value = float(puntaje) if isinstance(puntaje, (int, float)) else float(str(puntaje))
                    except:
                        puntaje_value = str(puntaje).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Información de Encuesta",
                    "value": {
                        "encuesta": str(encuesta).strip() if not pd.isna(encuesta) else None,
                        "motivo": str(motivo).strip() if not pd.isna(motivo) else None,
                        "puntaje": puntaje_value,
                        "encuestadora": str(encuestadora).strip() if not pd.isna(encuestadora) else None,
                    },
                })

            # Valor Parcial (partial value/cost)
            valor_parcial = row.get(" Valor Parcial ")  # Note the spaces in column name
            if pd.isna(valor_parcial):
                valor_parcial = row.get("Valor Parcial")  # Try without spaces
            
            if not pd.isna(valor_parcial):
                try:
                    valor_value = float(valor_parcial) if isinstance(valor_parcial, (int, float)) else float(str(valor_parcial))
                except:
                    valor_value = str(valor_parcial).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Valor Parcial",
                    "value": {"valor_parcial": valor_value},
                })

            # Days count
            dias = row.get("DÍAS PACIENTES ACOSTADOS")
            if not pd.isna(dias):
                try:
                    dias_value = int(dias) if isinstance(dias, (int, float)) else int(str(dias))
                except:
                    dias_value = str(dias).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Días de Hospitalización",
                    "value": {"dias_acostados": dias_value},
                })

            # Known columns that we've already processed
            known_columns = [
                # Patient info
                "RUT", "Nombre", "Fecha de nacimiento",
                # Episode info
                "Episodio / Estadía", "Fe.admisión", "Fecha del alta", 
                "Estado de alta", "Cama", "Fecha Asignación", 
                "Año Admisión", "Mes Admisión",
                # Already processed in records above
                "Texto libre diagnóstico admisión", "Servicio", "Centro Atención",
                "Clasificación Marca 1", "Clasificación Marca 2", "Clasificación Marca 3",
                "Desc. Convenio", "Nombre de la aseguradora", "Previsión Homóloga",
                "Vía de Ingreso", "Encuesta", "Motivo", "Puntaje", "Encuestadora",
                " Valor Parcial ", "Valor Parcial", "DÍAS PACIENTES ACOSTADOS"
            ]
            
            # Store any other columns as OTHER type
            for col in row.index:
                if col in known_columns:
                    continue
                
                value = row[col]
                if pd.isna(value):
                    value_data = None
                elif isinstance(value, (pd.Timestamp, datetime, date)):
                    value_data = value.isoformat()
                else:
                    str_value = str(value).strip()
                    value_data = str_value if str_value.lower() != 'nan' else None
                
                # Only add if there's actual data
                if value_data is not None:
                    records.append({
                        "info_type": EpisodeInfoType.OTHER,
                        "title": col,
                        "value": {col: value_data},
                    })

        except Exception as e:
            logger.error(f"Error parsing clinical episode information: {e}")

        return records

    async def _create_or_get_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """Create or get existing patient by medical identifier."""
        stmt = select(Patient).where(
            Patient.medical_identifier == patient_data["medical_identifier"]
        )
        result = await self.db.execute(stmt)
        existing_patient = result.scalar_one_or_none()

        if existing_patient:
            logger.info(
                f"Found existing patient: {patient_data['medical_identifier']}"
            )
            return existing_patient

        # Create new patient
        patient = Patient(**patient_data)
        self.db.add(patient)
        await self.db.flush()  # Flush to get the ID
        logger.info(f"Created new patient: {patient_data['medical_identifier']}")
        return patient

    async def _create_or_update_patient_information(
        self, patient_id: UUID, information: Dict[str, Any]
    ) -> PatientInformation:
        """Create or update patient information."""
        stmt = select(PatientInformation).where(
            PatientInformation.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        existing_info = result.scalar_one_or_none()

        if existing_info:
            # Update existing information
            existing_info.information = information
            logger.info(f"Updated patient information for patient {patient_id}")
            return existing_info

        # Create new information record
        patient_info = PatientInformation(
            patient_id=patient_id, information=information
        )
        self.db.add(patient_info)
        await self.db.flush()
        logger.info(f"Created patient information for patient {patient_id}")
        return patient_info

    async def _create_clinical_episode(
        self, patient_id: UUID, episode_data: Dict[str, Any]
    ) -> ClinicalEpisode:
        """Create a new clinical episode with bed foreign key lookup."""
        # Extract episode identifier for info records (not part of ClinicalEpisode model)
        episode_identifier = episode_data.pop("episode_identifier", None)
        
        # Handle bed lookup if bed_room is provided
        bed_room = episode_data.pop("bed_room", None)
        bed_id = None
        if bed_room:
            bed_id = await self._get_bed_id_by_room(bed_room)
            if not bed_id:
                logger.warning(f"Bed not found for room '{bed_room}', episode will have no bed assigned")
        
        episode_data["bed_id"] = bed_id
        episode = ClinicalEpisode(patient_id=patient_id, **episode_data)
        self.db.add(episode)
        await self.db.flush()  # Flush to get the ID
        
        # Store episode identifier as an information record if provided
        if episode_identifier:
            episode_info = ClinicalEpisodeInformation(
                episode_id=episode.id,
                info_type=EpisodeInfoType.OTHER,
                title="Episodio / Estadía",
                value={"episode_identifier": episode_identifier}
            )
            self.db.add(episode_info)
            await self.db.flush()
        
        logger.info(f"Created clinical episode for patient {patient_id} with bed_id {bed_id}")
        return episode

    async def _create_clinical_episode_information(
        self, episode_id: UUID, info_data: Dict[str, Any]
    ) -> ClinicalEpisodeInformation:
        """Create a clinical episode information record."""
        info = ClinicalEpisodeInformation(episode_id=episode_id, **info_data)
        self.db.add(info)
        await self.db.flush()
        return info

    async def _get_bed_id_by_room(self, room: str) -> Optional[UUID]:
        """Get bed ID by room identifier."""
        stmt = select(Bed).where(Bed.room == room)
        result = await self.db.execute(stmt)
        bed = result.scalar_one_or_none()
        return bed.id if bed else None


# ==================== MAIN UPLOAD FUNCTIONS ====================


async def upload_all_data(
    beds_excel_path: str | Path, patients_excel_path: str | Path
) -> Dict[str, int]:
    """
    Upload all data from both Excel files.

    Args:
        beds_excel_path: Path to "Camas NWP1 24-09-2025 1235.xlsx"
        patients_excel_path: Path to "Score Social.xlsx"

    Returns:
        Dictionary with counts of uploaded records
    """
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)

        results = {}

        # Upload beds first (patients may reference beds)
        logger.info("Starting bed data upload...")
        results["beds"] = await uploader.upload_beds_from_excel(beds_excel_path)

        # Upload patients and related data
        logger.info("Starting patient data upload...")
        results["patients"] = await uploader.upload_patients_from_excel(
            patients_excel_path
        )

        return results


async def upload_beds_only(excel_path: str | Path) -> int:
    """Upload only bed data."""
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)
        return await uploader.upload_beds_from_excel(excel_path)


async def upload_patients_only(excel_path: str | Path) -> int:
    """Upload only patient data."""
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)
        return await uploader.upload_patients_from_excel(excel_path)


# ==================== CLI INTERFACE ====================


def main():
    """Main CLI interface for uploading Excel data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload Excel data to the database"
    )
    parser.add_argument(
        "--beds",
        type=str,
        help='Path to beds Excel file (e.g., "Camas NWP1 24-09-2025 1235.xlsx")',
    )
    parser.add_argument(
        "--patients",
        type=str,
        help='Path to patients Excel file (e.g., "Score Social.xlsx")',
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all data (requires both --beds and --patients)",
    )

    args = parser.parse_args()

    if args.all:
        if not args.beds or not args.patients:
            print("Error: --all requires both --beds and --patients arguments")
            return

        print("Uploading all data...")
        results = asyncio.run(upload_all_data(args.beds, args.patients))
        print(f"Upload complete!")
        print(f"  Beds uploaded: {results['beds']}")
        print(f"  Patients uploaded: {results['patients']}")

    elif args.beds:
        print(f"Uploading beds from {args.beds}...")
        count = asyncio.run(upload_beds_only(args.beds))
        print(f"Upload complete! {count} beds uploaded.")

    elif args.patients:
        print(f"Uploading patients from {args.patients}...")
        count = asyncio.run(upload_patients_only(args.patients))
        print(f"Upload complete! {count} patients uploaded.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
