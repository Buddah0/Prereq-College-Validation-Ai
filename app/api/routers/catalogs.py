from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from app.schemas.catalogs import CatalogResponse
from app.schemas.common import ErrorResponse
from app.services.ingest_service import process_uploaded_catalog, fetch_catalog_from_url

router = APIRouter()

@router.post("/", response_model=CatalogResponse, responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 415: {"model": ErrorResponse}})
async def create_catalog(request: Request):
    """
    Ingest a catalog via file upload OR URL.
    - Multipart/Form-Data: `file` field.
    - JSON: `{"source_url": "..."}`.
    """
    content_type = request.headers.get("content-type", "")
    
    catalog_id = None
    source = ""
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
             raise HTTPException(status_code=422, detail="Missing 'file' in form data")
        if not hasattr(file, "filename"):
             raise HTTPException(status_code=422, detail="'file' must be an upload")
             
        catalog_id = await process_uploaded_catalog(file)
        source = f"file: {file.filename}"
        
    elif "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid JSON body")
            
        source_url = body.get("source_url")
        if not source_url:
            raise HTTPException(status_code=422, detail="Missing 'source_url' in JSON body")
            
        catalog_id = await fetch_catalog_from_url(source_url)
        source = f"url: {source_url}"
        
    else:
        raise HTTPException(status_code=415, detail="Content-Type must be 'multipart/form-data' or 'application/json'")

    return CatalogResponse(
        catalog_id=catalog_id,
        stored_at=datetime.utcnow(),
        message="Catalog ingested successfully",
        source=source
    )
