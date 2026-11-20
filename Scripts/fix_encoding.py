from pathlib import Path

for p in Path("data/docs").rglob("*.md"):
    raw = p.read_bytes()
    try:
        raw.decode("utf-8")      # already fine, skip
        continue
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
        p.write_text(text, encoding="utf-8")
        print("converted", p)