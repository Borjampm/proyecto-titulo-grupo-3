from fastapi import APIRouter, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from fastapi import Depends
from app.deps import get_session
from sqlalchemy.orm import selectinload
from enum import Enum
from typing import Union
from uuid import UUID
from datetime import datetime

from app.models.clinical_episode import ClinicalEpisode as ClinicalEpisodeModel
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.episode_document import EpisodeDocument
from app.models.task_instance import TaskInstance
from app.models.task_status_history import TaskStatusHistory
from app.schemas.clinical_episode import (
    ClinicalEpisodeWithPatient,
    ClinicalEpisode,
    HistoryEventType,
    HistoryEvent,
    EpisodeHistory,
    PaginatedClinicalEpisodes
)



router = APIRouter(prefix="/clinical-episodes", tags=["clinical-episodes"])


def build_search_filter(search: str):
    """
    Enhanced search handling multi-word names and room numbers.
    
    Supports searching by:
    - Patient first name (partial or full)
    - Patient last name (partial or full)
    - Multi-word first names (e.g., "Maria Jose")
    - Multi-word last names (e.g., "Garcia Lopez")
    - Room number
    
    Examples:
    - "Maria" → finds first or last name containing "Maria"
    - "Maria Garcia" → finds patients with both terms in their name
    - "Garcia Lopez" → finds multi-word last names
    - "101" → finds room 101
    - "Maria 101" → finds Maria in room 101 OR anyone named "Maria" or in room "101"
    """
    if not search or not search.strip():
        return None
    
    search = search.strip()
    search_terms = search.split()
    
    # Build the concatenated full name: "FirstName LastName"
    full_name = func.concat(Patient.first_name, ' ', Patient.last_name)
    
    if len(search_terms) == 1:
        # Single term: match against any field
        term = search_terms[0]
        return or_(
            Patient.first_name.ilike(f"%{term}%"),
            Patient.last_name.ilike(f"%{term}%"),
            Bed.room.ilike(f"%{term}%")
        )
    else:
        # Multiple terms: use hybrid approach
        
        # Strategy A: Full search string matches concatenated name
        # Handles: "Maria Garcia Lopez", "Garcia Lopez", etc.
        full_name_match = full_name.ilike(f"%{search}%")
        
        # Strategy B: Each word matches somewhere in first or last name
        # Handles: "Maria Lopez", "Lopez Maria", etc.
        word_conditions = []
        for term in search_terms:
            word_conditions.append(
                or_(
                    Patient.first_name.ilike(f"%{term}%"),
                    Patient.last_name.ilike(f"%{term}%")
                )
            )
        word_match = and_(*word_conditions)
        
        # Strategy C: Entire search matches room number
        room_match = Bed.room.ilike(f"%{search}%")
        
        # Combine all strategies with OR
        return or_(
            full_name_match,   # Consecutive words in full name
            word_match,        # All words match somewhere in name
            room_match         # Or it's a room number
        )


class ClinicalEpisodeInclude(str, Enum):
    PATIENT = "patient"


@router.get("/", response_model=PaginatedClinicalEpisodes)
async def list_clinical_episodes(
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    include: ClinicalEpisodeInclude | None = None,
    session: AsyncSession = Depends(get_session)
) -> PaginatedClinicalEpisodes:
    """
    List clinical episodes with optional search and pagination.
    
    Parameters:
    - search: Search by patient name (first, last, or full name) or room number
    - page: Page number (starts at 1)
    - page_size: Number of results per page (default: 50, max: 100)
    - include: Optional "patient" to include patient details
    
    Search examples:
    - "Maria" → finds patients with "Maria" in first or last name
    - "Maria Garcia" → finds patients with both terms in their name
    - "Garcia Lopez" → finds multi-word last names
    - "101" → finds episodes in room 101
    - "Maria 101" → finds Maria OR room 101
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    # Build base query
    query = select(ClinicalEpisodeModel)
    
    # Always join Patient and Bed for search capability
    query = query.join(Patient)
    query = query.join(Bed, isouter=True)  # LEFT JOIN (episodes may not have beds)
    
    # Apply search filter if provided
    if search:
        search_filter = build_search_filter(search)
        if search_filter is not None:
            query = query.where(search_filter)
    
    # Get total count before adding ORDER BY (ordering doesn't affect count)
    # Use distinct to avoid duplicate counts from joins
    count_query = select(func.count(func.distinct(ClinicalEpisodeModel.id)))
    count_query = count_query.select_from(ClinicalEpisodeModel)
    count_query = count_query.join(Patient)
    count_query = count_query.join(Bed, isouter=True)
    if search:
        search_filter = build_search_filter(search)
        if search_filter is not None:
            count_query = count_query.where(search_filter)
    total = await session.scalar(count_query) or 0
    
    # Add relevance sorting
    if search and search.strip():
        search_term = search.strip()
        # Sort by relevance:
        # 1. Exact first name matches (case-insensitive)
        # 2. Exact last name matches
        # 3. Exact room matches
        # 4. Most recent admissions
        query = query.order_by(
            # Exact first name match gets highest priority
            (Patient.first_name.ilike(search_term)).desc(),
            # Exact last name match
            (Patient.last_name.ilike(search_term)).desc(),
            # Exact room match
            (Bed.room.ilike(search_term)).desc(),
            # Most recent admissions
            ClinicalEpisodeModel.admission_at.desc()
        )
    else:
        # Default sort when no search: most recent first
        query = query.order_by(ClinicalEpisodeModel.admission_at.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Add selectinload for patient if requested
    if include == ClinicalEpisodeInclude.PATIENT:
        query = query.options(selectinload(ClinicalEpisodeModel.patient))
    
    # Execute query
    result = await session.execute(query)
    episodes = result.scalars().unique().all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return PaginatedClinicalEpisodes(
        data=episodes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{episode_id}", response_model=Union[ClinicalEpisodeWithPatient, ClinicalEpisode])
async def get_clinical_episode(
    episode_id: UUID,
    include: ClinicalEpisodeInclude | None = None,
    session: AsyncSession = Depends(get_session)
) -> Union[ClinicalEpisodeWithPatient, ClinicalEpisode]:
    """
    Get a specific clinical episode by ID.
    
    Optionally include related patient information by passing include=patient.
    """
    if include == ClinicalEpisodeInclude.PATIENT:
        result = await session.execute(
            select(ClinicalEpisodeModel)
            .where(ClinicalEpisodeModel.id == episode_id)
            .options(selectinload(ClinicalEpisodeModel.patient))
        )
    else:
        result = await session.execute(
            select(ClinicalEpisodeModel)
            .where(ClinicalEpisodeModel.id == episode_id)
        )
    
    episode = result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Clinical episode not found")
    
    return episode


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