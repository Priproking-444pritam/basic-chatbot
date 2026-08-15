from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tools import safe_eval


def test_eval_rejects_names():
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('echo pwned')")


def test_cors_health_from_docs_origin():
    client = TestClient(app)
    response = client.get("/api/health", headers={"Origin": "https://example.github.io"})
    assert response.status_code == 200
