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


# Sample data
SAMPLE_PATIENTS = [
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
    {
        "medical_identifier": "P004",
        "first_name": "Diego",
        "last_name": "Martínez",
        "rut": "14.567.890-1",
        "birth_date": date(1965, 1, 30),
        "gender": "M",
        "information": {
            "address": "Los Conquistadores 101, Las Condes",
            "phone": "+56 9 4567 8901",
            "emergency_contact": "Carmen Martínez - +56 9 7654 3210",
            "insurance": "Isapre Cruz Blanca",
            "blood_type": "AB+",
            "allergies": ["Latex"],
            "medical_history": "COPD, Osteoarthritis"
        }
    }
]

SAMPLE_BEDS = [
    {"room": "101", "active": True, "available": True},
    {"room": "102", "active": True, "available": True},
    {"room": "103", "active": True, "available": False},
    {"room": "201", "active": True, "available": True},
    {"room": "202", "active": True, "available": True},
    {"room": "203", "active": False, "available": False},  # Out of service
    {"room": "ICU-1", "active": True, "available": True},
    {"room": "ICU-2", "active": True, "available": False},
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
    """Create sample clinical episodes."""
    episodes = []
    statuses = [EpisodeStatus.ACTIVE, EpisodeStatus.DISCHARGED, EpisodeStatus.TRANSFERRED]

    for i, patient in enumerate(patients):
        # Create 1-2 episodes per patient
        num_episodes = random.randint(1, 2)

        for j in range(num_episodes):
            # Random bed assignment (can be None)
            bed = random.choice(beds) if random.choice([True, False]) else None

            # Random status
            status = random.choice(statuses)

            # Admission date (random within last 30 days)
            admission_date = datetime.now() - timedelta(days=random.randint(1, 30))

            episode = ClinicalEpisode(
                patient_id=patient.id,
                status=status,
                bed_id=bed.id if bed else None,
                admission_at=admission_date,
                discharge_at=admission_date + timedelta(days=random.randint(3, 14)) if status != EpisodeStatus.ACTIVE else None,
                expected_discharge=date.today() + timedelta(days=random.randint(1, 7)) if status == EpisodeStatus.ACTIVE else None
            )

            session.add(episode)
            await session.flush()

            # Create episode documents
            num_docs = min(random.randint(1, 3), len(SAMPLE_EPISODE_DOCUMENTS))
            for doc_data in random.sample(SAMPLE_EPISODE_DOCUMENTS, num_docs):
                episode_doc = EpisodeDocument(
                    episode_id=episode.id,
                    document_type=EpisodeDocumentType(doc_data["document_type"]),
                    file_url=doc_data["file_url"]
                )
                session.add(episode_doc)

            # Create episode information records
            num_info = min(random.randint(2, 3), len(SAMPLE_EPISODE_INFO))
            for info_data in random.sample(SAMPLE_EPISODE_INFO, num_info):
                episode_info = ClinicalEpisodeInformation(
                    episode_id=episode.id,
                    info_type=EpisodeInfoType(info_data["info_type"]),
                    title=info_data["title"],
                    value=info_data["value"]
                )
                session.add(episode_info)

            episodes.append(episode)
            status_str = "Active" if status == EpisodeStatus.ACTIVE else "Discharged" if status == EpisodeStatus.DISCHARGED else "Transferred"
            bed_info = f"Bed: {bed.room}" if bed else "No bed assigned"
            print(f"Created episode for {patient.first_name} {patient.last_name}: {status_str}, {bed_info}")

    await session.commit()
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


async def main(reset: bool = False):
    """Main seeding function."""
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL)

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

            print(f"\nSeeding complete!")
            print(f"Created {len(patients)} patients")
            print(f"Created {len(beds)} beds")
            print(f"Created {len(episodes)} clinical episodes")
            print(f"Created {len(tasks)} tasks with status history")

    except Exception as e:
        print(f"Error during seeding: {e}")
        raise
    finally:
        await engine.dispose()


async def clear_database_only():
    """Clear the entire database by dropping all tables and recreating them empty."""
    engine = create_async_engine(settings.DATABASE_URL)
    
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