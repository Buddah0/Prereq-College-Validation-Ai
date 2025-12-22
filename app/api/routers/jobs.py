from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.schemas.jobs import JobResponse
from app.storage.job_store import JobStore

router = APIRouter()

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    job = JobStore.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
    
@router.get("/", response_model=List[JobResponse])
def list_jobs(limit: int = 10):
    # Warning: .values() is arbitrary order in older python, but creation order in 3.7+
    # We'll reverse list to show newest first
    all_jobs = list(JobStore._jobs.values())
    return sorted(all_jobs, key=lambda x: x['created_at'], reverse=True)[:limit]
