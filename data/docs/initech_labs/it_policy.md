# INITECH LABS INC. – INTERNAL INFORMATION SECURITY POLICY
**Document Identifier:** POL-SEC-2024-v3  
**Effective Date:** October 12, 2024  
**Next Review Date:** April 12, 2025  
**Approved By:** Dr. Marcus Vance, Chief Information Security Officer (CISO)  

---

### 1. Password & Authentication Standards
All employees, contractors, and research fellows at Initech Labs must adhere to strict access control guidelines to protect proprietary genomic sequencing data and operational assets.

* **Length & Complexity:** Passwords for standard corporate accounts must be a minimum of 16 characters. Passwords for privileged admin accounts and R&D database environments must be at least 20 characters. Passwords must contain at least one uppercase letter, one lowercase letter, one number, and one special character (`!@#$%^&*`).
* **Rotation & History:** Corporate passwords must be changed every 90 days. R&D lab network accounts must be rotated every 60 days. System history will prevent the reuse of the last 12 passwords.
* **Multi-Factor Authentication (MFA):** MFA is mandatory across all systems via Duo Security push notifications. SMS-based MFA is strictly prohibited.
* **Password Managers:** Password storage is restricted exclusively to the corporate **1Password Enterprise Vault**. Saving passwords in web browsers or physical notebooks is a policy violation.

---

### 2. Virtual Private Network (VPN) Protocols
Remote access to Initech Labs' internal subnets, proprietary databases, and lab automation servers requires an active VPN connection.

* **Gateway & Software:** Staff must use the **Cisco Secure Client (v5.1.2 or higher)** connected to the primary corporate gateway at `vpn-primary.initechlabs-net.com:4433`.
* **Usage Mandate:** VPN must be enabled at all times when working outside the secure physical perimeter of the Cambridge headquarters (Building B, 400 Technology Square).
* **Restrictions:** Split-tunneling is strictly disabled. VPN sessions automatically terminate after 30 minutes of inactivity or a maximum continuous session length of 12 hours.

---

### 3. Device & Physical Security Rules
To safeguard intellectual property, all endpoints accessing the Initech network must comply with Mobile Device Management (MDM) enrollment via Workspace ONE.

* **Approved Hardware:** Only company-issued hardware may be used to access raw genomic files or customer samples. Personal devices (BYOD) are restricted to corporate email and Slack, provided Workspace ONE is installed.
* **Encryption:** Full-Disk Encryption (BitLocker with XTS-AES 256-bit on Windows 11 Enterprise; FileVault on macOS Sonoma 14.5+) is mandatory.
* **Screen Lock & Idle Timeout:** Screens must automatically lock after 5 minutes of inactivity. Manual locking (`Win+L` or `Ctrl+Cmd+Q`) is required whenever leaving a workstation unattended.
* **Peripheral Access:** USB storage drives are hardware-blocked by default. USB override exceptions must be granted in writing by Lead Security Engineer **Elena Rostova**.

---

### 4. Incident Reporting & Escalation
Prompt reporting of security events is critical to protecting patient data and biotech patents.

* **Definition of Incident:** Incidents include lost/stolen hardware, suspected phishing attempts, unexpected MFA push requests, or unauthorized attempts to access BSL-2 lab network segments.
* **Reporting SLA:** Security incidents must be reported within **15 minutes** of discovery.
* **Reporting Channels:**
  * **Email:** Send details to `soc-incident@initechlabs.com` with the subject header `[INCIDENT-URGENT]`.
  * **Hotline:** Call the 24/7 IT SOC Dispatch line at **+1 (555) 014-9982**.
* **Incident Commander:** Escalations are handled directly by Lead IT Administrator **Sarah Jenkins** (`sjenkins@initechlabs.com`). Failure to report an incident within 1 hour of discovery may result in immediate access revocation under Disciplinary Code 4.2-B.