def test_ssrf_guard(client):
    unsafe_urls = [
        "http://localhost/foo",
        "http://127.0.0.1/foo",
        "ftp://example.com/file",
        "file:///etc/passwd",
    ]
    for url in unsafe_urls:
        resp = client.post("/catalogs/", json={"source_url": url})
        assert resp.status_code == 422, f"Should block {url}"
