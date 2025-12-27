import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import shutil
from app.core.config import settings


@pytest.fixture(scope="module")
def client():
    # Use a separate test data directory
    original_data_dir = settings.DATA_DIR
    original_catalogs = settings.CATALOGS_DIR
    original_reports = settings.REPORTS_DIR

    test_dir = "test_data"
    settings.DATA_DIR = test_dir
    settings.CATALOGS_DIR = f"{test_dir}/catalogs"
    settings.REPORTS_DIR = f"{test_dir}/reports"

    os.makedirs(settings.CATALOGS_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    # Restore (though settings object persists, this is module scope usually fine)
    settings.DATA_DIR = original_data_dir
    settings.CATALOGS_DIR = original_catalogs
    settings.REPORTS_DIR = original_reports


@pytest.fixture
def sample_catalog_json():
    return [
        {"id": "CS101", "name": "Intro to CS", "prerequisites": []},
        {"id": "CS102", "name": "Data Structures", "prerequisites": ["CS101"]},
        {"id": "MATH101", "name": "Calc I", "prerequisites": []},
    ]
