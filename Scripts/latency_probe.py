import time
import auth, pipeline

user = auth.get_user("acme_corp_admin")
for i in range(4):
    r = pipeline.answer(user, f"How many holidays does Acme Corp recognize? (test {i})",
                        f"probe{i}", mode="baseline", run_label="probe")
    print(i + 1, round(r["latency_ms"] / 1000, 1), "s")
    time.sleep(20)