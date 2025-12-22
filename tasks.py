import asyncio
from typing import Optional
from uuid import UUID
from decimal import Decimal
import uuid as uuid_module
from celery.exceptions import Retry
import os
import logging

from celery_worker import celery_app
from database import async_get_db

logger = logging.getLogger(__name__)


@celery_app.task(name='create_default_ticket_type_and_creator_ticket', bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def create_default_ticket_type_and_creator_ticket(self, event_id: str, created_by: Optional[str] = None):
    """
    Background task to create a default ticket type and assign a ticket to the event creator
    
    Args:
        event_id: UUID string of the created event
        created_by: Optional user ID of the event creator
    """
    async def _create_ticket_async():
        from tickets.repositories import TicketRepository, TicketTypeRepository
        from tickets.inputs import CreateTicketInput, CreateTicketTypeInput
        
        # Use the app's database session
        async for db_session in async_get_db():
            try:
                # Convert string UUID to UUID object
                event_uuid = UUID(event_id)
                
                # Create default ticket type for the event
                ticket_type_repo = TicketTypeRepository(session=db_session)
                
                default_ticket_type_data = CreateTicketTypeInput(
                    name="General Admission",
                    price=Decimal("0.00"),  # Free ticket for event creator
                    description="Default ticket type for event attendees",
                    max_quantity=None,  # No limit
                    sale_start_date=None,
                    sale_end_date=None,
                    is_hidden=False,
                    is_waitlistable=True,
                    event_id=event_uuid
                )
                
                ticket_type = await ticket_type_repo.create(ticket_type_data=default_ticket_type_data)
                logger.info(f"Created default ticket type {ticket_type.id} for event {event_id}")
                
                # If we have a creator, create a ticket for them
                if created_by:
                    ticket_repo = TicketRepository(session=db_session)
                    
                    creator_ticket_data = CreateTicketInput(
                        user_id=created_by,
                        event_id=event_uuid,
                        ticket_type_id=ticket_type.id
                    )
                    
                    creator_ticket = await ticket_repo.create(ticket_data=creator_ticket_data)
                    logger.info(f"Created creator ticket {creator_ticket.id} for user {created_by} and event {event_id}")
                
                return {"success": True, "ticket_type_id": str(ticket_type.id)}
                
            except Exception as e:
                logger.error(f"Error in ticket creation process for event {event_id}: {str(e)}")
                raise e
            finally:
                break  # Exit the async generator
    
    # Run the async function using the same pattern as background_tasks.py
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_create_ticket_async())
        logger.info(f"Successfully created default ticket type and creator ticket for event {event_id}")
        return result
    except Exception as exc:
        logger.error(f"Failed to create ticket type/ticket for event {event_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        loop.close()


