"""
Test fixtures and helpers for creating test data.
"""
import uuid
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.models.clinical_episode import ClinicalEpisode, EpisodeStatus
from app.models.bed import Bed
from app.models.task_definition import TaskDefinition
from app.models.task_instance import TaskInstance, TaskStatus


async def create_test_patient(
    session: AsyncSession,
    medical_identifier: str = "MED001",
    first_name: str = "John",
    last_name: str = "Doe",
    rut: str = "12345678-9",
    birth_date: date = date(1990, 1, 15),
    gender: str = "M"
) -> Patient:
    """Create a test patient."""
    patient = Patient(
        medical_identifier=medical_identifier,
        first_name=first_name,
        last_name=last_name,
        rut=rut,
        birth_date=birth_date,
        gender=gender
    )
    session.add(patient)
    await session.flush()
    await session.refresh(patient)
    return patient


async def create_test_bed(
    session: AsyncSession,
    room: str = "101",
    active: bool = True,
    available: bool = True
) -> Bed:
    """Create a test bed."""
    bed = Bed(
        room=room,
        active=active,
        available=available
    )
    session.add(bed)
    await session.flush()
    await session.refresh(bed)
    return bed


async def create_test_clinical_episode(
    session: AsyncSession,
    patient_id: uuid.UUID,
    bed_id: uuid.UUID | None = None,
    status: EpisodeStatus = EpisodeStatus.ACTIVE,
    admission_at: datetime | None = None
) -> ClinicalEpisode:
    """Create a test clinical episode."""
    from datetime import timezone
    episode = ClinicalEpisode(
        patient_id=patient_id,
        bed_id=bed_id,
        status=status,
        admission_at=admission_at or datetime.now(timezone.utc)
    )
    session.add(episode)
    await session.flush()
    await session.refresh(episode)
    return episode


async def create_test_task_definition(
    session: AsyncSession,
    title: str = "Test Task",
    description: str = "Test Description",
    estimate_duration: int = 30,
    default_priority: int = 1,
    active: bool = True
) -> TaskDefinition:
    """Create a test task definition."""
    task_def = TaskDefinition(
        title=title,
        description=description,
        estimate_duration=estimate_duration,
        default_priority=default_priority,
        active=active
    )
    session.add(task_def)
    await session.flush()
    await session.refresh(task_def)
    return task_def


async def create_test_task_instance(
    session: AsyncSession,
    episode_id: uuid.UUID,
    title: str = "Test Task",
    description: str | None = "Test Description",
    due_date: date | None = None,
    priority: int = 1,
    status: TaskStatus = TaskStatus.PENDING
) -> TaskInstance:
    """Create a test task instance."""
    task = TaskInstance(
        episode_id=episode_id,
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        status=status
    )
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task

