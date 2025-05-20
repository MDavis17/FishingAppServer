# app/models/log.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LogEntry(BaseModel):
    id: Optional[int] = None
    dateTime: datetime
    species: str
    waterType: str
