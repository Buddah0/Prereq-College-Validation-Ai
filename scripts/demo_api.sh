#!/bin/bash
set -e

# Configuration
API_URL="http://127.0.0.1:8000"
SAMPLE_URL="https://raw.githubusercontent.com/Buddah0/Prereq-College-Validation-Ai/main/samples/sample-output.json"
MAX_RETRIES=30

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[DEMO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Prerequisites check
command -v curl >/dev/null 2>&1 || error "curl is required but not installed."

# Find Python
PYTHON_CMD="python3"
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -f ".wsl_venv/bin/python" ]; then
    PYTHON_CMD=".wsl_venv/bin/python"
fi

log "Using Python: $PYTHON_CMD"

# Helper for JSON parsing
parse_json() {
    # $1 = json string, $2 = key
    echo "$1" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('$2', ''))"
}

# Cleanup trap
cleanup() {
    if [ -n "$SERVER_PID" ]; then
        log "Stopping API server (PID $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# 1. Start Server
log "Starting FastAPI server..."
$PYTHON_CMD -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level error &

SERVER_PID=$!
log "Server PID: $SERVER_PID"

# 2. Wait for Health
log "Waiting for API to be ready..."
count=0
while ! curl -s "${API_URL}/health" > /dev/null; do
    sleep 1
    count=$((count+1))
    if [ $count -ge $MAX_RETRIES ]; then
        error "Timed out waiting for API health check."
    fi
    echo -n "."
done
echo ""
log "API is ready!"

# 3. Ingest Catalog
log "Ingesting catalog from GitHub Raw URL..."
RESPONSE=$(curl -s -X POST "${API_URL}/catalogs/" \
    -H "Content-Type: application/json" \
    -d "{\"source_url\": \"$SAMPLE_URL\"}")

CATALOG_ID=$(parse_json "$RESPONSE" "catalog_id")

if [ -z "$CATALOG_ID" ]; then
    error "Failed to ingest catalog. Response: $RESPONSE"
fi
log "Catalog Ingested. ID: $CATALOG_ID"

# 4. Trigger Analysis
log "Triggering analysis..."
RESPONSE=$(curl -s -X POST "${API_URL}/catalogs/${CATALOG_ID}/analyze")
JOB_ID=$(parse_json "$RESPONSE" "job_id")

if [ -z "$JOB_ID" ]; then
    error "Failed to start analysis. Response: $RESPONSE"
fi
log "Analysis Job Started. ID: $JOB_ID"

# 5. Poll Job Status
log "Polling job status..."
STATUS="queued"
while [ "$STATUS" != "done" ] && [ "$STATUS" != "failed" ]; do
    sleep 1
    RESPONSE=$(curl -s "${API_URL}/jobs/${JOB_ID}")
    STATUS=$(parse_json "$RESPONSE" "status")
    
    if [ "$STATUS" == "failed" ]; then
        error "Job failed. Trace: $(parse_json "$RESPONSE" "error")"
    fi
    echo -n "."
done
echo ""
log "Job Completed!"

# 6. Fetch Report
REPORT_ID=$(parse_json "$RESPONSE" "report_id") # Job response contains report_id on completion
log "Fetching Report: $REPORT_ID..."

REPORT_JSON=$(curl -s "${API_URL}/reports/${REPORT_ID}")

# Extract summary info
# Assuming report structure, adjust keys as needed based on actual report format
TOTAL_COURSES=$(echo "$REPORT_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('courses', [])))")
CYCLES=$(echo "$REPORT_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('cycles', [])))")

echo "---------------------------------------------------"
echo -e "${GREEN}Analysis Report Summary${NC}"
echo "Report ID: $REPORT_ID"
echo "Total Courses: $TOTAL_COURSES"
echo "Detected Cycles: $CYCLES"
echo "---------------------------------------------------"

log "Demo completed successfully."
