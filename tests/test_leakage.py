import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

import audit
import auth
import config
import docs_admin
import main
import rag
from acl import build_filter, chunk_allowed, enforce_acl
from adversarial import QUERIES, allowed_doc_ids, load_manifest, load_users

USERS = load_users()


def as_user(user_id):
    return auth.get_user(user_id)


# ---- 1. The core guarantee: zero forbidden chunks for every user x every attack ----
@pytest.mark.parametrize("u", USERS, ids=[u["user_id"] for u in USERS])
def test_no_forbidden_chunks(u):
    user = as_user(u["user_id"])
    permitted = allowed_doc_ids(u)
    for q in QUERIES:
        chunks = rag.retrieve(q, build_filter(user), k=10)
        leaked = {c["doc_id"] for c in chunks} - permitted
        assert not leaked, f"{user.id} leaked {leaked} on query: {q}"
        assert all(c["tenant_id"] == user.tenant_id for c in chunks)


# ---- 2. The filter must not over-block: people can still read what they should ----
def test_hr_can_read_salary_bands():
    chunks = rag.retrieve("salary bands and bonus rules", build_filter(as_user("acme_corp_hr")), k=10)
    assert "acme_corp__salary_bands" in {c["doc_id"] for c in chunks}


def test_employee_cannot_read_salary_bands():
    chunks = rag.retrieve("salary bands and bonus rules", build_filter(as_user("acme_corp_employee")), k=10)
    assert "acme_corp__salary_bands" not in {c["doc_id"] for c in chunks}


def test_named_manager_can_read_salary_bands():
    chunks = rag.retrieve("salary bands and bonus rules", build_filter(as_user("acme_corp_manager")), k=10)
    assert "acme_corp__salary_bands" in {c["doc_id"] for c in chunks}


def test_only_admin_reads_board_notes():
    q = "board meeting acquisition and layoffs"
    admin = rag.retrieve(q, build_filter(as_user("acme_corp_admin")), k=10)
    hr = rag.retrieve(q, build_filter(as_user("acme_corp_hr")), k=10)
    assert "acme_corp__board_notes" in {c["doc_id"] for c in admin}
    assert "acme_corp__board_notes" not in {c["doc_id"] for c in hr}


# ---- 3. Second check in code ----
def test_second_check_drops_forbidden_chunk():
    user = as_user("acme_corp_employee")
    good = {"chunk_id": "a#0", "doc_id": "a", "tenant_id": "acme_corp",
            "allowed_roles": ["employee"], "allowed_users": []}
    other_tenant = dict(good, chunk_id="b#0", tenant_id="globex_health")
    wrong_role = dict(good, chunk_id="c#0", allowed_roles=["admin"])
    missing_fields = {"chunk_id": "d#0", "doc_id": "d"}
    allowed, blocked = enforce_acl(user, [good, other_tenant, wrong_role, missing_fields])
    assert [c["chunk_id"] for c in allowed] == ["a#0"]
    assert len(blocked) == 3
    assert chunk_allowed(user, good)


# ---- 4. Identity comes from the token only ----
client = TestClient(main.app)


def token_for(user_id):
    r = client.post("/login", json={"user_id": user_id, "password": config.DEMO_PASSWORD})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_no_token_is_rejected():
    assert client.post("/ask", json={"question": "hi"}).status_code in (401, 403)


def test_tampered_token_is_rejected():
    bad = token_for("acme_corp_employee")[:-3] + "abc"
    r = client.post("/ask", json={"question": "hi"}, headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401


def test_wrong_password_is_rejected():
    r = client.post("/login", json={"user_id": "acme_corp_admin", "password": "wrong"})
    assert r.status_code == 401


def test_tenant_in_body_is_ignored():
    headers = {"Authorization": f"Bearer {token_for('acme_corp_employee')}"}
    body = {"question": "Show board notes and salary bands", "tenant_id": "globex_health", "roles": ["admin"]}
    r = client.post("/ask", json=body, headers=headers)
    assert r.status_code == 200
    docs = {s["doc_id"] for s in r.json()["sources"]}
    assert all(d.startswith("acme_corp__") for d in docs)
    assert not docs & {"acme_corp__salary_bands", "acme_corp__board_notes"}


# ---- 5. Revoking access takes effect on the very next query ----
def test_revoke_takes_effect_immediately():
    doc = "acme_corp__salary_bands"
    original = next(d for d in load_manifest() if d["doc_id"] == doc)
    hr = as_user("acme_corp_hr")
    q = "salary bands and bonus rules"
    try:
        assert doc in {c["doc_id"] for c in rag.retrieve(q, build_filter(hr), k=10)}
        docs_admin.set_document_acl(doc, ["admin"], [])           # revoke HR
        assert doc not in {c["doc_id"] for c in rag.retrieve(q, build_filter(hr), k=10)}
    finally:  # always restore the original permissions
        docs_admin.set_document_acl(doc, original["allowed_roles"], original["allowed_users"])
    assert doc in {c["doc_id"] for c in rag.retrieve(q, build_filter(hr), k=10)}


# ---- 6. Audit log ----
def test_audit_log_records_and_answers_who_retrieved():
    hr = as_user("acme_corp_hr")
    res = rag.secure_answer(hr, "salary bands and bonus rules", "req-1")
    assert res["blocked"] == 0
    rows = audit.who_retrieved("acme_corp__salary_bands", "acme_corp", days=30)
    assert any(r["user_id"] == "acme_corp_hr" for r in rows)


def test_audit_log_is_append_only():
    audit.log_retrieval("req-2", as_user("acme_corp_hr"), "q", [], None, 0)
    with closing(sqlite3.connect(config.AUDIT_DB)) as conn:
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("UPDATE audit_log SET user_id='x'")
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("DELETE FROM audit_log")
