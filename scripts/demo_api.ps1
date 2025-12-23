$ErrorActionPreference = "Stop"

# Configuration
$API_URL = "http://127.0.0.1:8000"
$SAMPLE_URL = "https://raw.githubusercontent.com/Buddah0/Prereq-College-Validation-Ai/main/samples/sample-output.json"
$MAX_RETRIES = 30

function Log-Message {
    param([string]$Message)
    Write-Host "[DEMO] $Message" -ForegroundColor Green
}

function Error-Exit {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    if ($Global:ServerProcess) {
        Stop-Process -Id $Global:ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

# Cleanup
try {
    Log-Message "Starting FastAPI server..."
    $Global:ServerProcess = Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "error" -PassThru -NoNewWindow
    Log-Message "Server PID: $($Global:ServerProcess.Id)"

    # Wait for Health
    Log-Message "Waiting for API to be ready..."
    $count = 0
    do {
        Start-Sleep -Seconds 1
        $count++
        try {
            $response = Invoke-RestMethod -Uri "$API_URL/health" -Method Get -ErrorAction Stop
            $baseHealth = $true
        }
        catch {
            $baseHealth = $false
        }
    } until ($baseHealth -or $count -ge $MAX_RETRIES)

    if (-not $baseHealth) {
        Error-Exit "Timed out waiting for API health check."
    }
    Log-Message "API is ready!"

    # Ingest Catalog
    Log-Message "Ingesting catalog from GitHub Raw URL..."
    $body = @{ source_url = $SAMPLE_URL } | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/catalogs/" -Method Post -Body $body -ContentType "application/json"
        $CATALOG_ID = $response.catalog_id
    }
    catch {
        Error-Exit "Failed to ingest catalog. $_"
    }
    Log-Message "Catalog Ingested. ID: $CATALOG_ID"

    # Analysis
    Log-Message "Triggering analysis..."
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/catalogs/$CATALOG_ID/analyze" -Method Post
        $JOB_ID = $response.job_id
    }
    catch {
        Error-Exit "Failed to start analysis. $_"
    }
    Log-Message "Analysis Job Started. ID: $JOB_ID"

    # Poll Job
    Log-Message "Polling job status..."
    $status = "queued"
    while ($status -ne "done" -and $status -ne "failed") {
        Start-Sleep -Seconds 1
        $response = Invoke-RestMethod -Uri "$API_URL/jobs/$JOB_ID" -Method Get
        $status = $response.status
        Write-Host -NoNewline "."
        
        if ($status -eq "failed") {
            Error-Exit "Job failed. Trace: $($response.error)"
        }
    }
    Write-Host ""
    Log-Message "Job Completed!"
    $REPORT_ID = $response.report_id

    # Fetch Report
    Log-Message "Fetching Report: $REPORT_ID..."
    $report = Invoke-RestMethod -Uri "$API_URL/reports/$REPORT_ID" -Method Get

    $totalCourses = if ($report.courses) { $report.courses.Count } else { 0 }
    $cycles = if ($report.cycles) { $report.cycles.Count } else { 0 }

    Write-Host "---------------------------------------------------"
    Write-Host "Analysis Report Summary" -ForegroundColor Green
    Write-Host "Report ID: $REPORT_ID"
    Write-Host "Total Courses: $totalCourses"
    Write-Host "Detected Cycles: $cycles"
    Write-Host "---------------------------------------------------"

}
catch {
    Error-Exit "Unexpected error: $_"
}
finally {
    if ($Global:ServerProcess) {
        Log-Message "Stopping API server..."
        Stop-Process -Id $Global:ServerProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
