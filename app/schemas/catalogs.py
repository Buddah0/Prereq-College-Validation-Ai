from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class CatalogIngestURL(BaseModel):
    source_url: HttpUrl

class CatalogResponse(BaseModel):
    catalog_id: str
    stored_at: datetime
    message: str
    source: str
