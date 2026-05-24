from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class CallRecordIn(BaseModel):
    id: str
    caller_phone: Optional[str] = None
    patient_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    outcome: Optional[str] = None
    transcript: Optional[Any] = None
    audio_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
