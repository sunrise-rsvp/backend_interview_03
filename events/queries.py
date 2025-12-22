from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from events.orm import Event
from events.schemas import Event as EventSchema
from events.cache_service import event_cache_service


class EventQueries:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _parse_cached_event(self, event_dict: dict) -> Event:
        """Parse and validate cached event data, converting to ORM Event object"""
        # Parse with pydantic for validation and type conversion
        event_schema = EventSchema.parse_obj(event_dict)
        
        # Convert directly to ORM object from pydantic fields
        event = Event(
            id=event_schema.id,
            name=event_schema.name,
            description=event_schema.description,
            location=event_schema.location,
            start_date=event_schema.start_date,
            end_date=event_schema.end_date,
            is_active=event_schema.is_active,
            created_at=event_schema.created_at,
            updated_at=event_schema.updated_at
        )
        return event

    async def get_by_id(self, event_id: UUID) -> Optional[Event]:
        """Get a single event by ID with cache-first strategy"""
        # Try to get from cache first
        cached_event = await event_cache_service.get_cached_event(event_id)
        if cached_event:
            # Convert cached dict back to Event object
            return self._parse_cached_event(cached_event)
        
        # Cache miss - get from database
        stmt = select(Event).where(and_(Event.id == event_id, Event.is_active == True))
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        
        # Cache the result if found
        if event:
            await event_cache_service.cache_event(event)
        
        return event

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Event]:
        """Get all active events with pagination and caching"""
        # Try to get from cache first
        cache_key = event_cache_service.get_all_events_cache_key(limit, offset)
        cached_result = await event_cache_service.get_cached_event_list(cache_key)
        
        if cached_result:
            # Convert cached event dicts back to Event objects
            return [self._dict_to_event(event_dict) for event_dict in cached_result["events"]]
        
        # Cache miss - get from database
        stmt = (
            select(Event)
            .where(Event.is_active == True)
            .order_by(Event.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        events = result.scalars().all()
        
        # Cache the results
        if events:
            total = await self.get_total_count()
            await event_cache_service.cache_event_list(events, total, cache_key)
        
        return events

    async def get_total_count(self) -> int:
        """Get total count of active events"""
        stmt = select(func.count(Event.id)).where(Event.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_events(
        self, 
        search_term: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Event]:
        """Search events by name, description, or location with caching"""
        # Try to get from cache first
        cache_key = event_cache_service.get_search_cache_key(search_term, location, limit, offset)
        cached_result = await event_cache_service.get_cached_event_list(cache_key)
        
        if cached_result:
            # Convert cached event dicts back to Event objects
            return [self._dict_to_event(event_dict) for event_dict in cached_result["events"]]
        
        # Cache miss - get from database
        stmt = select(Event).where(Event.is_active == True)
        
        if search_term:
            search_filter = or_(
                Event.name.ilike(f"%{search_term}%"),
                Event.description.ilike(f"%{search_term}%")
            )
            stmt = stmt.where(search_filter)
        
        if location:
            stmt = stmt.where(Event.location.ilike(f"%{location}%"))
        
        stmt = stmt.order_by(Event.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        events = result.scalars().all()
        
        # Cache the results
        if events:
            total = await self.get_search_count(search_term, location)
            await event_cache_service.cache_event_list(events, total, cache_key)
        
        return events

    async def get_search_count(
        self, 
        search_term: Optional[str] = None,
        location: Optional[str] = None
    ) -> int:
        """Get count of search results"""
        stmt = select(func.count(Event.id)).where(Event.is_active == True)
        
        if search_term:
            search_filter = or_(
                Event.name.ilike(f"%{search_term}%"),
                Event.description.ilike(f"%{search_term}%")
            )
            stmt = stmt.where(search_filter)
        
        if location:
            stmt = stmt.where(Event.location.ilike(f"%{location}%"))
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
