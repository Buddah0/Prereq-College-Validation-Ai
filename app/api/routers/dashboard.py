from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.storage.job_store import JobStore
from app.storage.filesystem import load_json_sync
import os
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_graph_elements(report_data):
    # Convert report metrics/structure to Cytoscape elements (nodes+edges)
    # The report contains stats, but for full graph viz we need the raw structure
    # OR we rely on what's in the report if it preserved connections.
    # Current Report schema (analysis_engine.py) doesn't embed the full graph structure!
    # It only has issues and metrics.
    # To viz the graph, we need to load the CATALOG source again or if the report had it.

    # Workaround: Re-load catalog to build graph for visualization.
    # This is slightly inefficient but safe for MVP.
    try:
        from analysis_engine import build_graph_from_catalog

        source_path = report_data.get("source_path")
        if not source_path or not os.path.exists(source_path):
            return []

        g = build_graph_from_catalog(source_path)
        elements = []
        for node in g.nodes():
            elements.append({"data": {"id": str(node)}})
        for u, v in g.edges():
            elements.append({"data": {"source": str(u), "target": str(v)}})
        return elements
    except Exception:
        return []


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    # List available catalogs
    cats = []
    if os.path.exists(settings.CATALOGS_DIR):
        for f in os.listdir(settings.CATALOGS_DIR):
            if f.endswith(".json"):
                path = os.path.join(settings.CATALOGS_DIR, f)
                try:
                    data = load_json_sync(path)
                    if isinstance(data, list):
                        cats.append(
                            {"id": f.replace(".json", ""), "course_count": len(data)}
                        )
                except Exception:
                    pass

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "catalogs": cats}
    )


@router.post("/analyze", response_class=HTMLResponse)
async def dashboard_analyze(
    request: Request, background_tasks: BackgroundTasks, catalog_id: str = Form(...)
):
    # Create job via existing analysis logic
    # We can reuse the service logic directly to avoid code duplication,
    # but analysis.analyze_catalog_endpoint is async and cleaner to call if we mock request or split logic.
    # Better: Use analysis router's underlying service function call pattern.

    # 1. Trigger Job
    # We need to replicate what POST /catalogs/{id}/analyze does
    from app.services.analyze_service import run_analysis_task
    import uuid

    job_id = str(uuid.uuid4())
    JobStore.create_job(job_id)

    # "simple" mode is default for dashboard
    options = {"mode": "simple"}

    background_tasks.add_task(run_analysis_task, job_id, catalog_id, options)

    # Return loading partial
    job = JobStore.get_job(job_id)
    return templates.TemplateResponse(
        "dashboard_results.html", {"request": request, "job": job}
    )


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def dashboard_job_status(request: Request, job_id: str):
    job = JobStore.get_job(job_id)
    if not job:
        return "Job not found"

    context = {"request": request, "job": job}

    if job["status"] == "done":
        # Load report to display results
        report_id = job.get("report_id")
        if report_id:
            report_path = Path(settings.REPORTS_DIR) / f"{report_id}.json"
            if report_path.exists():
                report_data = load_json_sync(str(report_path))
                context["report"] = report_data
                context["graph_elements"] = get_graph_elements(report_data)

    return templates.TemplateResponse("dashboard_results.html", context)
