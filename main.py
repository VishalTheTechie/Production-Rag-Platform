import uuid

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import audit
import auth
from docs_admin import get_document_tenant, set_document_acl
from rag import secure_answer

app = FastAPI(title="RAG Platform")
bearer = HTTPBearer()


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    """Identity comes ONLY from the verified token."""
    try:
        return auth.decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(user=Depends(current_user)):
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admins only")
    return user


class LoginRequest(BaseModel):
    user_id: str
    password: str


class AskRequest(BaseModel):
    # Only "question" is read. Any tenant_id / roles sent in the body are ignored.
    question: str


class AclUpdate(BaseModel):
    allowed_roles: list[str]
    allowed_users: list[str] = []


@app.post("/login")
def login(req: LoginRequest):
    user = auth.authenticate(req.user_id, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Wrong user or password")
    return {"access_token": auth.create_token(user), "token_type": "bearer"}


@app.post("/ask")
def ask(req: AskRequest, user=Depends(current_user)):
    request_id = str(uuid.uuid4())
    result = secure_answer(user, req.question, request_id)
    return {
        "request_id": request_id,
        "answer": result["answer"],
        "sources": [
            {"chunk_id": s["chunk_id"], "doc_id": s["doc_id"], "score": round(s["score"], 3)}
            for s in result["sources"]
        ],
    }


@app.get("/admin/audit/document/{doc_id}")
def who_retrieved(doc_id: str, days: int = Query(30, ge=1, le=365), admin=Depends(require_admin)):
    if get_document_tenant(doc_id) != admin.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"doc_id": doc_id, "days": days, "retrievals": audit.who_retrieved(doc_id, admin.tenant_id, days)}


@app.put("/admin/documents/{doc_id}/acl")
def change_acl(doc_id: str, body: AclUpdate, admin=Depends(require_admin)):
    if get_document_tenant(doc_id) != admin.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")
    set_document_acl(doc_id, body.allowed_roles, body.allowed_users)
    audit.log_acl_change(str(uuid.uuid4()), admin, doc_id, body.allowed_roles, body.allowed_users)
    return {"doc_id": doc_id, "allowed_roles": body.allowed_roles, "allowed_users": body.allowed_users}
