from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.core.config import settings
from app.storage.filesystem import load_json_sync

router = APIRouter()

@router.get("/{report_id}")
def get_report(report_id: str):
    """
    Returns the full JSON report.
    We don't use a strict Pydantic model response to allow flexibility with the legacy report format.
    """
    path = Path(settings.REPORTS_DIR) / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        data = load_json_sync(str(path))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")
