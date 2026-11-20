import pytest

import audit
import cache
import config
import corpus
import metrics
import pipeline
import rag


def fake_generate_ex(prompt, model=None, json_mode=False, tries=3):
    return {"text": "stub answer [acme_corp__handbook#0]", "input_tokens": 100,
            "output_tokens": 10, "model": "groq:openai/gpt-oss-20b"}


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    # Never call a real LLM in tests
    monkeypatch.setattr(rag, "generate", lambda *a, **k: "stub answer")
    monkeypatch.setattr(pipeline, "generate_ex", fake_generate_ex)
    # Throwaway databases, cache collection and corpus version file
    monkeypatch.setattr(config, "AUDIT_DB", str(tmp_path / "audit.db"))
    monkeypatch.setattr(config, "METRICS_DB", str(tmp_path / "metrics.db"))
    monkeypatch.setattr(config, "CACHE_COLLECTION", "cache_test")
    monkeypatch.setattr(config, "VERIFY_ENABLED", False, raising=False)
    monkeypatch.setattr(corpus, "VERSION_FILE", tmp_path / "corpus_version.txt")
    audit.init_db()
    metrics.init_db()
    cache.reset()
    cache._personal.clear()
    yield
    if cache.client.collection_exists("cache_test"):
        cache.client.delete_collection("cache_test")
