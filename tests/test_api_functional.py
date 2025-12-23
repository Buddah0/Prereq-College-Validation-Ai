import json
import time

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_upload_catalog(client, sample_catalog_json):
    file_content = json.dumps(sample_catalog_json).encode('utf-8')
    files = {"file": ("catalog.json", file_content, "application/json")}
    
    resp = client.post("/catalogs/", files=files)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "catalog_id" in data
    assert "file: catalog.json" in data["source"]
    return data["catalog_id"]

def test_upload_bad_json(client):
    files = {"file": ("bad.json", b"{invalid json", "application/json")}
    resp = client.post("/catalogs/", files=files)
    assert resp.status_code == 422

# Mocking httpx for URL ingest using pytest-httpx
def test_url_ingest(httpx_mock, client, sample_catalog_json):
    url = "https://raw.githubusercontent.com/user/repo/main/catalog.json"
    
    # Setup mock response
    httpx_mock.add_response(
        url=url,
        json=sample_catalog_json,
        status_code=200
    )
    
    # Payload
    payload = {"source_url": url}
    resp = client.post("/catalogs/", json=payload)
    
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "catalog_id" in data
    assert "url:" in data["source"]

def test_analysis_flow(client, sample_catalog_json):
    # 1. Upload
    catalog_id = test_upload_catalog(client, sample_catalog_json)
    
    # 2. Start Analysis
    resp = client.post(f"/catalogs/{catalog_id}/analyze")
    assert resp.status_code == 200
    job_data = resp.json()
    job_id = job_data["job_id"]
    assert job_data["status"] == "queued"
    
    # 3. Poll Job
    # Since we are using TestClient and BackgroundTasks, the background task runs synchronously 
    # immediately after the request finishes in recent FastAPI/Starlette versions when using TestClient.
    # So the job should be 'done' immediately.
    
    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    final_job = resp.json()
    assert final_job["status"] == "done"
    assert final_job["report_id"] is not None
    
    # 4. Get Report
    report_id = final_job["report_id"]
    resp = client.get(f"/reports/{report_id}")
    assert resp.status_code == 200
    report = resp.json()
    assert "metrics" in report
    assert report["metrics"]["course_count"] == 3

def test_analyze_not_found(client):
    resp = client.post("/catalogs/non-existent-id/analyze")
    assert resp.status_code == 404
