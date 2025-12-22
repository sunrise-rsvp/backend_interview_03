from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Base
import uuid


class TicketType(Base):
    __tablename__ = "ticket_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    max_quantity = Column(Integer, nullable=True, default=None)
    sale_start_date = Column(DateTime, nullable=True)
    sale_end_date = Column(DateTime, nullable=True)
    is_hidden = Column(Boolean, default=False, nullable=False)
    is_waitlistable = Column(Boolean, default=False, nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="ticket_types")
    tickets = relationship("Ticket", back_populates="ticket_type")

    @classmethod
    async def get_by_event_id(cls, event_id: uuid.UUID, db: AsyncSession) -> List['TicketType']:
        """Fetch all ticket types for an event"""
        stmt = select(cls).where(cls.event_id == event_id, cls.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def bulk_get(cls, ids: List[uuid.UUID], db: AsyncSession) -> List['TicketType']:
        """Fetch multiple ticket types by IDs"""
        stmt = select(cls).where(cls.id.in_(ids), cls.is_active == True)
        result = await db.execute(stmt)
        return result.scalars().all()

    def __repr__(self):
        return f"<TicketType(name='{self.name}')>"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    ticket_type_id = Column(UUID(as_uuid=True), ForeignKey("ticket_types.id"), nullable=False)
    is_checked_in = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="tickets")
    ticket_type = relationship("TicketType", back_populates="tickets")

    def __repr__(self):
        return f"<Ticket(id='{self.id}', user_id='{self.user_id}')>"
