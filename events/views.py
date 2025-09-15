from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter

from database import async_get_db
from rate_limiter import limiter
from events.repositories import EventRepository
from events.queries import EventQueries
from events.inputs import CreateEventInput, UpdateEventInput
from events.outputs import EventOutput, EventListOutput

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventOutput)
@limiter.limit("20/minute")
async def create_event(
    request: Request,
    event_data: CreateEventInput,
    db: AsyncSession = Depends(async_get_db)
):
    """Create a new event"""
    repository = EventRepository(session=db)
    event = await repository.create(event_data=event_data)
    return EventOutput.from_orm(event)


@router.get("/{event_id}/", response_model=EventOutput)
@limiter.limit("100/minute")
async def get_event(
    request: Request,
    event_id: UUID,
    db: AsyncSession = Depends(async_get_db)
):
    """Get a single event by ID"""
    queries = EventQueries(session=db)
    event = await queries.get_by_id(event_id=event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventOutput.from_orm(event)


@router.get("/", response_model=EventListOutput)
@limiter.limit("100/minute")
async def list_events(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(async_get_db)
):
    """List events with optional search and pagination"""
    queries = EventQueries(session=db)
    
    if search or location:
        events = await queries.search_events(
            search_term=search,
            location=location,
            limit=limit,
            offset=offset
        )
        total = await queries.get_search_count(
            search_term=search,
            location=location
        )
    else:
        events = await queries.get_all(limit=limit, offset=offset)
        total = await queries.get_total_count()
    
    event_outputs = [EventOutput.from_orm(event) for event in events]
    
    return EventListOutput(
        events=event_outputs,
        total=total
    )


@router.put("/{event_id}/", response_model=EventOutput)
@limiter.limit("20/minute")
async def update_event(
    request: Request,
    event_id: UUID,
    event_data: UpdateEventInput,
    db: AsyncSession = Depends(async_get_db)
):
    """Update an existing event"""
    queries = EventQueries(session=db)
    repository = EventRepository(session=db)
    
    # Check if event exists first (using queries for read operation)
    existing_event = await queries.get_by_id(event_id=event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update the event (using repository for write operation)
    updated_event = await repository.update(event_id=event_id, event_data=event_data)
    
    # If no fields to update, return the existing event
    if updated_event is None:
        return EventOutput.from_orm(existing_event)
    
    return EventOutput.from_orm(updated_event)


@router.delete("/{event_id}/")
@limiter.limit("20/minute")
async def delete_event(
    request: Request,
    event_id: UUID,
    db: AsyncSession = Depends(async_get_db)
):
    """Delete an event (soft delete)"""
    repository = EventRepository(session=db)
    deleted = await repository.delete(event_id=event_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully"}
