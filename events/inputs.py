from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateEventInput(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    start_date: datetime
    end_date: datetime
    created_by: Optional[str] = Field(None, max_length=255)


class UpdateEventInput(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
