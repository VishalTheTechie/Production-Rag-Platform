"""Access-control helpers. Used twice: as a Qdrant pre-filter, and as a code re-check."""
from qdrant_client import models


def build_filter(user):
    """Pre-filter: Qdrant only ever searches chunks this user may see.
    Rule: same tenant AND (one of my roles is allowed OR I am named personally)."""
    return models.Filter(
        must=[
            models.FieldCondition(
                key="tenant_id", match=models.MatchValue(value=user.tenant_id)
            ),
            models.Filter(
                should=[
                    models.FieldCondition(
                        key="allowed_roles",
                        match=models.MatchAny(any=list(user.roles)),
                    ),
                    models.FieldCondition(
                        key="allowed_users", match=models.MatchValue(value=user.id)
                    ),
                ]
            ),
        ]
    )


def chunk_allowed(user, chunk) -> bool:
    """Second check in plain Python. Fails closed: missing fields mean NOT allowed."""
    if chunk.get("tenant_id") != user.tenant_id:
        return False
    roles_ok = bool(set(chunk.get("allowed_roles") or []) & set(user.roles))
    user_ok = user.id in (chunk.get("allowed_users") or [])
    return roles_ok or user_ok


def enforce_acl(user, chunks):
    """Returns (allowed_chunks, blocked_chunks)."""
    allowed, blocked = [], []
    for c in chunks:
        (allowed if chunk_allowed(user, c) else blocked).append(c)
    return allowed, blocked
