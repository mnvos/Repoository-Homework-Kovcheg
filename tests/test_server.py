import os
import json
from importlib import reload
from fastapi.testclient import TestClient


def test_export_and_import_protection(tmp_path, monkeypatch):
    # Prepare environment before importing server.main
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("ADMIN_API_KEY", "secretkey")
    kb_file = tmp_path / "kb.json"
    kb_file.write_text(json.dumps({"meta": {}, "topics": []}))
    monkeypatch.setenv("DATABASE_URL", str(kb_file))

    # Import server after env set
    import server.main as server_main
    reload(server_main)
    client = TestClient(server_main.app)

    # Export should be accessible without key
    r = client.get("/kb/export")
    assert r.status_code == 200

    # Import without key should be unauthorized
    r = client.post("/kb/import", json={"meta": {}, "topics": []})
    assert r.status_code == 401

    # Import with correct key should work
    r = client.post("/kb/import", headers={"X-API-KEY": "secretkey"}, json={"meta": {}, "topics": []})
    assert r.status_code == 200