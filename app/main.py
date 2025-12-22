from fastapi import FastAPI
from app.core.config import settings
from app.api.routers import health, catalogs, analysis, jobs, reports

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(catalogs.router, prefix="/catalogs", tags=["Catalogs"])
app.include_router(analysis.router, prefix="/catalogs", tags=["Analysis"]) # Nested under catalogs for /{id}/analyze
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
