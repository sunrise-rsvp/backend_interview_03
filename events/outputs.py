from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class EventOutput(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True


class EventListOutput(BaseModel):
    events: list[EventOutput]
    total: int


class EventCountOutput(BaseModel):
    count: int
