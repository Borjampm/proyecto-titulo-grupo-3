from fastapi import APIRouter, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from fastapi import Depends
from app.deps import get_session
from sqlalchemy.orm import selectinload
from typing import Union
from uuid import UUID
from datetime import datetime

from app.models.clinical_episode import ClinicalEpisode as ClinicalEpisodeModel, EpisodeStatus
from app.models.patient import Patient
from app.models.bed import Bed
from app.models.episode_document import EpisodeDocument
from app.models.task_instance import TaskInstance
from app.models.task_status_history import TaskStatusHistory
from app.models.social_score_history import SocialScoreHistory
from app.models.alert import Alert as AlertModel
from app.schemas.clinical_episode import (
    ClinicalEpisodeWithPatient,
    ClinicalEpisodeWithIncludes,
    ClinicalEpisode,
    HistoryEventType,
    HistoryEvent,
    EpisodeHistory,
    PaginatedClinicalEpisodes,
    ReferralCreate,
    ReferralResponse
)
from app.schemas.social_score_history import SocialScoreHistory as SocialScoreHistorySchema



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


def parse_includes(include: str | None) -> set[str]:
    """Parse comma-separated include parameter into a set of include values."""
    if not include:
        return set()
    return {i.strip().lower() for i in include.split(",") if i.strip()}


@router.get("/", response_model=PaginatedClinicalEpisodes)
async def list_clinical_episodes(
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
    include: str | None = None,
    session: AsyncSession = Depends(get_session)
) -> PaginatedClinicalEpisodes:
    """
    List clinical episodes with optional search and pagination.
    
    Parameters:
    - search: Search by patient name (first, last, or full name) or room number
    - page: Page number (starts at 1)
    - page_size: Number of results per page (default: 50, max: 100)
    - include: Comma-separated list of includes: "patient", "social_score" (e.g., "patient,social_score")
    
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
    
    # Parse includes
    includes = parse_includes(include)
    include_patient = "patient" in includes
    include_social_score = "social_score" in includes
    
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
    if include_patient:
        query = query.options(selectinload(ClinicalEpisodeModel.patient))
    
    # Execute query
    result = await session.execute(query)
    episodes = result.scalars().unique().all()
    
    # If social_score is requested, fetch the most recent score for each episode
    if include_social_score and episodes:
        episode_ids = [ep.id for ep in episodes]
        
        # Subquery to get the most recent score per episode
        latest_score_subquery = (
            select(
                SocialScoreHistory.episode_id,
                func.max(SocialScoreHistory.recorded_at).label("max_recorded_at")
            )
            .where(SocialScoreHistory.episode_id.in_(episode_ids))
            .group_by(SocialScoreHistory.episode_id)
            .subquery()
        )
        
        # Get the actual score records
        scores_query = (
            select(SocialScoreHistory)
            .join(
                latest_score_subquery,
                and_(
                    SocialScoreHistory.episode_id == latest_score_subquery.c.episode_id,
                    SocialScoreHistory.recorded_at == latest_score_subquery.c.max_recorded_at
                )
            )
        )
        scores_result = await session.execute(scores_query)
        scores = scores_result.scalars().all()
        
        # Create a map of episode_id to latest score
        score_map = {score.episode_id: score for score in scores}
        
        # Build response with includes
        response_data = []
        for episode in episodes:
            episode_dict = {
                "id": episode.id,
                "patient_id": episode.patient_id,
                "discharge_at": episode.discharge_at,
                "expected_discharge": episode.expected_discharge,
                "status": episode.status,
                "bed_id": episode.bed_id,
                "admission_at": episode.admission_at,
                "episode_identifier": episode.episode_identifier,
                "grd_expected_days": episode.grd_expected_days,
                "grd_name": episode.grd_name,
                "created_at": episode.created_at,
                "updated_at": episode.updated_at,
                "patient": episode.patient if include_patient else None,
                "latest_social_score": score_map.get(episode.id)
            }
            response_data.append(ClinicalEpisodeWithIncludes(**episode_dict))
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return PaginatedClinicalEpisodes(
            data=response_data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return PaginatedClinicalEpisodes(
        data=episodes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/referrals", response_model=ReferralResponse)
async def create_referral(
    referral: ReferralCreate,
    session: AsyncSession = Depends(get_session)
) -> ReferralResponse:
    """
    Create a new referral from clinical services to stay management.
    
    This endpoint creates a new clinical episode for an existing patient.
    """
    patient_result = await session.execute(
        select(Patient).where(Patient.id == referral.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    episode = ClinicalEpisodeModel(
        patient_id=referral.patient_id,
        admission_at=referral.admission_at,
        status=EpisodeStatus.ACTIVE
    )
    
    session.add(episode)
    await session.flush()
    await session.refresh(episode, ['patient'])
    
    # TODO: Create alert for management team when alerts are implemented :$
    
    return episode


@router.patch("/{episode_id}/close", response_model=ClinicalEpisode)
async def close_episode(
    episode_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> ClinicalEpisode:
    """
    Close a clinical episode (mark as discharged).
    
    This sets the episode status to DISCHARGED and sets the discharge_at timestamp.
    """
    result = await session.execute(
        select(ClinicalEpisodeModel).where(ClinicalEpisodeModel.id == episode_id)
    )
    episode = result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Clinical episode not found")
    
    if episode.status == EpisodeStatus.DISCHARGED:
        raise HTTPException(status_code=400, detail="Episode is already closed")
    
    episode.status = EpisodeStatus.DISCHARGED
    episode.discharge_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(episode)
    
    return episode


# IMPORTANTE: Esto siempre tiene que ir al final de los endpoints porque si no una ruta se puede mappear a una ID de episodio.
@router.get("/{episode_id}", response_model=Union[ClinicalEpisodeWithIncludes, ClinicalEpisodeWithPatient, ClinicalEpisode])
async def get_clinical_episode(
    episode_id: UUID,
    include: str | None = None,
    session: AsyncSession = Depends(get_session)
) -> Union[ClinicalEpisodeWithIncludes, ClinicalEpisodeWithPatient, ClinicalEpisode]:
    """
    Get a specific clinical episode by ID.
    
    Optionally include related information by passing comma-separated includes:
    - include=patient - Include patient details
    - include=social_score - Include the most recent social score
    - include=patient,social_score - Include both
    """
    # Parse includes
    includes = parse_includes(include)
    include_patient = "patient" in includes
    include_social_score = "social_score" in includes
    
    # Build query
    query = select(ClinicalEpisodeModel).where(ClinicalEpisodeModel.id == episode_id)
    
    if include_patient:
        query = query.options(selectinload(ClinicalEpisodeModel.patient))
    
    result = await session.execute(query)
    episode = result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Clinical episode not found")
    
    # If social_score is requested, fetch the most recent score
    if include_social_score:
        score_query = (
            select(SocialScoreHistory)
            .where(SocialScoreHistory.episode_id == episode_id)
            .order_by(SocialScoreHistory.recorded_at.desc())
            .limit(1)
        )
        score_result = await session.execute(score_query)
        latest_score = score_result.scalar_one_or_none()
        
        # Build response with includes
        episode_dict = {
            "id": episode.id,
            "patient_id": episode.patient_id,
            "discharge_at": episode.discharge_at,
            "expected_discharge": episode.expected_discharge,
            "status": episode.status,
            "bed_id": episode.bed_id,
            "admission_at": episode.admission_at,
            "episode_identifier": episode.episode_identifier,
            "grd_expected_days": episode.grd_expected_days,
            "grd_name": episode.grd_name,
            "created_at": episode.created_at,
            "updated_at": episode.updated_at,
            "patient": episode.patient if include_patient else None,
            "latest_social_score": latest_score
        }
        return ClinicalEpisodeWithIncludes(**episode_dict)
    
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
    - Social score recordings (all scores with dates)
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
        select(TaskInstance)
        .options(selectinload(TaskInstance.assigned_worker))
        .where(TaskInstance.episode_id == episode_id)
    )
    tasks = tasks_result.scalars().all()
    
    # Create a map of task_id to task for quick lookup
    task_map = {str(task.id): task for task in tasks}
    
    for task in tasks:
        # Get assigned worker name
        assigned_worker_name = task.assigned_worker.name if task.assigned_worker else None
        
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
                "priority": task.priority,
                "assigned_worker_name": assigned_worker_name
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
            # Get assigned worker name from the task
            assigned_worker_name = task.assigned_worker.name if task and task.assigned_worker else None
            
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
                    "notes": status_change.notes,
                    "assigned_worker_name": assigned_worker_name
                }
            ))
    
    # 5. Social score recording events (only show if there's an actual score)
    social_scores_result = await session.execute(
        select(SocialScoreHistory)
        .where(SocialScoreHistory.episode_id == episode_id)
        .order_by(SocialScoreHistory.recorded_at)
    )
    social_scores = social_scores_result.scalars().all()
    
    for score in social_scores:
        # Only add to timeline if there's an actual score value
        if score.score is not None:
            description = f"Score social calculado: {score.score}"
            if score.recorded_by:
                description += f" por {score.recorded_by}"
            
            events.append(HistoryEvent(
                event_type=HistoryEventType.SOCIAL_SCORE_RECORDED,
                event_date=score.recorded_at,
                description=description,
                metadata={
                    "score_id": str(score.id),
                    "score": score.score,
                    "recorded_by": score.recorded_by,
                    "notes": score.notes
                }
            ))
    
    # 6. Alert creation events
    alerts_result = await session.execute(
        select(AlertModel)
        .where(AlertModel.episode_id == episode_id)
        .order_by(AlertModel.created_at)
    )
    alerts = alerts_result.scalars().all()
    
    for alert in alerts:
        description = f"Alerta creada: {alert.message}"
        if alert.created_by:
            description += f" (por {alert.created_by})"
        
        events.append(HistoryEvent(
            event_type=HistoryEventType.ALERT_CREATED,
            event_date=alert.created_at,
            description=description,
            metadata={
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "is_active": alert.is_active,
                "created_by": alert.created_by
            }
        ))
    
    # Sort events by date
    events.sort(key=lambda x: x.event_date)
    
    return EpisodeHistory(
        episode_id=episode_id,
        events=events
    )
