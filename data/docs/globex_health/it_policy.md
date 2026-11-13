# Globex Health Internal Cybersecurity Policy (POL-SEC-2024-V3)

**Effective Date:** November 1, 2024  
**Last Reviewed:** October 15, 2024  
**Policy Owner:** Dr. Aris Thorne, Chief Information Security Officer (CISO)  
**Applies To:** All 8,400 employees, contractors, and medical staff across all 5 Globex Health regional hospital facilities.

---

### 1. Purpose & Scope
This policy mandates technical and procedural safeguards to protect Electronic Protected Health Information (ePHI), clinical networks, and corporate infrastructure across all Globex Health entities (including St. Jude Memorial and Oak Valley Hospital). Compliance is mandatory for all personnel accessing the network.

---

### 2. Password & Access Control Policy
* **Length & Complexity:** All primary network passwords must be a minimum of **16 characters** in length and contain at least three of the following four character types: uppercase letters, lowercase letters, numbers, and special symbols (`!@#$%^&*`).
* **Expiration Schedules:** 
  * Standard corporate account passwords expire every **90 days**.
  * Electronic Health Record (EHR/Epic) and privileged system accounts expire every **45 days**.
  * Password history prevents the reuse of the previous **12 passwords**.
* **Account Lockout:** Accounts are locked for **30 minutes** after **5 consecutive failed login attempts**.
* **Multi-Factor Authentication (MFA):** Mandatory for all system access using **Duo Security** (push notification or physical hardware token). Delivery of MFA codes via SMS or voice call is strictly prohibited.

---

### 3. Remote Access & Virtual Private Network (VPN) Rules
* **Approved Client:** Remote access is strictly restricted to the Globex VPN portal (`vpn.globexhealth.org`) via the official **Cisco AnyConnect** client. Split-tunneling is strictly disabled.
* **Session Limits:** VPN sessions will automatically terminate after **15 minutes of inactivity**. Maximum continuous session length is capped at **12 hours**, after which re-authentication is required.
* **Geographic Access Restrictions:** VPN access is restricted to the United States and Canada. Employees traveling internationally must submit **Form SEC-88** at least **14 business days prior** to departure. Approval must be granted by Deputy CISO Marcus Vance.

---

### 4. Workstation & Device Security Rules
* **Corporate Laptops:** All issued laptops must run Windows 11 Enterprise with **BitLocker AES-256 bit encryption**. Mass USB storage ports are disabled by default; exemptions require an approved **Form DEV-12** signed by the facility IT Director.
* **Physical Security:** Laptops left unattended in non-clinical administrative areas must be secured using a Kensington cable lock.
* **Screen Lock Timers:** 
  * Clinical workstation screens auto-lock after **3 minutes** of inactivity.
  * Non-clinical administrative screens auto-lock after **5 minutes** of inactivity.
* **Mobile Devices (BYOD):** Personal devices accessing corporate email must enroll in MobileIron MDM. Eligible operating systems are limited to **iOS 16.0+** or **Android 13.0+**. Jailbroken or rooted devices are blocked automatically.

---

### 5. Incident Reporting Protocol
Any suspected security breach, phishing event, loss of equipment, or unauthorized exposure of ePHI must be reported immediately according to incident severity:

* **Reporting Timelines:**
  * **Tier 3 (Critical / ePHI Leak):** Must be reported within **15 minutes** of discovery.
  * **Tier 1 & 2 (Standard Security Incidents):** Must be reported within **60 minutes** of discovery.
* **Contact Channels:**
  * **Internal Extension:** Ext. 4400
  * **External Phone:** (555) 019-4400
  * **Email:** `soc@globexhealth.org`
  * **Portal:** `incident.globexhealth.org`
* **Incident Management:** All Tier 3 breach protocols are overseen by Incident Response Commander **Sarah Jenkins**, VP of IT Risk Management.

*Violations of POL-SEC-2024-V3 may result in disciplinary action up to immediate termination of employment and revocation of clinical network privileges.*