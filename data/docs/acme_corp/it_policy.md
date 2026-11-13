# Acme Corp Information Security Policy (POL-SEC-2024-V3)

**Effective Date:** October 15, 2024  
**Next Review Date:** November 1, 2025  
**Policy Owner:** Marcus Vance, Chief Information Security Officer (CISO)  
**Scope:** Applies to all full-time employees, contractors, and third-party vendors accessing Acme Corp networks, hardware, or production environments for our flagship SaaS platform, TaskPulse.

---

### 1. Password & Authentication Standards
To protect internal databases and TaskPulse user data, all staff must adhere to the following identity controls:

*   **Password Length & Complexity:** Passwords must be a minimum of **14 characters** long and contain at least one uppercase letter, one lowercase letter, one number, and one special character (`!@#$%^&*`).
*   **Rotation Schedule:** Standard user passwords expire every **90 days**. System administrator and root-level accounts must change passwords every **45 days**.
*   **Password History:** The system will prevent the re-use of an individual’s last **10 passwords**.
*   **Password Managers:** Employees are required to use the corporate **1Password** enterprise vault. Storing passwords in internet browsers or unencrypted local files is strictly forbidden.
*   **Multi-Factor Authentication (MFA):** MFA is mandatory across all systems via the **Duo Security** application. Authentication via SMS or voice calls is prohibited due to SIM-swapping risks.
*   **Account Lockout:** Accounts will automatically lock out for **30 minutes** after **5 consecutive failed login attempts**.

---

### 2. VPN & Network Security
Remote connection to Acme Corp networks requires compliance with secure access protocols:

*   **Mandatory VPN:** Employees working outside the primary Austin headquarters must connect via the **Acme Global Protect VPN** (`vpn.acmecorp.com`) before accessing internal software development repositories, Jira, or financial tools.
*   **Session Limits:** Active VPN sessions will automatically disconnect after **30 minutes of inactivity**. A hard cap forces a full re-authentication every **12 hours**, regardless of activity.
*   **Network Behavior:** Split-tunneling is permanently disabled on company laptops. All internet traffic must route through Acme’s secure DNS filtering system while connected to the VPN.

---

### 3. Workstation & Device Rules
All equipment issued by Acme Corp is managed by IT Operations under the supervision of Director David Ross.

*   **Device Encryption:** Full-disk encryption (BitLocker 256-bit for Windows; FileVault for macOS) must remain active on all corporate laptops at all times. Recovery keys are managed centrally via Microsoft Intune and Jamf Pro.
*   **Screen Lockouts:** Laptops must automatically lock after **5 minutes of inactivity**. Employees must manually lock screens (`Win+L` or `Ctrl+Cmd+Q`) whenever stepping away from their desks.
*   **BYOD (Bring Your Own Device):** Personal mobile devices may only access corporate email (Gmail) and Slack. Devices must run **AirWatch MDM**, maintain an updated OS, and enforce a 6-digit PIN. Jailbroken or rooted personal devices are blocked from network access.
*   **Physical Protection:** Laptops left unattended in vehicles must be locked inside the trunk. Hardware must never be checked as baggage on commercial airlines.

---

### 4. Incident Reporting Protocols
Prompt reporting is essential to mitigating data breaches, ransomware attacks, or compromise of TaskPulse source code.

*   **Reporting SLA:** Any security anomaly, stolen laptop, suspicious email link click, or unverified password prompt must be reported within **15 minutes** of discovery.
*   **Reporting Channels:**
    *   **Internal Emergency Phone:** Extension **4357** (HELP) or direct line **512-555-0199**.
    *   **Email:** Submit an urgent ticket to `security-incident@acmecorp.com`.
    *   **Slack Channel:** `#sec-ops-urgent` (monitored 24/7).
*   **Incident Response Lead:** Reports are routed directly to **Sarah Jenkins**, Lead Incident Response Analyst.
*   **Non-Compliance:** Failure to report a known security incident within **2 hours** may result in disciplinary action up to immediate termination.