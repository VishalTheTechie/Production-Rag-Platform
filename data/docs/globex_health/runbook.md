# Globex Health IT Operations Runbook: Incident Escalation & On-Call Protocols

**Document ID:** RUN-OPS-2024-V4.2  
**Effective Date:** November 15, 2024  
**Next Review Date:** May 15, 2025  
**Owner:** Enterprise Site Reliability Engineering (SRE) & Clinical Informatics  

---

## 1. Core Systems Classification & Recovery Time Objectives (RTO)

*   **PulseEHR (Tier 1 - Critical):** Core Electronic Health Record system. Maximum acceptable downtime: **15 minutes**. Max database latency: **250ms**.
*   **PharmNet-Rx (Tier 1 - Critical):** Automated pharmacy dispensing and medication administration system. Maximum acceptable downtime: **15 minutes**.
*   **AegisPACS (Tier 1 - Critical):** Medical imaging, radiology, and PACS network. Maximum acceptable downtime: **30 minutes**.
*   **OmniTrack (Tier 2 - High):** Bed management and patient flow logistics system. Maximum acceptable downtime: **2 hours**.
*   **GlobexConnect (Tier 2 - High):** Internal VoIP, nursing badge communication, and staff paging infrastructure. Maximum acceptable downtime: **1 hour**.

---

## 2. On-Call Shift Architecture & Scheduling Rules

*   **Rotation Schedule:** On-call shifts rotate weekly on **Tuesdays at 08:00 EST**. Shift handovers must occur synchronously via Microsoft Teams Channel `IT-Ops-Handover`.
*   **Maximum On-Duty Duration:** No engineer may serve as Primary On-Call for more than **6 consecutive days (144 hours)** without a mandatory 48-hour off-duty period.
*   **Shift Swap Policy:** Shift swaps must be submitted via Jira Service Management using Form `OPS-SWAP` at least **24 hours prior** to the shift start. All swaps require explicit sign-off from Infrastructure Lead **Marcus Vance**.
*   **Hardware Requirements:** Primary engineers must carry a Globex-issued iPhone 14 with the PagerDuty app configured to override iOS Focus/Silent modes.

---

## 3. Incident Severity Levels & SLAs

*   **P1 (Critical):** Complete outage of a Tier 1 system or active threat to patient safety.  
    *   *Acknowledgement SLA:* **3 minutes**  
    *   *Bridge Activation SLA:* **5 minutes**  
*   **P2 (High):** Degradation of a Tier 1 system or total outage of a Tier 2 system.  
    *   *Acknowledgement SLA:* **15 minutes**  
    *   *Target Resolution:* **2 hours**  
*   **P3 (Moderate):** Non-clinical system degradation or minor administrative impact.  
    *   *Acknowledgement SLA:* **60 minutes** (during business hours: 07:00–19:00 EST)  
*   **P4 (Low):** Minor bug or informational alert with zero immediate operational impact.  
    *   *Acknowledgement SLA:* **24 hours**  

---

## 4. On-Call Escalation Matrix

If the Primary Engineer does not acknowledge an alert within the specified SLA, PagerDuty automatically triggers the following escalation chain:

| Tier / Elapsed Time | Role | Assigned Personnel | Direct Phone / Contact |
| :--- | :--- | :--- | :--- |
| **Level 1 (0 min)** | Primary SRE On-Call | Dynamic Rotation | PagerDuty Push / SMS |
| **Level 2 (+5 min)** | Secondary SRE Lead | **Elena Rostova** | +1 (555) 019-8234 |
| **Level 3 (+15 min)** | Infrastructure Manager | **Marcus Vance** | +1 (555) 014-9921 |
| **Level 4 (+30 min)** | VP of IT Infrastructure | **Dr. Sarah Lin** | +1 (555) 017-3340 |
| **Level 5 (+45 min)** | Chief Information Officer | **David K. Miller** | +1 (555) 012-7788 |

---

## 5. Major Incident Protocol (P1 Outages)

1.  **Bridge Activation:** Open the persistent Emergency Command Zoom Room (**Meeting ID:** `882-901-4431`, **Passcode:** `9110`).
2.  **Communication Channel:** Establish live updates in Slack channel `#incident-emergency-live`.
3.  **Incident Commander (IC):** The Primary On-Call Engineer assumes the IC role until formally relieved by Elena Rostova or Marcus Vance.
4.  **Clinical Operations Liaison:** Instantly page Lead Clinical Informaticist **Dr. Aris Thorne** via internal extension **x4402** or mobile code "BLUE-IT".
5.  **PHI Security Compliance:** Engineers are strictly prohibited from posting unencrypted Patient Health Information (PHI) or raw SQL dumps into Slack or Jira. Incident logs containing PHI must be archived exclusively in SecureVault under Key ID `GLB-PHI-SEC-99`.

---

## 6. Post-Incident Requirements

A formal Post-Mortem Report (PMR) must be created using Jira template `PMR-TEMP-V2` within **48 hours** of closing any P1 or P2 incident. Review meetings take place bi-weekly on **Thursdays at 14:00 EST**.