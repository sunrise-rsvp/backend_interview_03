from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from slowapi import Limiter

from database import async_get_db
from rate_limiter import limiter
from auth import get_current_user_id
from events.repositories import EventRepository
from events.queries import EventQueries
from events.orm import Event
from events.inputs import CreateEventInput, UpdateEventInput
from events.outputs import EventOutput, EventListOutput, EventCountOutput, EventWithTicketsOutput
from tasks import create_default_ticket_type_and_creator_ticket

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventOutput)
@limiter.limit("20/minute")
async def create_event(
    request: Request,
    event_data: CreateEventInput,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """Create a new event"""
    repository = EventRepository(session=db)
    event_data.created_by = str(current_user_id)
    event = await repository.create(event_data=event_data)
    
    # Trigger background task to create default ticket type and creator ticket
    create_default_ticket_type_and_creator_ticket.delay(
        event_id=str(event.id),
        created_by=event_data.created_by
    )
    
    return EventOutput.from_orm(event)


@router.get("/with-tickets/", response_model=list[EventWithTicketsOutput])
@limiter.limit("100/minute")
async def list_events_with_tickets(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """List events with their ticket counts"""
    queries = EventQueries(session=db)
    events = await queries.get_all(limit=100, offset=0)
    
    results = []
    for event in events:
        # Get ticket count for each event
        ticket_count = await queries.get_ticket_count_for_event(event_id=event.id)
        results.append(EventWithTicketsOutput(
            id=event.id,
            name=event.name,
            ticket_count=ticket_count
        ))
    return results


@router.get("/count/", response_model=EventCountOutput)
@limiter.limit("100/minute")
async def get_event_count(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """Get the total count of active events"""
    queries = EventQueries(session=db)
    count = await queries.get_total_count()
    return EventCountOutput(count=count)


@router.get("/{event_id}/", response_model=EventOutput)
@limiter.limit("100/minute")
async def get_event(
    request: Request,
    event_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
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
    current_user_id: UUID = Depends(get_current_user_id),
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
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """Update an existing event"""
    queries = EventQueries(session=db)
    repository = EventRepository(session=db)
    
    # Check if event exists
    stmt = select(Event).where(and_(Event.id == event_id, Event.is_active == True))
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Verify user owns the event
    existing_event = await queries.get_by_id(event_id=event_id)
    if existing_event.created_by != str(current_user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    
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
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(async_get_db)
):
    """Delete an event (soft delete)"""
    repository = EventRepository(session=db)
    deleted = await repository.delete(event_id=event_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted successfully"}
