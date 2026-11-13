"""Logs every request (cost, tokens, latency, route, quality) to SQLite."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import pandas as pd

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  run_label TEXT NOT NULL,
  request_id TEXT,
  user_id TEXT,
  tenant_id TEXT,
  query TEXT,
  cache_hit INTEGER,
  route TEXT,
  model TEXT,
  escalated INTEGER,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  latency_ms REAL,
  correct INTEGER
);
"""


def init_db():
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def cost_usd(model_label, tokens_in, tokens_out):
    """Cost = tokens x price table. Prices are per 1M tokens (see config.PRICES)."""
    name = (model_label or "").split(":", 1)[-1]
    p_in, p_out = config.PRICES.get(name, config.DEFAULT_PRICE)
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000


def log_request(run_label, request_id, user, query, cache_hit, route, model,
                escalated, tokens_in, tokens_out, cost, latency_ms):
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        cur = conn.execute(
            "INSERT INTO requests (ts, run_label, request_id, user_id, tenant_id, query, cache_hit,"
            " route, model, escalated, input_tokens, output_tokens, cost_usd, latency_ms)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), run_label, request_id, user.id, user.tenant_id,
             query, int(cache_hit), route, model, int(escalated), tokens_in, tokens_out, cost, latency_ms),
        )
        conn.commit()
        return cur.lastrowid


def set_quality(row_id, correct):
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        conn.execute("UPDATE requests SET correct=? WHERE id=?", (int(bool(correct)), row_id))
        conn.commit()


def count_rows(run_label):
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        return conn.execute("SELECT COUNT(*) FROM requests WHERE run_label=?", (run_label,)).fetchone()[0]


def clear_run(run_label):
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        conn.execute("DELETE FROM requests WHERE run_label=?", (run_label,))
        conn.commit()


def load(run_label=None):
    with closing(sqlite3.connect(config.METRICS_DB)) as conn:
        if run_label:
            return pd.read_sql("SELECT * FROM requests WHERE run_label=? ORDER BY id", conn, params=(run_label,))
        return pd.read_sql("SELECT * FROM requests ORDER BY id", conn)


init_db()
