from typing import Optional, List, Dict, Any
from uuid import UUID
import json
from redis_client import redis_client
from events.orm import Event
from events.outputs import EventOutput


class EventCacheService:
    """Service for caching event data in Redis"""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour default TTL
        self.list_cache_ttl = 600  # 10 minutes for list caches
    
    def _get_event_key(self, event_id: UUID) -> str:
        """Generate Redis key for individual event"""
        return f"event:{str(event_id)}"
    
    def _get_list_key(self, key_suffix: str) -> str:
        """Generate Redis key for event lists"""
        return f"events:list:{key_suffix}"
    
    def _get_search_key(self, search_term: Optional[str], location: Optional[str], limit: int, offset: int) -> str:
        """Generate Redis key for search results"""
        search_part = f"search:{search_term}" if search_term else "all"
        location_part = f"location:{location}" if location else "any"
        return f"events:{search_part}:{location_part}:{limit}:{offset}"
    
    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert Event ORM object to dictionary for caching"""
        return {
            "id": str(event.id),
            "name": event.name,
            "description": event.description,
            "location": event.location,
            "start_date": event.start_date.isoformat() if event.start_date else None,
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "is_active": event.is_active,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None
        }
    
    async def cache_event(self, event: Event) -> bool:
        """Cache a single event"""
        key = self._get_event_key(event.id)
        event_data = self._event_to_dict(event)
        return await redis_client.set(key, event_data, self.cache_ttl)
    
    async def get_cached_event(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached event by ID"""
        key = self._get_event_key(event_id)
        return await redis_client.get(key)
    
    async def cache_event_list(
        self, 
        events: List[Event], 
        total: int, 
        cache_key: str
    ) -> bool:
        """Cache a list of events with metadata"""
        event_list_data = {
            "events": [self._event_to_dict(event) for event in events],
            "total": total
        }
        return await redis_client.set(cache_key, event_list_data, self.list_cache_ttl)
    
    async def get_cached_event_list(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached event list"""
        return await redis_client.get(cache_key)
    
    async def invalidate_event(self, event_id: UUID) -> bool:
        """Invalidate cached event"""
        key = self._get_event_key(event_id)
        return await redis_client.delete(key)
    
    async def invalidate_event_lists(self) -> int:
        """Invalidate all cached event lists"""
        return await redis_client.delete_pattern("events:list:*")
    
    async def invalidate_search_caches(self) -> int:
        """Invalidate all search result caches"""
        return await redis_client.delete_pattern("events:search:*")
    
    async def invalidate_all_event_caches(self) -> bool:
        """Invalidate all event-related caches"""
        try:
            await redis_client.delete_pattern("event:*")
            await redis_client.delete_pattern("events:*")
            return True
        except Exception as e:
            print(f"Error invalidating all event caches: {e}")
            return False
    
    async def warm_cache_for_event(self, event: Event) -> bool:
        """Warm cache for a specific event"""
        return await self.cache_event(event)
    
    async def warm_cache_for_popular_events(self, events: List[Event]) -> int:
        """Warm cache for multiple popular events"""
        successful_caches = 0
        for event in events:
            if await self.cache_event(event):
                successful_caches += 1
        return successful_caches
    
    def get_all_events_cache_key(self, limit: int, offset: int) -> str:
        """Get cache key for all events list"""
        return self._get_list_key(f"all:{limit}:{offset}")
    
    def get_search_cache_key(
        self, 
        search_term: Optional[str], 
        location: Optional[str], 
        limit: int, 
        offset: int
    ) -> str:
        """Get cache key for search results"""
        return self._get_search_key(search_term, location, limit, offset)


# Global cache service instance
event_cache_service = EventCacheService()
