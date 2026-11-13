"""Admin operations on documents: look up a document's tenant, change its ACL."""
from qdrant_client import QdrantClient, models

import config

client = QdrantClient(url=config.QDRANT_URL)


def _doc_filter(doc_id):
    return models.Filter(
        must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
    )


def get_document_tenant(doc_id):
    points, _ = client.scroll(
        collection_name=config.COLLECTION,
        scroll_filter=_doc_filter(doc_id),
        limit=1,
        with_payload=True,
    )
    return points[0].payload["tenant_id"] if points else None


def set_document_acl(doc_id, allowed_roles, allowed_users):
    """Updates EVERY chunk of the document. Takes effect on the very next query."""
    client.set_payload(
        collection_name=config.COLLECTION,
        payload={"allowed_roles": allowed_roles, "allowed_users": allowed_users},
        points=_doc_filter(doc_id),
        wait=True,
    )
