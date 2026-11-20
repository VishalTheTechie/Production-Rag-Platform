import auth
import audit
import cache
import config
import corpus
import docs_admin
import metrics
import pipeline

Q = "What is the annual bonus payout date?"


def ask(user_id, q=Q, mode="optimized"):
    return pipeline.answer(auth.get_user(user_id), q, "rid", mode=mode, run_label="test")


def test_normalize():
    assert cache.normalize("  How do I RESET my password?? ") == "how do i reset my password"


def test_repeat_question_hits_cache():
    assert ask("acme_corp_hr")["cache_hit"] is False
    assert ask("acme_corp_hr")["cache_hit"] is True


def test_cache_is_not_shared_across_tenants():
    ask("acme_corp_hr")
    assert ask("globex_health_hr")["cache_hit"] is False


def test_cache_is_not_shared_across_roles():
    ask("acme_corp_admin")                      # admin may see confidential documents
    assert ask("acme_corp_employee")["cache_hit"] is False


def test_named_user_gets_private_scope():
    # acme_corp_manager is personally named on salary_bands, so must not share with plain employees
    assert cache.access_scope(auth.get_user("acme_corp_manager")).endswith("|u:acme_corp_manager")
    assert "|u:" not in cache.access_scope(auth.get_user("acme_corp_employee"))


def test_corpus_version_bump_invalidates_cache():
    ask("acme_corp_hr")
    corpus.bump_version()
    assert ask("acme_corp_hr")["cache_hit"] is False


def test_acl_change_invalidates_cache():
    ask("acme_corp_hr")
    assert ask("acme_corp_hr")["cache_hit"] is True
    docs_admin.set_document_acl("acme_corp__salary_bands", ["hr", "admin"], ["acme_corp_manager"])
    assert ask("acme_corp_hr")["cache_hit"] is False


def test_idk_answers_are_not_cached(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_ex", lambda *a, **k: {
        "text": "I don't know.", "input_tokens": 50, "output_tokens": 5, "model": "groq:openai/gpt-oss-120b"})
    ask("acme_corp_hr")
    assert ask("acme_corp_hr")["cache_hit"] is False


def test_cache_hit_is_audited_and_costs_nothing():
    ask("acme_corp_hr")
    r = ask("acme_corp_hr")
    assert r["cache_hit"] and r["cost_usd"] == 0.0
    rows = audit.who_retrieved(r["sources"][0]["doc_id"], "acme_corp", days=1)
    assert len(rows) >= 2


def test_escalation_when_small_model_answer_is_weak(monkeypatch):
    calls = []

    def weak_then_good(prompt, model=None, json_mode=False, tries=3):
        calls.append(model)
        text = "I don't know." if len(calls) == 1 else "Good answer [acme_corp__handbook#0]"
        return {"text": text, "input_tokens": 80, "output_tokens": 8, "model": "groq:x"}

    monkeypatch.setattr(pipeline, "generate_ex", weak_then_good)
    r = ask("acme_corp_hr", "What is the bonus date?")        # short, simple question
    assert r["route"] == "simple" and r["escalated"] is True and len(calls) == 2


def test_baseline_mode_never_uses_cache():
    ask("acme_corp_hr", mode="baseline")
    r = ask("acme_corp_hr", mode="baseline")
    assert r["cache_hit"] is False and r["route"] == "large"


def test_requests_are_logged_with_cost():
    ask("acme_corp_hr")
    df = metrics.load("test")
    assert len(df) == 1 and df.cost_usd.iloc[0] > 0


def test_number_guard_blocks_different_level(monkeypatch):
    monkeypatch.setattr(config, "CACHE_THRESHOLD", 0.0)       # let the guard make the decision
    ask("acme_corp_hr", "What is the bonus target for L4 employees?")
    assert ask("acme_corp_hr", "What is the bonus target for L5 employees?")["cache_hit"] is False


def test_verifier_can_reject_and_accept(monkeypatch):
    monkeypatch.setattr(config, "CACHE_THRESHOLD", 0.0)
    monkeypatch.setattr(config, "VERIFY_ENABLED", True, raising=False)
    monkeypatch.setattr(config, "VERIFY_THRESHOLD", 0.5, raising=False)
    ask("acme_corp_hr", "What is the bonus payout date?")
    monkeypatch.setattr(cache.verifier, "same_question_score", lambda a, b: 0.1)
    assert ask("acme_corp_hr", "When are bonuses paid?")["cache_hit"] is False
    monkeypatch.setattr(cache.verifier, "same_question_score", lambda a, b: 0.9)
    assert ask("acme_corp_hr", "When do annual bonuses get paid out?")["cache_hit"] is True


def test_latency_excludes_rate_limit_waiting(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_ex", lambda *a, **k: {
        "text": "ok [acme_corp__handbook#0]", "input_tokens": 10, "output_tokens": 5,
        "model": "groq:openai/gpt-oss-20b", "waited_s": 500.0})
    r = ask("acme_corp_hr", "How many holidays are there?")
    assert r["latency_ms"] < 5_000          # the 500 s of "waiting" is not counted as latency
