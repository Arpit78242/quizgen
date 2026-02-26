from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class SourceOut(BaseModel):
    id: UUID
    source_type: str
    file_name: Optional[str]
    topic: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
