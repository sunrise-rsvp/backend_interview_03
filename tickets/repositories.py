from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from tickets.orm import Ticket, TicketType
from tickets.inputs import CreateTicketInput, CreateTicketTypeInput, UpdateTicketInput


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket_data: CreateTicketInput) -> Ticket:
        """Create a new ticket"""
        ticket = Ticket(
            user_id=ticket_data.user_id,
            event_id=ticket_data.event_id,
            ticket_type_id=ticket_data.ticket_type_id
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def update(self, ticket_id: UUID, ticket_data: UpdateTicketInput) -> Optional[Ticket]:
        """Update an existing ticket"""
        # Build update dict excluding None values and ID
        update_data = {
            key: value for key, value in ticket_data.dict().items() 
            if value is not None
        }
        
        if not update_data:
            # If no data to update, return None
            return None
        
        stmt = (
            update(Ticket)
            .where(and_(Ticket.id == ticket_id, Ticket.is_active == True))
            .values(**update_data)
            .returning(Ticket)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, ticket_id: UUID) -> bool:
        """Soft delete a ticket by setting is_active to False"""
        stmt = (
            update(Ticket)
            .where(and_(Ticket.id == ticket_id, Ticket.is_active == True))
            .values(is_active=False)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


class TicketTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket_type_data: CreateTicketTypeInput) -> TicketType:
        """Create a new ticket type"""
        ticket_type = TicketType(
            name=ticket_type_data.name,
            price=ticket_type_data.price,
            description=ticket_type_data.description,
            max_quantity=ticket_type_data.max_quantity,
            sale_start_date=ticket_type_data.sale_start_date,
            sale_end_date=ticket_type_data.sale_end_date,
            is_hidden=ticket_type_data.is_hidden,
            is_waitlistable=ticket_type_data.is_waitlistable,
            event_id=ticket_type_data.event_id
        )
        self.session.add(ticket_type)
        await self.session.commit()
        await self.session.refresh(ticket_type)
        return ticket_type

    async def delete(self, ticket_type_id: UUID) -> bool:
        """Soft delete a ticket type by setting is_active to False"""
        stmt = (
            update(TicketType)
            .where(and_(TicketType.id == ticket_type_id, TicketType.is_active == True))
            .values(is_active=False)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
