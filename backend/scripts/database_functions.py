#!/usr/bin/env python3
"""
Database management script for the clinical management system.

This script provides functions to manage the database including:
- Seeding sample data for all tables
- Resetting the database (drop, recreate, and seed)
- Clearing the database (drop and recreate empty tables)

Sample data includes:
- Patients with their information
- Beds for hospital management
- Clinical episodes with proper relationships
- Documents for patients and episodes
- Clinical episode information records

Available functions:
    seed()   - Seed the database with sample data (preserves existing data)
    reset()  - Drop all tables, recreate them, and seed with sample data
    clear()  - Drop all tables and recreate them empty (no seed data)
"""

import asyncio
import argparse
import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings
from app.db import Base
from app.models.patient import Patient
from app.models.patient_information import PatientInformation
from app.models.patient_document import PatientDocument, DocumentType
from app.models.bed import Bed
from app.models.clinical_episode import ClinicalEpisode, EpisodeStatus
from app.models.episode_document import EpisodeDocument, EpisodeDocumentType
from app.models.clinical_episode_information import ClinicalEpisodeInformation, EpisodeInfoType
from app.models.task_instance import TaskInstance, TaskStatus
from app.models.task_status_history import TaskStatusHistory
from app.models.social_score_history import SocialScoreHistory


# Sample data - Enhanced for comprehensive search testing
SAMPLE_PATIENTS = [
    # Test Case 1: Simple single-word names
    {
        "medical_identifier": "P001",
        "first_name": "María",
        "last_name": "González",
        "rut": "12.345.678-9",
        "birth_date": date(1985, 3, 15),
        "gender": "F",
        "information": {
            "address": "Calle Falsa 123, Santiago",
            "phone": "+56 9 1234 5678",
            "emergency_contact": "Juan González - +56 9 8765 4321",
            "insurance": "FONASA",
            "blood_type": "O+",
            "allergies": ["Penicillin", "Aspirin"],
            "medical_history": "Hypertension, Diabetes Type 2"
        }
    },
    # Test Case 2: Another simple name (for testing duplicate first names)
    {
        "medical_identifier": "P002",
        "first_name": "Carlos",
        "last_name": "Rodríguez",
        "rut": "11.222.333-4",
        "birth_date": date(1978, 7, 22),
        "gender": "M",
        "information": {
            "address": "Av. Providencia 456, Providencia",
            "phone": "+56 9 2345 6789",
            "emergency_contact": "Ana Rodríguez - +56 9 9876 5432",
            "insurance": "Isapre Consalud",
            "blood_type": "A+",
            "allergies": ["Sulfa drugs"],
            "medical_history": "Previous myocardial infarction, Hyperlipidemia"
        }
    },
    # Test Case 3: Common first name for multiple matches
    {
        "medical_identifier": "P003",
        "first_name": "Ana",
        "last_name": "López",
        "rut": "13.456.789-0",
        "birth_date": date(1992, 11, 8),
        "gender": "F",
        "information": {
            "address": "Pasaje Los Leones 789, Ñuñoa",
            "phone": "+56 9 3456 7890",
            "emergency_contact": "Roberto López - +56 9 8765 4321",
            "insurance": "FONASA",
            "blood_type": "B-",
            "allergies": [],
            "medical_history": "Asthma, Migraine"
        }
    },
    # Test Case 4: Multi-word first name
    {
        "medical_identifier": "P004",
        "first_name": "Maria Jose",
        "last_name": "García",
        "rut": "14.567.890-1",
        "birth_date": date(1965, 1, 30),
        "gender": "F",
        "information": {
            "address": "Los Conquistadores 101, Las Condes",
            "phone": "+56 9 4567 8901",
            "emergency_contact": "Carmen Martínez - +56 9 7654 3210",
            "insurance": "Isapre Cruz Blanca",
            "blood_type": "AB+",
            "allergies": ["Latex"],
            "medical_history": "Pregnancy complications"
        }
    },
    # Test Case 5: Multi-word last name
    {
        "medical_identifier": "P005",
        "first_name": "Pedro",
        "last_name": "García López",
        "rut": "15.678.901-2",
        "birth_date": date(1988, 5, 20),
        "gender": "M",
        "information": {
            "address": "Av. Apoquindo 2500, Las Condes",
            "phone": "+56 9 5678 9012",
            "emergency_contact": "Isabel García - +56 9 6543 2109",
            "insurance": "FONASA",
            "blood_type": "O-",
            "allergies": ["Peanuts"],
            "medical_history": "Appendectomy 2015"
        }
    },
    # Test Case 6: Multi-word first AND last name
    {
        "medical_identifier": "P006",
        "first_name": "Ana María",
        "last_name": "De La Cruz",
        "rut": "16.789.012-3",
        "birth_date": date(1990, 9, 12),
        "gender": "F",
        "information": {
            "address": "Santa Rosa 1234, La Florida",
            "phone": "+56 9 6789 0123",
            "emergency_contact": "José De La Cruz - +56 9 5432 1098",
            "insurance": "Isapre Banmédica",
            "blood_type": "A-",
            "allergies": ["Ibuprofen"],
            "medical_history": "Chronic bronchitis"
        }
    },
    # Test Case 7: Another multi-word first AND last name
    {
        "medical_identifier": "P007",
        "first_name": "Juan Carlos",
        "last_name": "Dos Santos",
        "rut": "17.890.123-4",
        "birth_date": date(1982, 2, 28),
        "gender": "M",
        "information": {
            "address": "Gran Avenida 5678, San Miguel",
            "phone": "+56 9 7890 1234",
            "emergency_contact": "Claudia Dos Santos - +56 9 4321 0987",
            "insurance": "FONASA",
            "blood_type": "B+",
            "allergies": [],
            "medical_history": "Type 1 Diabetes, Hypertension"
        }
    },
    # Test Case 8: Duplicate first name "Maria" (different spelling)
    {
        "medical_identifier": "P008",
        "first_name": "Maria",
        "last_name": "Fernández",
        "rut": "18.901.234-5",
        "birth_date": date(1995, 6, 15),
        "gender": "F",
        "information": {
            "address": "Libertad 890, Viña del Mar",
            "phone": "+56 9 8901 2345",
            "emergency_contact": "Luis Fernández - +56 9 3210 9876",
            "insurance": "Isapre Colmena",
            "blood_type": "AB-",
            "allergies": ["Codeine"],
            "medical_history": "Seasonal allergies"
        }
    },
    # Test Case 9: Common last name to test multiple matches
    {
        "medical_identifier": "P009",
        "first_name": "Roberto",
        "last_name": "García",
        "rut": "19.012.345-6",
        "birth_date": date(1970, 12, 5),
        "gender": "M",
        "information": {
            "address": "Los Carrera 2345, Concepción",
            "phone": "+56 9 9012 3456",
            "emergency_contact": "Patricia García - +56 9 2109 8765",
            "insurance": "FONASA",
            "blood_type": "O+",
            "allergies": ["Shellfish"],
            "medical_history": "Gout, High cholesterol"
        }
    },
    # Test Case 10: Hyphenated last name
    {
        "medical_identifier": "P010",
        "first_name": "Carmen",
        "last_name": "Silva-Henríquez",
        "rut": "20.123.456-7",
        "birth_date": date(1987, 8, 22),
        "gender": "F",
        "information": {
            "address": "Pedro de Valdivia 456, Providencia",
            "phone": "+56 9 0123 4567",
            "emergency_contact": "Diego Silva - +56 9 1098 7654",
            "insurance": "Isapre Vida Tres",
            "blood_type": "A+",
            "allergies": ["Dairy"],
            "medical_history": "Lactose intolerance"
        }
    },
    # Test Case 11: Another Ana to test common name search
    {
        "medical_identifier": "P011",
        "first_name": "Ana",
        "last_name": "Martínez",
        "rut": "21.234.567-8",
        "birth_date": date(1993, 4, 10),
        "gender": "F",
        "information": {
            "address": "Vitacura 3000, Vitacura",
            "phone": "+56 9 1234 5670",
            "emergency_contact": "Sergio Martínez - +56 9 0987 6543",
            "insurance": "FONASA",
            "blood_type": "B-",
            "allergies": ["Nuts"],
            "medical_history": "No significant history"
        }
    },
    # Test Case 12: Similar to existing patient (Garcia Lopez) but reversed
    {
        "medical_identifier": "P012",
        "first_name": "López",
        "last_name": "García",
        "rut": "22.345.678-9",
        "birth_date": date(1975, 11, 30),
        "gender": "M",
        "information": {
            "address": "Recoleta 789, Recoleta",
            "phone": "+56 9 2345 6701",
            "emergency_contact": "Maria García - +56 9 9876 5432",
            "insurance": "Isapre Consalud",
            "blood_type": "O-",
            "allergies": [],
            "medical_history": "Hernia repair 2018"
        }
    },
    # Test Case 13: Three-word last name
    {
        "medical_identifier": "P013",
        "first_name": "Francisco",
        "last_name": "Van Der Berg",
        "rut": "23.456.789-0",
        "birth_date": date(1968, 7, 14),
        "gender": "M",
        "information": {
            "address": "Kennedy 4500, Vitacura",
            "phone": "+56 9 3456 7012",
            "emergency_contact": "Helena Van Der Berg - +56 9 8765 4321",
            "insurance": "Isapre Cruz Blanca",
            "blood_type": "A+",
            "allergies": ["Penicillin"],
            "medical_history": "Bypass surgery 2020"
        }
    },
    # Test Case 14: Partial name match test
    {
        "medical_identifier": "P014",
        "first_name": "Gabriela",
        "last_name": "Garcés",
        "rut": "24.567.890-1",
        "birth_date": date(1991, 3, 8),
        "gender": "F",
        "information": {
            "address": "Independencia 1500, Independencia",
            "phone": "+56 9 4567 8012",
            "emergency_contact": "Pablo Garcés - +56 9 7654 3210",
            "insurance": "FONASA",
            "blood_type": "AB+",
            "allergies": ["Eggs"],
            "medical_history": "Food allergies"
        }
    },
    # Test Case 15: Another common name "Jose"
    {
        "medical_identifier": "P015",
        "first_name": "Jose",
        "last_name": "Ramírez",
        "rut": "25.678.901-2",
        "birth_date": date(1980, 10, 25),
        "gender": "M",
        "information": {
            "address": "Miraflores 2100, Santiago",
            "phone": "+56 9 5678 9023",
            "emergency_contact": "Silvia Ramírez - +56 9 6543 2109",
            "insurance": "Isapre Banmédica",
            "blood_type": "O+",
            "allergies": [],
            "medical_history": "Arthritis"
        }
    }
]

SAMPLE_BEDS = [
    # Regular numbered rooms (floor 1)
    {"room": "101", "active": True, "available": True},
    {"room": "102", "active": True, "available": True},
    {"room": "103", "active": True, "available": False},
    {"room": "105", "active": True, "available": True},
    
    # Regular numbered rooms (floor 2)
    {"room": "201", "active": True, "available": True},
    {"room": "202", "active": True, "available": True},
    {"room": "203", "active": False, "available": False},  # Out of service
    {"room": "210", "active": True, "available": True},
    
    # Rooms with 'r' prefix (Rehabilitation wing)
    {"room": "r101", "active": True, "available": True},
    {"room": "r102", "active": True, "available": False},
    {"room": "r103", "active": True, "available": True},
    {"room": "r105", "active": True, "available": True},
    {"room": "r201", "active": True, "available": True},
    {"room": "r202", "active": True, "available": True},
    
    # Rooms with 'g' prefix (General wing)
    {"room": "g101", "active": True, "available": True},
    {"room": "g102", "active": True, "available": True},
    {"room": "g201", "active": True, "available": True},
    {"room": "g324", "active": True, "available": True},
    {"room": "g325", "active": True, "available": False},
    {"room": "g326", "active": True, "available": True},
    
    # ICU rooms
    {"room": "ICU-1", "active": True, "available": True},
    {"room": "ICU-2", "active": True, "available": False},
    {"room": "ICU-3", "active": True, "available": True},
    
    # Emergency rooms
    {"room": "ER-1", "active": True, "available": True},
    {"room": "ER-2", "active": True, "available": True},
    
    # Maternity rooms
    {"room": "MAT-101", "active": True, "available": True},
    {"room": "MAT-102", "active": True, "available": True},
]

SAMPLE_DOCUMENTS = [
    {
        "document_type": "medical_report",
        "file_url": "https://storage.example.com/patients/P001/medical_report_001.pdf"
    },
    {
        "document_type": "lab_result",
        "file_url": "https://storage.example.com/patients/P001/lab_results_2024_01.pdf"
    },
    {
        "document_type": "imaging",
        "file_url": "https://storage.example.com/patients/P002/xray_chest_2024_01.jpg"
    },
    {
        "document_type": "prescription",
        "file_url": "https://storage.example.com/patients/P002/prescription_2024_01.pdf"
    }
]

SAMPLE_EPISODE_DOCUMENTS = [
    {
        "document_type": "medical_report",
        "file_url": "https://storage.example.com/episodes/E001/admission_report.pdf"
    },
    {
        "document_type": "lab_result",
        "file_url": "https://storage.example.com/episodes/E001/blood_work.pdf"
    },
    {
        "document_type": "treatment_plan",
        "file_url": "https://storage.example.com/episodes/E001/treatment_plan.pdf"
    }
]

SAMPLE_EPISODE_INFO = [
    {
        "info_type": "diagnosis",
        "title": "Primary Diagnosis",
        "value": {
            "condition": "Acute Myocardial Infarction",
            "severity": "Moderate",
            "confirmation_date": "2024-01-15T10:30:00Z"
        }
    },
    {
        "info_type": "medication",
        "title": "Current Medications",
        "value": {
            "medications": [
                {"name": "Aspirin", "dosage": "100mg", "frequency": "daily"},
                {"name": "Clopidogrel", "dosage": "75mg", "frequency": "daily"},
                {"name": "Atorvastatin", "dosage": "20mg", "frequency": "daily"}
            ]
        }
    },
    {
        "info_type": "vital_signs",
        "title": "Latest Vital Signs",
        "value": {
            "blood_pressure": "130/85",
            "heart_rate": "78 bpm",
            "temperature": "36.8°C",
            "oxygen_saturation": "97%",
            "recorded_at": "2024-01-15T14:30:00Z"
        }
    }
]

SAMPLE_TASKS = [
    {
        "title": "Contact Family Member",
        "description": "Call emergency contact to inform about patient admission and current status",
        "priority": 5,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 30, "Admin Staff", "Attempting to reach family member"),
            (TaskStatus.COMPLETED, 45, "Admin Staff", "Successfully contacted family, they will visit tomorrow")
        ]
    },
    {
        "title": "Verify Insurance Coverage",
        "description": "Check patient's insurance coverage and confirm hospitalization authorization",
        "priority": 4,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 60, "Insurance Coordinator", "Contacting insurance provider"),
            (TaskStatus.COMPLETED, 180, "Insurance Coordinator", "Coverage verified, all procedures authorized")
        ]
    },
    {
        "title": "Obtain Consent Form - Procedure Authorization",
        "description": "Have patient sign informed consent form for scheduled procedures",
        "priority": 5,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 120, "Nurse Coordinator", "Explaining procedures to patient"),
            (TaskStatus.COMPLETED, 135, "Nurse Coordinator", "Form signed and filed in patient record")
        ]
    },
    {
        "title": "Social Work Evaluation",
        "description": "Complete social work assessment to determine post-discharge needs and support",
        "priority": 3,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 240, "Social Worker", "Interview with patient in progress"),
            (TaskStatus.COMPLETED, 300, "Social Worker", "Assessment complete, report filed")
        ]
    },
    {
        "title": "Verify Outstanding Payments",
        "description": "Review patient account and confirm any pending payments from previous visits",
        "priority": 2,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 90, "Billing Department", "Reviewing payment history")
        ]
    },
    {
        "title": "Room Assignment Confirmation",
        "description": "Confirm room assignment and notify housekeeping for preparation",
        "priority": 4,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created")
        ]
    },
    {
        "title": "Request Medical Records Transfer",
        "description": "Request medical records from patient's primary care physician",
        "priority": 3,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.CANCELLED, 60, "Records Dept", "Patient brought complete medical history with them")
        ]
    },
    {
        "title": "Schedule Post-Discharge Follow-up",
        "description": "Coordinate follow-up appointment with specialist after discharge",
        "priority": 2,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 200, "Scheduling Coordinator", "Checking specialist availability")
        ]
    },
    {
        "title": "Complete Admission Paperwork",
        "description": "Finalize all required admission forms and documentation",
        "priority": 5,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 15, "Admissions Office", "Processing admission forms"),
            (TaskStatus.COMPLETED, 40, "Admissions Office", "All paperwork completed and filed")
        ]
    },
    {
        "title": "Dietary Restrictions Update",
        "description": "Update patient dietary requirements in hospital meal system",
        "priority": 3,
        "status_progression": [
            (TaskStatus.PENDING, 0, None, "Task created"),
            (TaskStatus.IN_PROGRESS, 50, "Nutrition Services", "Entering dietary preferences"),
            (TaskStatus.COMPLETED, 55, "Nutrition Services", "Dietary profile updated in system")
        ]
    }
]


async def create_tables(engine):
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(engine):
    """Drop all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def reset_database(engine):
    """Reset the database by dropping and recreating all tables."""
    print("Resetting database...")
    await drop_tables(engine)
    await create_tables(engine)
    print("Database reset complete.")


async def seed_patients(session: AsyncSession) -> List[Patient]:
    """Create sample patients with their information."""
    patients = []

    for patient_data in SAMPLE_PATIENTS:
        # Create patient
        patient = Patient(
            medical_identifier=patient_data["medical_identifier"],
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            rut=patient_data["rut"],
            birth_date=patient_data["birth_date"],
            gender=patient_data["gender"]
        )

        session.add(patient)
        await session.flush()  # Get the patient ID

        # Create patient information
        patient_info = PatientInformation(
            patient_id=patient.id,
            information=patient_data["information"]
        )
        session.add(patient_info)

        # Create some patient documents
        for doc_data in random.sample(SAMPLE_DOCUMENTS, random.randint(1, 3)):
            if random.choice([True, False]):  # Randomly assign documents to some patients
                patient_doc = PatientDocument(
                    patient_id=patient.id,
                    document_type=DocumentType(doc_data["document_type"]),
                    file_url=doc_data["file_url"]
                )
                session.add(patient_doc)

        patients.append(patient)
        print(f"Created patient: {patient.first_name} {patient.last_name} (ID: {patient.medical_identifier})")

    await session.commit()
    return patients


async def seed_beds(session: AsyncSession) -> List[Bed]:
    """Create sample beds."""
    beds = []

    for bed_data in SAMPLE_BEDS:
        bed = Bed(
            room=bed_data["room"],
            active=bed_data["active"],
            available=bed_data["available"]
        )
        session.add(bed)
        beds.append(bed)
        print(f"Created bed: Room {bed_data['room']} (Active: {bed_data['active']}, Available: {bed_data['available']})")

    await session.commit()
    return beds


async def seed_clinical_episodes(session: AsyncSession, patients: List[Patient], beds: List[Bed]) -> List[ClinicalEpisode]:
    """Create sample clinical episodes with comprehensive bed assignments for testing."""
    episodes = []
    statuses = [EpisodeStatus.ACTIVE, EpisodeStatus.DISCHARGED, EpisodeStatus.TRANSFERRED]

    # Get available beds only for active episodes
    available_beds = [bed for bed in beds if bed.available and bed.active]
    bed_index = 0

    # Ensure every patient gets at least one episode
    for i, patient in enumerate(patients):
        # First 10 patients get active episodes with beds for better testing
        if i < 10:
            # Assign bed sequentially to ensure diverse room assignments
            bed = available_beds[bed_index % len(available_beds)] if available_beds else None
            bed_index += 1
            
            # Admission date (stagger them over last 30 days)
            admission_date = datetime.now() - timedelta(days=i * 2)

            episode = ClinicalEpisode(
                patient_id=patient.id,
                status=EpisodeStatus.ACTIVE,
                bed_id=bed.id if bed else None,
                admission_at=admission_date,
                discharge_at=None,
                expected_discharge=date.today() + timedelta(days=random.randint(3, 14))
            )

            session.add(episode)
            await session.flush()

            # Create episode documents
            num_docs = min(random.randint(1, 2), len(SAMPLE_EPISODE_DOCUMENTS))
            for doc_data in random.sample(SAMPLE_EPISODE_DOCUMENTS, num_docs):
                episode_doc = EpisodeDocument(
                    episode_id=episode.id,
                    document_type=EpisodeDocumentType(doc_data["document_type"]),
                    file_url=doc_data["file_url"]
                )
                session.add(episode_doc)

            # Create episode information records
            num_info = min(random.randint(1, 2), len(SAMPLE_EPISODE_INFO))
            for info_data in random.sample(SAMPLE_EPISODE_INFO, num_info):
                episode_info = ClinicalEpisodeInformation(
                    episode_id=episode.id,
                    info_type=EpisodeInfoType(info_data["info_type"]),
                    title=info_data["title"],
                    value=info_data["value"]
                )
                session.add(episode_info)

            episodes.append(episode)
            bed_info = f"Room {bed.room}" if bed else "No bed assigned"
            print(f"Created ACTIVE episode for {patient.first_name} {patient.last_name}: {bed_info}")
        
        # Remaining patients get a mix of statuses
        else:
            num_episodes = 1  # One episode per remaining patient
            
            for j in range(num_episodes):
                # Random bed assignment (can be None for discharged)
                status = random.choice(statuses)
                bed = None
                
                if status == EpisodeStatus.ACTIVE and available_beds:
                    bed = available_beds[bed_index % len(available_beds)]
                    bed_index += 1
                elif status != EpisodeStatus.ACTIVE:
                    # Discharged/transferred patients might have had a bed
                    bed = random.choice(beds) if random.random() > 0.3 else None
                
                # Admission date (random within last 60 days for discharged)
                admission_date = datetime.now() - timedelta(days=random.randint(1, 60))
                
                episode = ClinicalEpisode(
                    patient_id=patient.id,
                    status=status,
                    bed_id=bed.id if bed else None,
                    admission_at=admission_date,
                    discharge_at=admission_date + timedelta(days=random.randint(3, 21)) if status != EpisodeStatus.ACTIVE else None,
                    expected_discharge=date.today() + timedelta(days=random.randint(1, 10)) if status == EpisodeStatus.ACTIVE else None
                )
                
                session.add(episode)
                await session.flush()
                
                # Create episode documents (fewer for discharged)
                if random.random() > 0.3:
                    num_docs = min(random.randint(1, 2), len(SAMPLE_EPISODE_DOCUMENTS))
                    for doc_data in random.sample(SAMPLE_EPISODE_DOCUMENTS, num_docs):
                        episode_doc = EpisodeDocument(
                            episode_id=episode.id,
                            document_type=EpisodeDocumentType(doc_data["document_type"]),
                            file_url=doc_data["file_url"]
                        )
                        session.add(episode_doc)
                
                # Create episode information records
                if random.random() > 0.4:
                    num_info = min(random.randint(1, 2), len(SAMPLE_EPISODE_INFO))
                    for info_data in random.sample(SAMPLE_EPISODE_INFO, num_info):
                        episode_info = ClinicalEpisodeInformation(
                            episode_id=episode.id,
                            info_type=EpisodeInfoType(info_data["info_type"]),
                            title=info_data["title"],
                            value=info_data["value"]
                        )
                        session.add(episode_info)
                
                episodes.append(episode)
                status_str = status.value.upper()
                bed_info = f"Room {bed.room}" if bed else "No bed"
                print(f"Created {status_str} episode for {patient.first_name} {patient.last_name}: {bed_info}")

    await session.commit()
    print(f"\nEpisode Status Summary:")
    print(f"  Active: {len([e for e in episodes if e.status == EpisodeStatus.ACTIVE])}")
    print(f"  Discharged: {len([e for e in episodes if e.status == EpisodeStatus.DISCHARGED])}")
    print(f"  Transferred: {len([e for e in episodes if e.status == EpisodeStatus.TRANSFERRED])}")
    print(f"  With beds: {len([e for e in episodes if e.bed_id is not None])}")
    print(f"  Without beds: {len([e for e in episodes if e.bed_id is None])}")
    
    return episodes


async def seed_tasks(session: AsyncSession, episodes: List[ClinicalEpisode]) -> List[TaskInstance]:
    """Create sample tasks with status history for clinical episodes."""
    tasks = []
    
    # Create tasks for active episodes only
    active_episodes = [ep for ep in episodes if ep.status == EpisodeStatus.ACTIVE]
    
    if not active_episodes:
        print("No active episodes found, skipping task creation")
        return tasks
    
    # Pick the first active episode for comprehensive task demonstration
    demo_episode = active_episodes[0]
    
    print(f"\nCreating tasks for episode {demo_episode.id}...")
    
    for task_data in SAMPLE_TASKS:
        # Calculate due date (1-7 days from episode admission)
        due_date = (demo_episode.admission_at + timedelta(days=random.randint(1, 7))).date()
        
        # Get the status progression
        status_progression = task_data["status_progression"]
        
        # The final status is the last one in the progression
        final_status = status_progression[-1][0]
        
        # Create the task instance
        task = TaskInstance(
            episode_id=demo_episode.id,
            title=task_data["title"],
            description=task_data["description"],
            due_date=due_date,
            priority=task_data["priority"],
            status=final_status
        )
        
        session.add(task)
        await session.flush()  # Get the task ID
        
        # Create status history for each transition
        for idx, (status, minutes_offset, changed_by, notes) in enumerate(status_progression):
            # Calculate when this status change occurred
            changed_at = demo_episode.admission_at + timedelta(minutes=minutes_offset)
            
            # Determine old_status (None for the first status, previous status for subsequent ones)
            old_status = None if idx == 0 else status_progression[idx - 1][0]
            
            status_history = TaskStatusHistory(
                task_id=task.id,
                old_status=old_status,
                new_status=status,
                changed_at=changed_at,
                changed_by=changed_by,
                notes=notes
            )
            
            session.add(status_history)
        
        tasks.append(task)
        print(f"  - Created task: '{task_data['title']}' with {len(status_progression)} status changes")
    
    # Add a few random tasks to other active episodes
    for episode in active_episodes[1:3]:  # Add to 2 more episodes if they exist
        num_tasks = random.randint(2, 4)
        for task_data in random.sample(SAMPLE_TASKS, min(num_tasks, len(SAMPLE_TASKS))):
            due_date = (episode.admission_at + timedelta(days=random.randint(1, 7))).date()
            
            # Random status for these tasks
            random_status = random.choice([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED])
            
            task = TaskInstance(
                episode_id=episode.id,
                title=task_data["title"],
                description=task_data["description"],
                due_date=due_date,
                priority=task_data["priority"],
                status=random_status
            )
            
            session.add(task)
            await session.flush()
            
            # Create initial status history
            status_history = TaskStatusHistory(
                task_id=task.id,
                old_status=None,
                new_status=random_status,
                changed_at=episode.admission_at + timedelta(minutes=random.randint(10, 120)),
                notes="Task created"
            )
            session.add(status_history)
            tasks.append(task)
    
    await session.commit()
    return tasks


async def seed_social_scores(session: AsyncSession, episodes: List[ClinicalEpisode]) -> List[SocialScoreHistory]:
    """Create sample social score history for clinical episodes."""
    scores = []
    
    # Define which episodes get multiple scores (indices 0, 2, 4, 6, 8 will have multiple scores)
    multi_score_indices = {0, 2, 4, 6, 8}
    
    print("\nCreating social score history...")
    
    for idx, episode in enumerate(episodes):
        # Base score between 1 and 15
        base_score = random.randint(1, 15)
        
        # First score - recorded at admission
        first_score = SocialScoreHistory(
            episode_id=episode.id,
            score=base_score,
            recorded_at=episode.admission_at + timedelta(hours=random.randint(1, 4)),
            recorded_by="Social Worker",
            notes="Initial social assessment"
        )
        session.add(first_score)
        scores.append(first_score)
        
        # Some episodes get additional scores at different dates
        if idx in multi_score_indices:
            # Second score - a few days later
            second_score_value = max(1, min(15, base_score + random.randint(-3, 3)))
            second_score = SocialScoreHistory(
                episode_id=episode.id,
                score=second_score_value,
                recorded_at=episode.admission_at + timedelta(days=random.randint(3, 7)),
                recorded_by="Social Worker",
                notes="Follow-up assessment"
            )
            session.add(second_score)
            scores.append(second_score)
            
            # Some get a third score
            if idx in {0, 4, 8}:
                third_score_value = max(1, min(15, second_score_value + random.randint(-2, 2)))
                third_score = SocialScoreHistory(
                    episode_id=episode.id,
                    score=third_score_value,
                    recorded_at=episode.admission_at + timedelta(days=random.randint(10, 14)),
                    recorded_by="Case Manager",
                    notes="Pre-discharge evaluation"
                )
                session.add(third_score)
                scores.append(third_score)
    
    await session.commit()
    
    # Count episodes with multiple scores
    episode_score_counts = {}
    for score in scores:
        episode_score_counts[score.episode_id] = episode_score_counts.get(score.episode_id, 0) + 1
    
    multi_score_episodes = sum(1 for count in episode_score_counts.values() if count > 1)
    print(f"Created {len(scores)} social score records for {len(episodes)} episodes")
    print(f"  Episodes with multiple scores: {multi_score_episodes}")
    
    return scores


async def main(reset: bool = False):
    """Main seeding function."""
    # Create engine
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(database_url)

    try:
        if reset:
            await reset_database(engine)

        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            print("Starting database seeding...")

            # Seed patients first (they are referenced by other tables)
            patients = await seed_patients(session)

            # Seed beds
            beds = await seed_beds(session)

            # Seed clinical episodes (references patients and beds)
            episodes = await seed_clinical_episodes(session, patients, beds)

            # Seed tasks with status history
            tasks = await seed_tasks(session, episodes)

            # Seed social score history
            social_scores = await seed_social_scores(session, episodes)

            print(f"\nSeeding complete!")
            print(f"Created {len(patients)} patients")
            print(f"Created {len(beds)} beds")
            print(f"Created {len(episodes)} clinical episodes")
            print(f"Created {len(tasks)} tasks with status history")
            print(f"Created {len(social_scores)} social score history records")

    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        await engine.dispose()


async def clear_database_only():
    """Clear the entire database by dropping all tables and recreating them empty."""
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    engine = create_async_engine(database_url)
    
    try:
        print("WARNING: This will drop all tables and recreate them empty. This is a destructive action and cannot be undone.")
        print("Are you sure you want to continue? (y/n)")
        confirmation = input()
        if confirmation != "y":
            print("Database clearing cancelled.")
            return
        
        print("Clearing database...")
        await drop_tables(engine)
        print("All tables dropped.")
        
        # Recreate empty tables
        await create_tables(engine)
        print("Empty tables recreated.")
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error during database clearing: {e}")
        raise
    finally:
        await engine.dispose()


def seed():
    """Seed the database with sample data."""
    asyncio.run(main(reset=False))

def reset():
    """Reset and seed the database."""
    asyncio.run(main(reset=True))

def clear():
    """Clear the entire database (drop all tables and recreate them empty)."""
    asyncio.run(clear_database_only())