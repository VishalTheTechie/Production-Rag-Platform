"""Append-only audit log in SQLite. Database triggers block UPDATE and DELETE."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  request_id TEXT,
  event_type TEXT NOT NULL,
  user_id TEXT,
  tenant_id TEXT,
  query TEXT,
  doc_ids TEXT,
  chunk_ids TEXT,
  model TEXT,
  blocked_count INTEGER DEFAULT 0
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""


def init_db():
    with closing(sqlite3.connect(config.AUDIT_DB)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _insert(event_type, request_id, user, query, doc_ids, chunk_ids, model, blocked):
    with closing(sqlite3.connect(config.AUDIT_DB)) as conn:
        conn.execute(
            "INSERT INTO audit_log (ts, request_id, event_type, user_id, tenant_id, query,"
            " doc_ids, chunk_ids, model, blocked_count) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (_now(), request_id, event_type, user.id, user.tenant_id, query,
             json.dumps(doc_ids), json.dumps(chunk_ids), model, blocked),
        )
        conn.commit()


def log_retrieval(request_id, user, query, chunks, model, blocked_count=0):
    _insert(
        "retrieval", request_id, user, query,
        sorted({c["doc_id"] for c in chunks}), [c["chunk_id"] for c in chunks],
        model, blocked_count,
    )


def log_acl_change(request_id, admin, doc_id, allowed_roles, allowed_users):
    detail = f"ACL change on {doc_id}: roles={allowed_roles} users={allowed_users}"
    _insert("acl_change", request_id, admin, detail, [doc_id], [], None, 0)


def who_retrieved(doc_id, tenant_id, days=30):
    """Answers: who retrieved document X in the last N days?"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with closing(sqlite3.connect(config.AUDIT_DB)) as conn:
        rows = conn.execute(
            "SELECT ts, user_id, request_id, query FROM audit_log"
            " WHERE event_type='retrieval' AND tenant_id=? AND ts>=? AND doc_ids LIKE ?"
            " ORDER BY ts DESC",
            (tenant_id, cutoff, f'%"{doc_id}"%'),
        ).fetchall()
    return [{"ts": r[0], "user_id": r[1], "request_id": r[2], "query": r[3]} for r in rows]


init_db()
