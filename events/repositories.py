from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from events.orm import Event
from events.inputs import CreateEventInput, UpdateEventInput
from events.cache_service import event_cache_service


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_data: CreateEventInput) -> Event:
        """Create a new event"""
        event = Event(
            name=event_data.name,
            description=event_data.description,
            location=event_data.location,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            created_by=event_data.created_by
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def update(self, event_id: UUID, event_data: UpdateEventInput) -> Optional[Event]:
        """Update an existing event"""
        # Build update dict excluding None values and ID
        update_data = {
            key: value for key, value in event_data.dict().items() 
            if value is not None
        }
        
        if not update_data:
            # If no data to update, return None (let view layer handle this)
            return None
        
        stmt = (
            update(Event)
            .where(and_(Event.id == event_id, Event.is_active == True))
            .values(**update_data)
            .returning(Event)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        updated_event = result.scalar_one_or_none()
        
        if updated_event:
            # Update cache with new event data
            await event_cache_service.cache_event(updated_event)
            # Invalidate list caches since event data changed
            await event_cache_service.invalidate_event_lists()
            await event_cache_service.invalidate_search_caches()
        
        return updated_event

    async def delete(self, event_id: UUID) -> bool:
        """Soft delete an event by setting is_active to False"""
        stmt = (
            update(Event)
            .where(and_(Event.id == event_id, Event.is_active == True))
            .values(is_active=False)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        deleted = result.rowcount > 0
        
        if deleted:
            # Invalidate the specific event cache and list caches
            await event_cache_service.invalidate_event(event_id)
            await event_cache_service.invalidate_event_lists()
            await event_cache_service.invalidate_search_caches()
        
        return deleted


