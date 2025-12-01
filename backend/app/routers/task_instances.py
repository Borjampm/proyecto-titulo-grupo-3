from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.deps import get_session
from app.models.task_instance import (
    TaskInstance as TaskInstanceModel,
    TaskStatus
)
from app.models.task_status_history import TaskStatusHistory
from app.models.worker import Worker as WorkerModel
from app.schemas.task_instance import (
    TaskInstance,
    TaskInstanceCreate,
    TaskInstanceUpdate,
    TaskStatus as TaskStatusSchema
)


router = APIRouter(prefix="/task-instances", tags=["task-instances"])


@router.get("/statuses", response_model=List[str])
async def get_task_statuses() -> List[str]:
    """
    Get all possible task status values.

    Returns:
        List of available task statuses
    """
    return [status.value for status in TaskStatus]


@router.get("/", response_model=List[TaskInstance])
async def get_all_tasks(
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (PENDING, IN_PROGRESS, COMPLETED, etc.)"
    ),
    assigned_to_id: Optional[UUID] = Query(
        None,
        description="Filter by assigned worker ID"
    ),
    open_only: bool = Query(
        True,
        description="If True, only returns tasks with PENDING or IN_PROGRESS status"
    ),
    order_by_due_date: bool = Query(
        True,
        description="If True, orders tasks by due date (earliest first)"
    ),
    session: AsyncSession = Depends(get_session)
) -> List[TaskInstance]:
    """
    Get all tasks with optional filtering.

    Args:
        status_filter: Filter by specific status
        assigned_to_id: Filter by assigned worker
        open_only: If True, only returns PENDING and IN_PROGRESS tasks
        order_by_due_date: If True, orders by due date ascending
        session: Database session

    Returns:
        List of task instances
    """
    query = select(TaskInstanceModel).options(
        selectinload(TaskInstanceModel.assigned_worker)
    )
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = TaskStatus(status_filter.upper())
            query = query.where(TaskInstanceModel.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter
    elif open_only:
        query = query.where(
            or_(
                TaskInstanceModel.status == TaskStatus.PENDING,
                TaskInstanceModel.status == TaskStatus.IN_PROGRESS
            )
        )
    
    # Filter by assigned worker
    if assigned_to_id:
        query = query.where(TaskInstanceModel.assigned_to_id == assigned_to_id)
    
    # Order by due date
    if order_by_due_date:
        # Nulls last - tasks without due date appear at the end
        query = query.order_by(
            TaskInstanceModel.due_date.asc().nulls_last(),
            TaskInstanceModel.priority.desc(),
            TaskInstanceModel.created_at.desc()
        )
    else:
        query = query.order_by(TaskInstanceModel.created_at.desc())
    
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/episode/{episode_id}", response_model=List[TaskInstance])
async def get_episode_tasks(
    episode_id: UUID,
    assigned_to_id: Optional[UUID] = Query(
        None,
        description="Filter by assigned worker ID"
    ),
    session: AsyncSession = Depends(get_session)
) -> List[TaskInstance]:
    """
    Get all tasks for a specific clinical episode.

    Args:
        episode_id: The UUID of the clinical episode
        assigned_to_id: Filter by assigned worker
        session: Database session

    Returns:
        List of task instances for the episode
    """
    query = select(TaskInstanceModel).options(
        selectinload(TaskInstanceModel.assigned_worker)
    ).where(TaskInstanceModel.episode_id == episode_id)
    
    if assigned_to_id:
        query = query.where(TaskInstanceModel.assigned_to_id == assigned_to_id)
    
    query = query.order_by(
        TaskInstanceModel.due_date.asc().nulls_last(),
        TaskInstanceModel.priority.desc()
    )
    
    result = await session.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskInstance)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> TaskInstance:
    """
    Get a specific task by ID.

    Args:
        task_id: The UUID of the task instance
        session: Database session

    Returns:
        The task instance

    Raises:
        HTTPException: 404 if task not found
    """
    result = await session.execute(
        select(TaskInstanceModel)
        .options(selectinload(TaskInstanceModel.assigned_worker))
        .where(TaskInstanceModel.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    return task


@router.patch("/{task_id}", response_model=TaskInstance)
async def update_task(
    task_id: UUID,
    task_update: TaskInstanceUpdate,
    session: AsyncSession = Depends(get_session)
) -> TaskInstance:
    """
    Update a task instance.

    Can be used to update any field including status, description,
    title, etc. If status is changed, automatically creates a status history record.

    Args:
        task_id: The UUID of the task instance
        task_update: The fields to update
        session: Database session

    Returns:
        The updated task instance

    Raises:
        HTTPException: 404 if task not found
    """
    result = await session.execute(
        select(TaskInstanceModel)
        .options(selectinload(TaskInstanceModel.assigned_worker))
        .where(TaskInstanceModel.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Update only the fields that were provided
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Check if status is being updated
    old_status = task.status
    status_changed = False
    
    for field, value in update_data.items():
        if field == "status" and value != old_status:
            status_changed = True
        setattr(task, field, value)
    
    # Create status history record if status changed
    if status_changed:
        status_history = TaskStatusHistory(
            task_id=task.id,
            old_status=old_status,
            new_status=task.status,
            notes=f"Status updated from {old_status.value} to {task.status.value}"
        )
        session.add(status_history)

    await session.commit()
    await session.refresh(task)

    return task


@router.patch("/{task_id}/status", response_model=TaskInstance)
async def update_task_status(
    task_id: UUID,
    new_status: TaskStatusSchema,
    session: AsyncSession = Depends(get_session)
) -> TaskInstance:
    """
    Update only the status of a task instance.
    
    Automatically creates a status history record tracking the change.

    Args:
        task_id: The UUID of the task instance
        new_status: The new status to set
        session: Database session

    Returns:
        The updated task instance

    Raises:
        HTTPException: 404 if task not found
    """
    result = await session.execute(
        select(TaskInstanceModel).where(TaskInstanceModel.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Store old status before updating
    old_status = task.status
    new_status_enum = TaskStatus(new_status.value)
    
    # Only create history if status actually changed
    if old_status != new_status_enum:
        task.status = new_status_enum
        
        # Create status history record
        status_history = TaskStatusHistory(
            task_id=task.id,
            old_status=old_status,
            new_status=new_status_enum,
            notes=f"Status updated from {old_status.value} to {new_status_enum.value}"
        )
        session.add(status_history)

    await session.commit()
    await session.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> None:
    """
    Delete a task instance.

    Args:
        task_id: The UUID of the task instance
        session: Database session

    Raises:
        HTTPException: 404 if task not found
    """
    result = await session.execute(
        select(TaskInstanceModel).where(TaskInstanceModel.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    await session.delete(task)
    await session.commit()


@router.post(
    "/",
    response_model=TaskInstance,
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    task_create: TaskInstanceCreate,
    session: AsyncSession = Depends(get_session)
) -> TaskInstance:
    """
    Create a new task instance.
    
    Automatically creates an initial status history record.

    Args:
        task_create: The task data
        session: Database session

    Returns:
        The created task instance
    """
    task = TaskInstanceModel(
        episode_id=task_create.episode_id,
        title=task_create.title,
        description=task_create.description,
        due_date=task_create.due_date,
        priority=task_create.priority,
        status=TaskStatus(task_create.status.value),
        meta_json=task_create.meta_json,
        assigned_to_id=task_create.assigned_to_id
    )

    session.add(task)
    await session.flush()  # Get the task ID
    
    # Create initial status history record
    status_history = TaskStatusHistory(
        task_id=task.id,
        old_status=None,  # No previous status for new tasks
        new_status=task.status,
        notes="Task created"
    )
    session.add(status_history)
    
    await session.commit()
    
    # Reload task with worker relationship
    result = await session.execute(
        select(TaskInstanceModel)
        .options(selectinload(TaskInstanceModel.assigned_worker))
        .where(TaskInstanceModel.id == task.id)
    )
    task = result.scalar_one()

    return task
