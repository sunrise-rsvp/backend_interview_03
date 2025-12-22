from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserOutput(BaseModel):
    id: UUID
    email: str
    password_hash: str
    api_key: Optional[str]

    class Config:
        from_attributes = True
