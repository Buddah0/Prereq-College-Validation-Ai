import json
import aiofiles
from pathlib import Path
from app.core.config import settings

async def save_upload_file(file_content: bytes, filename: str) -> str:
    # Generate unique ID for the catalog
    import uuid
    catalog_id = str(uuid.uuid4())
    # Use catalog_id as filename stem
    dest_path = Path(settings.CATALOGS_DIR) / f"{catalog_id}.json"
    
    async with aiofiles.open(dest_path, 'wb') as f:
        await f.write(file_content)
        
    return catalog_id

def save_json_sync(data: list | dict, directory: str) -> str:
    import uuid
    file_id = str(uuid.uuid4())
    dest_path = Path(directory) / f"{file_id}.json"
    with open(dest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return file_id

def load_json_sync(path: str) -> dict | list:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
