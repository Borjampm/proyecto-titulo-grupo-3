from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.deps import get_session
from app.models.worker import Worker as WorkerModel
from app.schemas.worker import (
    Worker,
    WorkerCreate,
    WorkerUpdate,
    WorkerSimple
)


router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/", response_model=List[Worker])
async def get_workers(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session)
) -> List[Worker]:
    """
    Get all workers.

    Args:
        active_only: If True, only returns active workers
        session: Database session

    Returns:
        List of workers
    """
    query = select(WorkerModel)
    if active_only:
        query = query.where(WorkerModel.active == True)
    query = query.order_by(WorkerModel.name)
    
    result = await session.execute(query)
    workers = result.scalars().all()
    return workers


@router.get("/simple", response_model=List[WorkerSimple])
async def get_workers_simple(
    session: AsyncSession = Depends(get_session)
) -> List[WorkerSimple]:
    """
    Get simplified list of active workers (for dropdowns).

    Args:
        session: Database session

    Returns:
        List of simplified worker objects
    """
    result = await session.execute(
        select(WorkerModel)
        .where(WorkerModel.active == True)
        .order_by(WorkerModel.name)
    )
    workers = result.scalars().all()
    return workers


@router.get("/{worker_id}", response_model=Worker)
async def get_worker(
    worker_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> Worker:
    """
    Get a specific worker by ID.

    Args:
        worker_id: The UUID of the worker
        session: Database session

    Returns:
        The worker

    Raises:
        HTTPException: 404 if worker not found
    """
    result = await session.execute(
        select(WorkerModel).where(WorkerModel.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id {worker_id} not found"
        )

    return worker


@router.post("/", response_model=Worker, status_code=status.HTTP_201_CREATED)
async def create_worker(
    worker_create: WorkerCreate,
    session: AsyncSession = Depends(get_session)
) -> Worker:
    """
    Create a new worker.

    Args:
        worker_create: The worker data
        session: Database session

    Returns:
        The created worker
    """
    worker = WorkerModel(
        name=worker_create.name,
        email=worker_create.email,
        role=worker_create.role,
        department=worker_create.department
    )

    session.add(worker)
    await session.commit()
    await session.refresh(worker)

    return worker


@router.patch("/{worker_id}", response_model=Worker)
async def update_worker(
    worker_id: UUID,
    worker_update: WorkerUpdate,
    session: AsyncSession = Depends(get_session)
) -> Worker:
    """
    Update a worker.

    Args:
        worker_id: The UUID of the worker
        worker_update: The fields to update
        session: Database session

    Returns:
        The updated worker

    Raises:
        HTTPException: 404 if worker not found
    """
    result = await session.execute(
        select(WorkerModel).where(WorkerModel.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id {worker_id} not found"
        )

    # Update only the fields that were provided
    update_data = worker_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)

    await session.commit()
    await session.refresh(worker)

    return worker


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker(
    worker_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> None:
    """
    Soft delete a worker (set active to False).

    Args:
        worker_id: The UUID of the worker
        session: Database session

    Raises:
        HTTPException: 404 if worker not found
    """
    result = await session.execute(
        select(WorkerModel).where(WorkerModel.id == worker_id)
    )
    worker = result.scalar_one_or_none()

    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker with id {worker_id} not found"
        )

    # Soft delete - just mark as inactive
    worker.active = False
    await session.commit()

