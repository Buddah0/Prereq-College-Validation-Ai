from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    """
    Standard error response model (Problem Details style).
    """

    detail: str
    status_code: int
    type: Optional[str] = None
    instance: Optional[str] = None
    additional_info: Optional[dict[str, Any]] = None
