from fastapi import APIRouter, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.deps import get_session
from sqlalchemy.orm import selectinload
from enum import Enum
from typing import Union
from uuid import UUID
from datetime import datetime

from app.models.clinical_episode import ClinicalEpisode as ClinicalEpisodeModel
from app.models.episode_document import EpisodeDocument
from app.models.task_instance import TaskInstance
from app.models.task_status_history import TaskStatusHistory
from app.schemas.clinical_episode import (
    ClinicalEpisodeWithPatient,
    ClinicalEpisode,
    HistoryEventType,
    HistoryEvent,
    EpisodeHistory
)



router = APIRouter(prefix="/clinical-episodes", tags=["clinical-episodes"])


class ClinicalEpisodeInclude(str, Enum):
    PATIENT = "patient"


@router.get("/", response_model=Union[list[ClinicalEpisodeWithPatient], list[ClinicalEpisode]])
async def list_clinical_episodes(
    include: ClinicalEpisodeInclude | None = None,
    session: AsyncSession = Depends(get_session)
) -> Union[list[ClinicalEpisodeWithPatient], list[ClinicalEpisode]]:
    if include == ClinicalEpisodeInclude.PATIENT:
        clinical_episodes = select(ClinicalEpisodeModel)
        clinical_episodes_with_patient_info = clinical_episodes.options(selectinload(ClinicalEpisodeModel.patient))
        result = await session.execute(clinical_episodes_with_patient_info)
    else:
        clinical_episodes = select(ClinicalEpisodeModel)
        result = await session.execute(clinical_episodes)
    return result.scalars().all()


@router.get("/{episode_id}/history", response_model=EpisodeHistory)
async def get_episode_history(
    episode_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> EpisodeHistory:
    """
    Get the history of events for a clinical episode.
    
    Returns a chronologically sorted list of events including:
    - Patient admission
    - Documents uploaded
    - Tasks created
    - Task status updates (complete history of all status changes)
    """
    # Verify episode exists
    episode_result = await session.execute(
        select(ClinicalEpisodeModel).where(ClinicalEpisodeModel.id == episode_id)
    )
    episode = episode_result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Clinical episode not found")
    
    events: list[HistoryEvent] = []
    
    # 1. Patient admission event
    events.append(HistoryEvent(
        event_type=HistoryEventType.PATIENT_ADMISSION,
        event_date=episode.admission_at,
        description="Patient admitted to clinical episode",
        metadata={
            "episode_id": str(episode.id),
            "patient_id": str(episode.patient_id),
            "bed_id": str(episode.bed_id) if episode.bed_id else None
        }
    ))
    
    # 2. Document upload events
    documents_result = await session.execute(
        select(EpisodeDocument).where(EpisodeDocument.episode_id == episode_id)
    )
    documents = documents_result.scalars().all()
    
    for doc in documents:
        # Extract filename from file_url as a fallback for document name
        filename = doc.file_url.split("/")[-1] if doc.file_url else "Unknown document"
        
        events.append(HistoryEvent(
            event_type=HistoryEventType.DOCUMENT_UPLOADED,
            event_date=doc.created_at,
            description=f"Document uploaded: {filename}",
            metadata={
                "document_id": str(doc.id),
                "document_type": doc.document_type.value,
                "file_url": doc.file_url,
                "filename": filename
            }
        ))
    
    # 3. Task creation events
    tasks_result = await session.execute(
        select(TaskInstance).where(TaskInstance.episode_id == episode_id)
    )
    tasks = tasks_result.scalars().all()
    
    # Create a map of task_id to task for quick lookup
    task_map = {str(task.id): task for task in tasks}
    
    for task in tasks:
        # Task creation event
        events.append(HistoryEvent(
            event_type=HistoryEventType.TASK_CREATED,
            event_date=task.created_at,
            description=f"Task created: {task.title}",
            metadata={
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "initial_status": task.status.value,
                "priority": task.priority
            }
        ))
    
    # 4. Task status change events from history table
    # Get all task IDs for this episode
    task_ids = [task.id for task in tasks]
    
    if task_ids:
        status_history_result = await session.execute(
            select(TaskStatusHistory)
            .where(TaskStatusHistory.task_id.in_(task_ids))
            .order_by(TaskStatusHistory.changed_at)
        )
        status_changes = status_history_result.scalars().all()
        
        for status_change in status_changes:
            task = task_map.get(str(status_change.task_id))
            task_title = task.title if task else "Unknown Task"
            
            # Build description based on old and new status
            if status_change.old_status is None:
                description = f"Task '{task_title}' initialized with status: {status_change.new_status.value}"
            else:
                description = f"Task '{task_title}' status changed from {status_change.old_status.value} to {status_change.new_status.value}"
            
            events.append(HistoryEvent(
                event_type=HistoryEventType.TASK_UPDATED,
                event_date=status_change.changed_at,
                description=description,
                metadata={
                    "task_id": str(status_change.task_id),
                    "task_title": task_title,
                    "old_status": status_change.old_status.value if status_change.old_status else None,
                    "new_status": status_change.new_status.value,
                    "changed_by": status_change.changed_by,
                    "notes": status_change.notes
                }
            ))
    
    # Sort events by date
    events.sort(key=lambda x: x.event_date)
    
    return EpisodeHistory(
        episode_id=episode_id,
        events=events
    )