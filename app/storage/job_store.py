from datetime import datetime, timedelta
import uuid
from typing import Dict, Optional
from app.schemas.jobs import JobStatus

class JobStore:
    _jobs: Dict[str, dict] = {}
    
    @classmethod
    def create_job(cls, catalog_id: str) -> str:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        cls._jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "catalog_id": catalog_id,
            "created_at": now,
            "updated_at": now,
            "report_id": None,
            "error": None
        }
        return job_id

    @classmethod
    def get_job(cls, job_id: str) -> Optional[dict]:
        return cls._jobs.get(job_id)

    @classmethod
    def update_job(cls, job_id: str, status: JobStatus, report_id: Optional[str] = None, error: Optional[str] = None):
        if job_id in cls._jobs:
            cls._jobs[job_id]["status"] = status
            cls._jobs[job_id]["updated_at"] = datetime.utcnow()
            if report_id:
                cls._jobs[job_id]["report_id"] = report_id
            if error:
                cls._jobs[job_id]["error"] = error

    @classmethod
    def cleanup_old_jobs(cls, ttl_seconds: int = 7200):
        cutoff = datetime.utcnow() - timedelta(seconds=ttl_seconds)
        to_remove = [
            jid for jid, job in cls._jobs.items() 
            if job["updated_at"] < cutoff and job["status"] in ("done", "failed")
        ]
        for jid in to_remove:
            del cls._jobs[jid]
