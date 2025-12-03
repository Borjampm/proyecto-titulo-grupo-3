from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.deps import get_session
from app.models.alert import Alert as AlertModel, AlertType, AlertSeverity
from app.models.clinical_episode import ClinicalEpisode
from app.models.patient import Patient
from app.schemas.alert import Alert, AlertCreateManual, AlertWithPatient

router = APIRouter(tags=["alerts"])


@router.get("/clinical-episodes/{episode_id}/alerts", response_model=List[Alert])
async def get_episode_alerts(
    episode_id: UUID,
    active_only: bool = Query(True, description="Filter to only active alerts"),
    session: AsyncSession = Depends(get_session)
) -> List[Alert]:
    """
    Get all alerts for a specific clinical episode.
    
    Args:
        episode_id: UUID of the clinical episode
        active_only: If True, only return active alerts (default: True)
    
    Returns:
        List of alerts for the episode
    """
    # Build query
    query = select(AlertModel).where(AlertModel.episode_id == episode_id)
    
    # Filter by active status if requested
    if active_only:
        query = query.where(AlertModel.is_active == True)
    
    # Order by most recent first
    query = query.order_by(AlertModel.created_at.desc())
    
    # Execute query
    result = await session.execute(query)
    alerts = result.scalars().all()
    
    return alerts


@router.post("/clinical-episodes/{episode_id}/alerts", response_model=Alert)
async def create_episode_alert(
    episode_id: UUID,
    alert_data: AlertCreateManual,
    session: AsyncSession = Depends(get_session)
) -> Alert:
    """
    Create a new social-risk alert for a clinical episode.
    
    This endpoint is for manually creating alerts (e.g., by social workers).
    Only social-risk alerts can be created manually.
    
    Args:
        episode_id: UUID of the clinical episode
        alert_data: Alert data (message, severity, created_by)
    
    Returns:
        The created alert
    """
    # Verify episode exists
    episode_result = await session.execute(
        select(ClinicalEpisode).where(ClinicalEpisode.id == episode_id)
    )
    episode = episode_result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Clinical episode not found")
    
    # Create alert
    new_alert = AlertModel(
        episode_id=episode_id,
        alert_type=AlertType.SOCIAL_RISK,  # Manual alerts are always social-risk
        severity=alert_data.severity,
        message=alert_data.message,
        is_active=True,
        created_by=alert_data.created_by
    )
    
    session.add(new_alert)
    await session.commit()
    await session.refresh(new_alert)
    
    return new_alert


@router.get("/alerts", response_model=List[AlertWithPatient])
async def get_all_alerts(
    active_only: bool = Query(True, description="Filter to only active alerts"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(1000, ge=1, le=10000, description="Number of alerts per page"),
    session: AsyncSession = Depends(get_session)
) -> List[AlertWithPatient]:
    """
    Get all alerts across all clinical episodes (paginated).
    
    Args:
        active_only: If True, only return active alerts (default: True)
        alert_type: Optional filter by alert type
        page: Page number (1-indexed)
        page_size: Number of alerts per page (max 10000)
    
    Returns:
        List of alerts with patient information
    """
    # Build query with episode and patient join for information
    query = select(AlertModel).options(
        selectinload(AlertModel.clinical_episode).selectinload(ClinicalEpisode.patient)
    )
    
    # Filter by active status if requested
    if active_only:
        query = query.where(AlertModel.is_active == True)
    
    # Filter by alert type if provided
    if alert_type:
        query = query.where(AlertModel.alert_type == alert_type)
    
    # Order by most recent first
    query = query.order_by(AlertModel.created_at.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await session.execute(query)
    alerts = result.scalars().all()
    
    # Transform to include patient name
    alerts_with_patient = []
    for alert in alerts:
        patient_name = None
        if alert.clinical_episode and alert.clinical_episode.patient:
            patient = alert.clinical_episode.patient
            patient_name = f"{patient.first_name or ''} {patient.last_name or ''}".strip() or "Sin nombre"
        
        alert_dict = {
            "id": alert.id,
            "episode_id": alert.episode_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "is_active": alert.is_active,
            "created_by": alert.created_by,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "patient_name": patient_name
        }
        alerts_with_patient.append(AlertWithPatient(**alert_dict))
    
    return alerts_with_patient


@router.patch("/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(
    alert_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Alert:
    """
    Mark an alert as resolved by setting is_active to False.
    
    Args:
        alert_id: UUID of the alert to resolve
    
    Returns:
        The updated alert with is_active=False
    """
    # Fetch alert
    result = await session.execute(
        select(AlertModel).where(AlertModel.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update is_active to False
    alert.is_active = False
    await session.commit()
    await session.refresh(alert)
    
    return alert

