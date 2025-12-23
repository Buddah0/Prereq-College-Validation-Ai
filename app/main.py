from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from app.api.routers import analysis, catalogs, health, jobs, reports
from app.core.config import settings
from app.schemas.common import ErrorResponse


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            status_code=exc.status_code,
            type="HTTPException",
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Validation Error",
            status_code=422,
            type="ValidationError",
            additional_info={"errors": exc.errors()},
        ).model_dump(),
    )


# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(catalogs.router, prefix="/catalogs", tags=["Catalogs"])
app.include_router(analysis.router, prefix="/catalogs", tags=["Analysis"])  # Nested under catalogs for /{id}/analyze
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
