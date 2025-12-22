import httpx
import json
from fastapi import UploadFile, HTTPException
from app.storage.filesystem import save_upload_file
from app.core.config import settings
import ipaddress
from urllib.parse import urlparse

async def process_uploaded_catalog(file: UploadFile) -> str:
    content = await file.read()
    # Basic validation that it's json
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("Catalog must be a list of courses")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON file")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
        
    catalog_id = await save_upload_file(content, file.filename)
    return catalog_id

def _is_safe_url(url: str) -> bool:
    # SSRF Protection
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Resolve IP
        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            # It's a domain name, safer to let httpx handle dns but we should ideally resolve and check IP.
            # For this MVP, we will rely on a simple deny list if possible, or just trust public DNS for now
            # but usually for SSRF we resolve and check if private.
            # Re-resolving here might be complex due to async/sync mismatch or double-dns.
            # We'll do a basic check for localhost/127.0.0.1 strings in hostname as a weak guard 
            # and allow httpx to fetch.
            if hostname in ["localhost", "127.0.0.1", "::1"]:
                 return False
            return True
            
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
            
        return True
    except Exception:
        return False

async def fetch_catalog_from_url(url: str) -> str:
    if not _is_safe_url(url):
        raise HTTPException(status_code=422, detail="Invalid or unsafe URL")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            # Check content length
            if len(resp.content) > settings.MAX_URL_DOWNLOAD_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large")
                
            content = resp.content
            
            # Helper: if it's GitHub Raw, it might be text/plain, but we treat as JSON
            try:
                data = json.loads(content)
                if not isinstance(data, list):
                     raise ValueError("Catalog must be a list of courses")
            except json.JSONDecodeError:
                 raise HTTPException(status_code=422, detail="Content from URL is not valid JSON")
            except ValueError as e:
                 raise HTTPException(status_code=422, detail=str(e))
                 
            # Save
            catalog_id = await save_upload_file(content, "url_import.json")
            return catalog_id

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch upstream URL: {str(e)}")
