"""Prints the numbers for your resume line:
   N adversarial checks, leaks found, and filtering overhead in ms."""
import statistics
import sys
import time

sys.path.insert(0, "tests")
import auth
import config
import rag
from acl import build_filter
from adversarial import QUERIES, allowed_doc_ids, load_users
from embeddings import embed_one


def main():
    users = load_users()
    checks, leaks = 0, 0
    for u in users:
        user = auth.get_user(u["user_id"])
        permitted = allowed_doc_ids(u)
        for q in QUERIES:
            chunks = rag.retrieve(q, build_filter(user), k=10)
            checks += 1
            if {c["doc_id"] for c in chunks} - permitted:
                leaks += 1
                print("LEAK:", u["user_id"], "|", q)

    # Filtering overhead: time only the Qdrant search (embedding done once per query)
    admin = auth.get_user("acme_corp_admin")
    flt = build_filter(admin)
    plain, filtered = [], []
    for q in QUERIES:
        vec = embed_one(q)
        for _ in range(5):
            t = time.perf_counter()
            rag.client.query_points(collection_name=config.COLLECTION, query=vec, limit=5)
            plain.append((time.perf_counter() - t) * 1000)
            t = time.perf_counter()
            rag.client.query_points(collection_name=config.COLLECTION, query=vec, query_filter=flt, limit=5)
            filtered.append((time.perf_counter() - t) * 1000)

    overhead = statistics.median(filtered) - statistics.median(plain)
    report = (
        f"Users x adversarial queries checked: {checks}\n"
        f"Cross-tenant / forbidden leaks: {leaks}\n"
        f"Median search without filter: {statistics.median(plain):.1f} ms\n"
        f"Median search with ACL filter: {statistics.median(filtered):.1f} ms\n"
        f"Filtering overhead (median): {overhead:.1f} ms\n"
    )
    print("\n" + report)
    open("eval/leakage_report.txt", "w", encoding="utf-8").write(report)


if __name__ == "__main__":
    main()
