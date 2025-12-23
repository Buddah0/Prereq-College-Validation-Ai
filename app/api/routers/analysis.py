from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.jobs import JobResponse, JobCreate
from app.schemas.common import ErrorResponse
from app.storage.job_store import JobStore
from app.services.analyze_service import run_analysis_task
from app.core.config import settings
from pathlib import Path

router = APIRouter()

@router.post("/{catalog_id}/analyze", response_model=JobResponse, responses={404: {"model": ErrorResponse}})
def analyze_catalog_endpoint(
    catalog_id: str,
    background_tasks: BackgroundTasks,
    options: dict = {}
):
    # check if catalog exists
    # Although run_analysis_task checks it, checking here gives immediate 404
    path = Path(settings.CATALOGS_DIR) / f"{catalog_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Catalog not found")
        
    # Create job
    job_id = JobStore.create_job(catalog_id)
    
    # Enqueue task
    background_tasks.add_task(run_analysis_task, job_id, catalog_id, options)
    
    # Return queued job
    job = JobStore.get_job(job_id)
    return job
