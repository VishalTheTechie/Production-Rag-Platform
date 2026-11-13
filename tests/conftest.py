import pytest

import audit
import config
import rag


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    # Never call a real LLM in tests
    monkeypatch.setattr(rag, "generate", lambda *a, **k: "stub answer")
    # Use a throwaway audit database
    monkeypatch.setattr(config, "AUDIT_DB", str(tmp_path / "audit.db"))
    audit.init_db()
