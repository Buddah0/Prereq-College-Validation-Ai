from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


JobStatus = Literal["queued", "running", "done", "failed"]


class JobCreate(BaseModel):
    catalog_id: str
    options: dict = {}


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    catalog_id: str
    report_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
