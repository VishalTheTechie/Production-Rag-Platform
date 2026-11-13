# ACME CORP ENGINEERING RUNBOOK: ON-CALL & INCIDENT ESCALATION PROCEDURES
**Document ID:** RUN-OPS-2024-V4.2  
**Effective Date:** November 12, 2024  
**Owner:** Infrastructure & Site Reliability Engineering (SRE) Team  

### 1. On-Call Shift Management
* **Handover Schedule:** The weekly rotation hands over every Tuesday at 10:00 AM EST.
* **Handover Protocol:** Outgoing and incoming engineers must complete a 15-minute sync on Slack channel `#sre-handoff`. Outstanding non-critical operational issues must be logged as Jira tickets tagged `tech-debt-ops`.
* **Roles:** 
  * **Primary On-Call:** Dedicated exclusively to incoming alerts, system triage, and active incident mitigation.
  * **Secondary On-Call:** Supports Primary during SEV-1/SEV-2 events and manages internal developer support requests via `#dev-support`.

### 2. Incident Severity Matrix & Response Timelines

| Severity | Definition / Thresholds | Acknowledgment SLA | Target Mitigation SLA | Automated Escalation Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1** | Core service outage. Examples: `TaskEngine-Prod` unreachable, or global HTTP 5xx error rate >4% on `Kong-Gateway-US`. | 5 Minutes | 45 Minutes | Unacknowledged after 5 mins or unmitigated after 30 mins |
| **SEV-2** | Key feature degraded. Examples: Gantt rendering component `Canvas-Render-V2` failing, or DB CPU >85% on `db01-a` for >10 mins. | 15 Minutes | 2 Hours | Unacknowledged after 15 mins or unmitigated after 90 mins |
| **SEV-3** | Minor impact, internal tool failure, or non-critical latency. Example: `AuthZero-Proxy` latency >300ms or billing export batch delays. | 60 Minutes | 24 Hours | Unacknowledged after 60 mins |

### 3. Escalation Hierarchy & Contact Registry

If an alert is unacknowledged within the designated SLA window, PagerDuty automatically escalates through the hierarchy below:

* **Level 1 (Primary On-Call):** Rotating Engineer (PagerDuty schedule: `Schedule-SRE-Prod-L1`). Current On-Call Lead: **Marcus Vance** (+1-555-014-8832).
* **Level 2 (Secondary On-Call / SRE Lead):** **Devraj Patel** (+1-555-019-4411). PagerDuty target: `Schedule-SRE-Prod-L2`.
* **Level 3 (Engineering Director):** **Sarah Chen** (+1-555-017-3390). Contacted automatically if SEV-1 exceeds 30 minutes without resolution.
* **Level 4 (Executive / VP of Engineering):** **Elena Rostova** (+1-555-012-9900). Escalated manually by L3 for major outages (>60 mins SEV-1) impacting enterprise SLAs.
* **Customer Communications Lead:** **Brian Miller** (+1-555-018-2254). Notified immediately upon SEV-1 confirmation to handle customer communications.

### 4. Standard Triage Protocol

1. **Acknowledge Notification:** Acknowledge the PagerDuty page or reply `ACK` in Slack channel `#incident-alerts`.
2. **Establish Incident Command:**
   * Generate an incident Slack channel: `#incident-YYYYMMDD-[system]`.
   * For SEV-1 and SEV-2 incidents, open the designated Zoom bridge: `https://acme.zoom.us/j/9988776655`.
3. **Execute System Diagnostics:**
   * **API Issues:** Check Datadog dashboard `Kong-Gateway-Health`. If error rates exceed 4%, execute rollback: `/scripts/deploy_rollback.sh --service=kong-east`.
   * **Database Failures:** Inspect `PostgreSQL-Cluster-DB01`. If primary node `db01-a` is unresponsive, initiate manual failover to replica: `pg_failover_trigger --cluster=db01 --promote-replica=db01-b`.
   * **Authentication Issues:** Inspect `AuthZero-Proxy` container logs via AWS CloudWatch log group `/aws/ecs/authzero-proxy`.
4. **External Status Communication:** Brian Miller (or delegate) must update `status.acmeworkspace.io` within 15 minutes of SEV-1 declaration, with mandatory follow-up updates every 30 minutes until mitigation.