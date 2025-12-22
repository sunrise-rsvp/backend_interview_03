"""
End-to-end integration tests for Event CRUD operations using Playwright
"""
import pytest
import asyncio
import json
from uuid import uuid4
from playwright.async_api import Page, expect
import httpx


@pytest.mark.integration
@pytest.mark.crud
class TestEventsCRUDIntegration:
    """Test Event CRUD operations end-to-end"""
    
    @pytest.mark.asyncio
    async def test_create_event_via_api(self, server_process, api_client, sample_event_data):
        """Test creating an event via API endpoint"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post("/events/", json=sample_event_data)
            assert response.status_code == 200
            
            event_data = response.json()
            assert event_data["name"] == sample_event_data["name"]
            assert event_data["description"] == sample_event_data["description"]
            assert event_data["location"] == sample_event_data["location"]
            assert "id" in event_data
            
            return event_data
    
    @pytest.mark.asyncio
    async def test_get_event_via_api(self, server_process, api_client, sample_event_data):
        """Test retrieving an event via API endpoint"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # First create an event
            create_response = await client.post("/events/", json=sample_event_data)
            created_event = create_response.json()
            event_id = created_event["id"]
            
            # Then retrieve it
            get_response = await client.get(f"/events/{event_id}/")
            assert get_response.status_code == 200
            
            retrieved_event = get_response.json()
            assert retrieved_event["id"] == event_id
            assert retrieved_event["name"] == sample_event_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_event(self, server_process, api_client):
        """Test retrieving a non-existent event returns 404"""
        fake_id = str(uuid4())
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/events/{fake_id}/")
            assert response.status_code == 404
            assert "Event not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_list_events_via_api(self, server_process, api_client, sample_event_data_list):
        """Test listing events with pagination"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create multiple events
            created_events = []
            for event_data in sample_event_data_list:
                response = await client.post("/events/", json=event_data)
                created_events.append(response.json())
            
            # Test listing all events
            list_response = await client.get("/events/")
            assert list_response.status_code == 200
            
            response_data = list_response.json()
            assert "events" in response_data
            assert "total" in response_data
            assert len(response_data["events"]) >= len(sample_event_data_list)
            
            # Test pagination
            paginated_response = await client.get("/events/?limit=2&offset=0")
            assert paginated_response.status_code == 200
            paginated_data = paginated_response.json()
            assert len(paginated_data["events"]) <= 2
    
    @pytest.mark.asyncio
    async def test_search_events_via_api(self, server_process, api_client, sample_event_data_list):
        """Test searching events by name and location"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create events
            for event_data in sample_event_data_list:
                await client.post("/events/", json=event_data)
            
            # Search by name
            search_response = await client.get("/events/?search=Tech")
            assert search_response.status_code == 200
            search_data = search_response.json()
            
            # Should find the Tech Conference event
            tech_events = [e for e in search_data["events"] if "Tech" in e["name"]]
            assert len(tech_events) >= 1
            
            # Search by location
            location_response = await client.get("/events/?location=Austin")
            assert location_response.status_code == 200
            location_data = location_response.json()
            
            # Should find Austin events
            austin_events = [e for e in location_data["events"] if "Austin" in e["location"]]
            assert len(austin_events) >= 1
    
    @pytest.mark.asyncio
    async def test_update_event_via_api(self, server_process, api_client, sample_event_data):
        """Test updating an event via API endpoint"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            create_response = await client.post("/events/", json=sample_event_data)
            created_event = create_response.json()
            event_id = created_event["id"]
            
            # Update the event
            update_data = {
                "name": "Updated Test Event",
                "description": "This is an updated test event"
            }
            
            update_response = await client.put(f"/events/{event_id}/", json=update_data)
            assert update_response.status_code == 200
            
            updated_event = update_response.json()
            assert updated_event["name"] == update_data["name"]
            assert updated_event["description"] == update_data["description"]
            assert updated_event["location"] == sample_event_data["location"]  # unchanged
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_event(self, server_process, api_client):
        """Test updating a non-existent event returns 404"""
        fake_id = str(uuid4())
        update_data = {"name": "Should not work"}
        
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.put(f"/events/{fake_id}/", json=update_data)
            assert response.status_code == 404
            assert "Event not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_event_via_api(self, server_process, api_client, sample_event_data):
        """Test deleting an event via API endpoint (soft delete)"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create an event
            create_response = await client.post("/events/", json=sample_event_data)
            created_event = create_response.json()
            event_id = created_event["id"]
            
            # Delete the event
            delete_response = await client.delete(f"/events/{event_id}/")
            assert delete_response.status_code == 200
            assert "deleted successfully" in delete_response.json()["message"]
            
            # Verify event is no longer accessible
            get_response = await client.get(f"/events/{event_id}/")
            assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_event(self, server_process, api_client):
        """Test deleting a non-existent event returns 404"""
        fake_id = str(uuid4())
        
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.delete(f"/events/{fake_id}/")
            assert response.status_code == 404
            assert "Event not found" in response.json()["detail"]


@pytest.mark.integration 
@pytest.mark.slow
class TestEventWorkflowIntegration:
    """Test complete event workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_event_lifecycle(self, server_process, api_client, sample_event_data):
        """Test complete CRUD lifecycle of an event"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # 1. Create event
            create_response = await client.post("/events/", json=sample_event_data)
            assert create_response.status_code == 200
            event = create_response.json()
            event_id = event["id"]
            
            # 2. Retrieve event
            get_response = await client.get(f"/events/{event_id}/")
            assert get_response.status_code == 200
            retrieved_event = get_response.json()
            assert retrieved_event["name"] == sample_event_data["name"]
            
            # 3. Update event
            update_data = {"name": "Lifecycle Updated Event"}
            update_response = await client.put(f"/events/{event_id}/", json=update_data)
            assert update_response.status_code == 200
            updated_event = update_response.json()
            assert updated_event["name"] == update_data["name"]
            
            # 4. Verify update by retrieving again
            verify_response = await client.get(f"/events/{event_id}/")
            assert verify_response.status_code == 200
            verified_event = verify_response.json()
            assert verified_event["name"] == update_data["name"]
            
            # 5. Delete event
            delete_response = await client.delete(f"/events/{event_id}/")
            assert delete_response.status_code == 200
            
            # 6. Verify deletion
            final_get_response = await client.get(f"/events/{event_id}/")
            assert final_get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_bulk_event_operations(self, server_process, api_client, sample_event_data_list):
        """Test bulk operations on multiple events"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            created_event_ids = []
            
            # Create multiple events
            for event_data in sample_event_data_list:
                response = await client.post("/events/", json=event_data)
                assert response.status_code == 200
                created_event_ids.append(response.json()["id"])
            
            # Verify all events exist in list
            list_response = await client.get("/events/")
            assert list_response.status_code == 200
            all_events = list_response.json()["events"]
            
            for event_id in created_event_ids:
                assert any(event["id"] == event_id for event in all_events)
            
            # Update all events
            for event_id in created_event_ids:
                update_response = await client.put(
                    f"/events/{event_id}/", 
                    json={"description": "Bulk updated event"}
                )
                assert update_response.status_code == 200
            
            # Delete all events
            for event_id in created_event_ids:
                delete_response = await client.delete(f"/events/{event_id}/")
                assert delete_response.status_code == 200
            
            # Verify all events are deleted
            for event_id in created_event_ids:
                get_response = await client.get(f"/events/{event_id}/")
                assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.crud
class TestEventValidationIntegration:
    """Test event validation and error handling"""
    
    @pytest.mark.asyncio
    async def test_create_event_with_invalid_data(self, server_process, api_client):
        """Test creating event with invalid data"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Test with missing required fields
            invalid_data = {"description": "Missing name"}
            response = await client.post("/events/", json=invalid_data)
            assert response.status_code == 422  # Validation error
            
            # Test with invalid date format
            invalid_date_data = {
                "name": "Test Event",
                "start_date": "invalid-date",
                "end_date": "2024-12-25T18:00:00"
            }
            response = await client.post("/events/", json=invalid_date_data)
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_event_with_invalid_data(self, server_process, api_client, sample_event_data):
        """Test updating event with invalid data"""
        async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
            # Create valid event first
            create_response = await client.post("/events/", json=sample_event_data)
            event = create_response.json()
            event_id = event["id"]
            
            # Try to update with invalid data
            invalid_update = {"start_date": "not-a-date"}
            response = await client.put(f"/events/{event_id}/", json=invalid_update)
            assert response.status_code == 422
