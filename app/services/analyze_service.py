import asyncio
from typing import Optional
from pathlib import Path
from app.core.config import settings
from app.storage.job_store import JobStore
from app.storage.filesystem import save_json_sync

# We import the existing engine logic
# We must ensure the project root is in sys.path or accessible
import sys
# Assuming app is running from root, these imports should work
try:
    from analysis_engine import analyze_catalog, write_report_json
except ImportError:
    # If running as app.services.analyze_service, we might need path hack if not installed as package
    import os
    sys.path.append(os.getcwd())
    from analysis_engine import analyze_catalog, write_report_json

def run_analysis_task(job_id: str, catalog_id: str, options: dict):
    """
    This function runs in the background.
    It performs the CPU-bound analysis. 
    Since the analysis engine is sync, we can run it here directly.
    If it blocks the event loop significantly, we should use run_in_executor.
    """
    try:
        JobStore.update_job(job_id, status="running")
        
        # Locate catalog file
        catalog_path = Path(settings.CATALOGS_DIR) / f"{catalog_id}.json"
        
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog {catalog_id} not found")
            
        # Run analysis (Sync call)
        # Note: In a high-throughput async app, we'd run this in a thread pool:
        # report = await loop.run_in_executor(None, analyze_catalog, str(catalog_path), options)
        # But for 'Simple async analysis mode' request, direct call in BackgroundTask is accepted 
        # (BackgroundTask runs in a thread pool automatically? No, only def functions. async def awaitable is awaited on loop)
        # We will make this function synchronous so FastAPI runs it in threadpool.
        
        report = analyze_catalog(str(catalog_path), config=options)
        
        # Save report
        report_id = save_json_sync(report.to_dict(), settings.REPORTS_DIR)
        
        JobStore.update_job(job_id, status="done", report_id=report_id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        JobStore.update_job(job_id, status="failed", error=str(e))
