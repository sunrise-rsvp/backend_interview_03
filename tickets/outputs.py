from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class TicketTypeOutput(BaseModel):
    id: UUID
    name: str
    price: Decimal
    description: Optional[str]
    max_quantity: Optional[int]
    sale_start_date: Optional[datetime]
    sale_end_date: Optional[datetime]
    is_hidden: bool
    is_waitlistable: bool
    event_id: UUID

    class Config:
        from_attributes = True


class TicketOutput(BaseModel):
    id: UUID
    user_id: Optional[str]
    event_id: UUID
    ticket_type_id: UUID
    is_checked_in: bool

    class Config:
        from_attributes = True


class TicketListOutput(BaseModel):
    tickets: List[TicketOutput]
    total: int
