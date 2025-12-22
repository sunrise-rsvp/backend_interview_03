from datetime import datetime
from typing import Optional
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field


class CreateTicketTypeInput(BaseModel):
    name: str = Field(..., max_length=255)
    price: Decimal = Field(..., ge=0)
    description: Optional[str] = None
    max_quantity: Optional[int] = Field(None, ge=0)
    sale_start_date: Optional[datetime] = None
    sale_end_date: Optional[datetime] = None
    is_hidden: bool = False
    is_waitlistable: bool = False
    event_id: UUID


class CreateTicketInput(BaseModel):
    user_id: Optional[str] = Field(None, max_length=255)
    event_id: UUID
    ticket_type_id: UUID


class UpdateTicketInput(BaseModel):
    user_id: Optional[str] = Field(None, max_length=255)
    is_checked_in: Optional[bool] = None
