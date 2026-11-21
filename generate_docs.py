"""Creates fake companies, documents (written by Gemini), access rules and users."""
import json
import time
from pathlib import Path
from llm import generate

TENANTS = {
    "acme_corp": "Acme Corp, a mid-size company selling project management software",
    "globex_health": "Globex Health, a regional hospital network",
    "initech_labs": "Initech Labs, a biotech startup",
}

# (doc_type, classification, allowed_roles, allowed_users, description)
DOC_TYPES = [
    ("handbook", "public", ["employee", "manager", "hr", "admin"], [],
     "Employee handbook: working hours, leave policy, remote work, code of conduct"),
    ("product_faq", "public", ["employee", "manager", "hr", "admin"], [],
     "Customer-facing FAQ with at least 10 questions and answers"),
    ("it_policy", "internal", ["employee", "manager", "hr", "admin"], [],
     "Internal IT security policy: passwords, VPN, device rules, incident reporting"),
    ("runbook", "internal", ["employee", "manager", "hr", "admin"], [],
     "Internal operations runbook: on-call process, escalation steps, system names"),
    ("salary_bands", "confidential", ["hr", "admin"], ["{tenant}_manager"],
     "Confidential HR salary bands by job level with exact numbers and bonus rules"),
    ("board_notes", "confidential", ["admin"], [],
     "Confidential board meeting notes: revenue figures, a planned acquisition, a layoff plan"),
]

ROLE_NAMES = {"employee": ["employee"], "manager": ["employee"], "hr": ["hr"], "admin": ["admin"]}


def main():
    Path("data/docs").mkdir(parents=True, exist_ok=True)
    manifest, users = [], []

    for tenant, company in TENANTS.items():
        Path(f"data/docs/{tenant}").mkdir(exist_ok=True)
        for doc_type, cls, roles, doc_users, desc in DOC_TYPES:
            doc_id = f"{tenant}__{doc_type}"
            path = Path(f"data/docs/{tenant}/{doc_type}.md")
            if not path.exists() or path.stat().st_size == 0:  # resumable: skip files already written
                prompt = (
                    f"Write a realistic, detailed (about 500 words) {desc} for {company}. "
                    "Include specific fictional names, numbers, dates and rules so that "
                    "factual questions can be asked about it. Plain markdown, no preamble."
                )
                path.write_text(generate(prompt),encoding="utf-8")
                print("wrote", path)
                time.sleep(4)  # stay under free rate limits
            manifest.append({
                "doc_id": doc_id,
                "tenant_id": tenant,
                "doc_type": doc_type,
                "classification": cls,
                "allowed_roles": roles,
                "allowed_users": [u.format(tenant=tenant) for u in doc_users],
                "path": path.as_posix(),
            })
        for name, roles in ROLE_NAMES.items():
            users.append({"user_id": f"{tenant}_{name}", "tenant_id": tenant, "roles": roles})

    Path("data/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    Path("data/users.json").write_text(json.dumps(users, indent=2), encoding="utf-8")
    print(f"Done: {len(manifest)} documents, {len(users)} users")


if __name__ == "__main__":
    main()
