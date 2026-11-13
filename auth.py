"""Login + JWT tokens. Identity ALWAYS comes from the verified token, never from a request body."""
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

import config


@dataclass(frozen=True)
class User:
    id: str
    tenant_id: str
    roles: tuple


def _load_users():
    data = json.loads(Path("data/users.json").read_text(encoding="utf-8"))
    return {u["user_id"]: u for u in data}


def get_user(user_id):
    u = _load_users().get(user_id)
    if not u:
        return None
    return User(u["user_id"], u["tenant_id"], tuple(u["roles"]))


def authenticate(user_id, password):
    """Demo login: one shared demo password. Real systems store hashed passwords per user."""
    user = get_user(user_id)
    if user and hmac.compare_digest(password.encode(), config.DEMO_PASSWORD.encode()):
        return user
    return None


def create_token(user):
    payload = {
        "sub": user.id,
        "tenant_id": user.tenant_id,
        "roles": list(user.roles),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token):
    """Raises an exception if the token is forged, tampered with or expired."""
    p = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    return User(p["sub"], p["tenant_id"], tuple(p["roles"]))
