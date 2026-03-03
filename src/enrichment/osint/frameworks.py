"""Built-in reference data for compliance frameworks and threat intelligence.

Contains pre-loaded reference data for:
- NIST SP 800-53 (most common controls)
- ISO 27001 (top controls)
- CIS Controls v8 (critical controls)
- MITRE ATT&CK (common techniques)

These datasets enable offline OSINT lookups without requiring external API calls.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# NIST SP 800-53 Revision 5 — Top 20 Most Common Controls
# ---------------------------------------------------------------------------

NIST_800_53_CONTROLS = {
    "AC-1": {
        "family": "Access Control",
        "title": "Policy and Procedures",
        "description": "Develop and document organization-wide access control policies and procedures, review/update periodically.",
        "control_type": "Management",
    },
    "AC-2": {
        "family": "Access Control",
        "title": "Account Management",
        "description": "Establish and maintain system accounts, including privileged accounts; manage account access based on need-to-know.",
        "control_type": "Administrative",
    },
    "AC-3": {
        "family": "Access Control",
        "title": "Access Enforcement",
        "description": "Enforce approved authorizations for logical and physical access using access control mechanisms.",
        "control_type": "Technical",
    },
    "AC-5": {
        "family": "Access Control",
        "title": "Separation of Duties",
        "description": "Enforce separation of duties through access controls and automated enforcement mechanisms.",
        "control_type": "Technical",
    },
    "AC-6": {
        "family": "Access Control",
        "title": "Least Privilege",
        "description": "Limit user access and privileges to only those required to accomplish assigned functions.",
        "control_type": "Technical",
    },
    "AU-1": {
        "family": "Audit and Accountability",
        "title": "Policy and Procedures",
        "description": "Develop and document audit and accountability policies and procedures.",
        "control_type": "Management",
    },
    "AU-2": {
        "family": "Audit and Accountability",
        "title": "Audit Events",
        "description": "Determine system events to be audited; define triggering mechanisms for audit logging.",
        "control_type": "Technical",
    },
    "AU-3": {
        "family": "Audit and Accountability",
        "title": "Content of Audit Records",
        "description": "Ensure audit records contain sufficient information to determine what occurred and who was responsible.",
        "control_type": "Technical",
    },
    "AU-6": {
        "family": "Audit and Accountability",
        "title": "Audit Review, Analysis, and Reporting",
        "description": "Review, analyze, and report audit findings on a regular basis.",
        "control_type": "Technical",
    },
    "CM-1": {
        "family": "Configuration Management",
        "title": "Policy and Procedures",
        "description": "Develop and document configuration management policies and procedures.",
        "control_type": "Management",
    },
    "CM-3": {
        "family": "Configuration Management",
        "title": "Change Control",
        "description": "Establish and document a change control process; ensure testing before implementation.",
        "control_type": "Technical",
    },
    "CM-5": {
        "family": "Configuration Management",
        "title": "Access Restrictions for Change",
        "description": "Restrict physical and logical access to information system components when making changes.",
        "control_type": "Technical",
    },
    "IA-1": {
        "family": "Identification and Authentication",
        "title": "Policy and Procedures",
        "description": "Develop and document identification and authentication policies and procedures.",
        "control_type": "Management",
    },
    "IA-2": {
        "family": "Identification and Authentication",
        "title": "Authentication",
        "description": "Authenticate users and devices; use multi-factor authentication for privileged accounts.",
        "control_type": "Technical",
    },
    "IA-4": {
        "family": "Identification and Authentication",
        "title": "Identifier Management",
        "description": "Manage system identifiers; use unique identifiers for users and resources.",
        "control_type": "Technical",
    },
    "SC-1": {
        "family": "System and Communications Protection",
        "title": "Policy and Procedures",
        "description": "Develop and document system and communications protection policies.",
        "control_type": "Management",
    },
    "SC-7": {
        "family": "System and Communications Protection",
        "title": "Boundary Protection",
        "description": "Monitor and control communications at system boundaries; implement perimeter defense.",
        "control_type": "Technical",
    },
    "SC-12": {
        "family": "System and Communications Protection",
        "title": "Cryptographic Key Establishment and Management",
        "description": "Establish and manage cryptographic keys; secure storage and lifecycle management.",
        "control_type": "Technical",
    },
    "SI-1": {
        "family": "System and Information Integrity",
        "title": "Policy and Procedures",
        "description": "Develop and document system and information integrity policies.",
        "control_type": "Management",
    },
    "SI-4": {
        "family": "System and Information Integrity",
        "title": "Information System Monitoring",
        "description": "Monitor systems for unauthorized access; log and analyze anomalies.",
        "control_type": "Technical",
    },
}

# ---------------------------------------------------------------------------
# ISO/IEC 27001:2022 — Top 15 Controls
# ---------------------------------------------------------------------------

ISO_27001_CONTROLS = {
    "A.5.1": {
        "domain": "Information Security Policies",
        "title": "Policies for Information Security",
        "description": "Information security policies are established, documented, approved, published and communicated to all relevant personnel.",
    },
    "A.6.1": {
        "domain": "Organization of Information Security",
        "title": "Internal Organization",
        "description": "Management commitment to information security is established and implemented across the organization.",
    },
    "A.7.1": {
        "domain": "Human Resource Security",
        "title": "Screening",
        "description": "Background checks and verification are performed before employment to reduce risks.",
    },
    "A.8.3": {
        "domain": "Asset Management",
        "title": "Acceptable Use of Assets",
        "description": "Rules for acceptable use of information and assets are established and communicated.",
    },
    "A.9.1": {
        "domain": "Access Control",
        "title": "Access Control Policy",
        "description": "Access control policies and rules are established, documented and reviewed regularly.",
    },
    "A.9.2": {
        "domain": "Access Control",
        "title": "User Access Management",
        "description": "User access is granted based on business requirements; access is regularly reviewed and revoked.",
    },
    "A.9.4": {
        "domain": "Access Control",
        "title": "Management of Secret Authentication Information",
        "description": "Password and cryptographic key management controls are implemented.",
    },
    "A.10.1": {
        "domain": "Cryptography",
        "title": "Cryptographic Controls",
        "description": "Encryption and cryptographic controls are used to protect confidentiality and integrity.",
    },
    "A.12.1": {
        "domain": "Operations Security",
        "title": "Operational Procedures",
        "description": "Documented procedures for system operations and maintenance are established.",
    },
    "A.12.6": {
        "domain": "Operations Security",
        "title": "Management of Technical Vulnerabilities",
        "description": "Information on technical vulnerabilities is obtained; systems are patched promptly.",
    },
    "A.13.1": {
        "domain": "Communications Security",
        "title": "Network Security",
        "description": "Networks are managed to prevent unauthorized access and isolation of services.",
    },
    "A.14.1": {
        "domain": "System Acquisition, Development and Maintenance",
        "title": "Information Security Requirements Analysis and Specification",
        "description": "Security requirements are defined for new systems and changes.",
    },
    "A.14.2": {
        "domain": "System Acquisition, Development and Maintenance",
        "title": "Security of Development, Test and Acceptance Environments",
        "description": "Development, testing and acceptance environments are secured separately from production.",
    },
    "A.16.1": {
        "domain": "Information Security Incident Management",
        "title": "Management of Information Security Incidents and Improvements",
        "description": "Incident response procedures are established; incidents are reported and analyzed.",
    },
    "A.18.1": {
        "domain": "Compliance",
        "title": "Compliance with Legal and Regulatory Requirements",
        "description": "Compliance with applicable laws and regulations is monitored and ensured.",
    },
}

# ---------------------------------------------------------------------------
# CIS Controls v8 — Top 10 Critical Controls
# ---------------------------------------------------------------------------

CIS_CONTROLS_V8 = {
    "1.1": {
        "group": "Inventory and Control of Enterprise Assets",
        "title": "Establish and Maintain Detailed Asset Inventory",
        "description": "Maintain an accurate, current, and complete inventory of all hardware assets connected to the network.",
        "criticality": "Foundational",
    },
    "2.1": {
        "group": "Inventory and Control of Software Assets",
        "title": "Establish and Maintain a Software Inventory",
        "description": "Establish and maintain an accurate, current, and complete inventory of all software connected to enterprise assets.",
        "criticality": "Foundational",
    },
    "3.1": {
        "group": "Data Protection",
        "title": "Establish and Maintain a Data Security and Privacy Policy",
        "description": "Establish and maintain a data security and privacy policy for the organization.",
        "criticality": "Foundational",
    },
    "4.1": {
        "group": "Secure Configuration Management",
        "title": "Establish and Maintain a Secure Configuration Management Process",
        "description": "Establish and maintain a secure configuration management process for enterprise assets.",
        "criticality": "Foundational",
    },
    "5.1": {
        "group": "Account Management",
        "title": "Establish and Maintain an Inventory of Accounts",
        "description": "Establish and maintain an inventory of accounts managed by the organization.",
        "criticality": "Foundational",
    },
    "6.1": {
        "group": "Access Control Management",
        "title": "Establish and Maintain an Access Control Policy",
        "description": "Establish and maintain an access control policy for enterprise assets.",
        "criticality": "Foundational",
    },
    "7.1": {
        "group": "Continuous Vulnerability and Patch Management",
        "title": "Establish and Maintain a Vulnerability Management Process",
        "description": "Establish and maintain a process to identify, classify, remediate and mitigate vulnerabilities.",
        "criticality": "Foundational",
    },
    "8.1": {
        "group": "Audit Logging and Event Detection",
        "title": "Establish and Maintain an Audit Logging Process",
        "description": "Establish and maintain an audit logging process that captures and logs security-relevant events.",
        "criticality": "Foundational",
    },
    "9.1": {
        "group": "Email and Web Browser Protections",
        "title": "Establish and Maintain a Secure Email Gateway",
        "description": "Establish and maintain an email gateway that filters and scans for malicious content.",
        "criticality": "Foundational",
    },
    "10.1": {
        "group": "Malware Defenses",
        "title": "Establish and Maintain Endpoint Protection",
        "description": "Establish and maintain endpoint protection tools on all enterprise assets.",
        "criticality": "Foundational",
    },
}

# ---------------------------------------------------------------------------
# MITRE ATT&CK Framework — Top 20 Most Common Techniques
# ---------------------------------------------------------------------------

MITRE_ATTACK_TECHNIQUES = {
    "T1566": {
        "tactic": "Initial Access",
        "technique": "Phishing",
        "description": "Adversaries send phishing messages to gain access or gather information.",
        "sub_techniques": ["T1566.001", "T1566.002", "T1566.003"],
    },
    "T1566.001": {
        "tactic": "Initial Access",
        "technique": "Phishing: Spearphishing Attachment",
        "description": "Adversaries send phishing messages with malicious attachments.",
    },
    "T1566.002": {
        "tactic": "Initial Access",
        "technique": "Phishing: Spearphishing Link",
        "description": "Adversaries send phishing messages with malicious links.",
    },
    "T1200": {
        "tactic": "Initial Access",
        "technique": "Hardware Additions",
        "description": "Adversaries introduce computer hardware that can be used to gain initial access.",
    },
    "T1190": {
        "tactic": "Initial Access",
        "technique": "Exploit Public-Facing Application",
        "description": "Adversaries exploit weaknesses in internet-facing applications.",
    },
    "T1133": {
        "tactic": "Initial Access",
        "technique": "External Remote Services",
        "description": "Adversaries leverage external remote services to gain initial access.",
    },
    "T1200": {
        "tactic": "Execution",
        "technique": "Command and Scripting Interpreter",
        "description": "Adversaries use command and scripting interpreters to execute code.",
    },
    "T1059": {
        "tactic": "Execution",
        "technique": "Command and Scripting Interpreter",
        "description": "Adversaries abuse command and script interpreters for execution.",
        "sub_techniques": [
            "T1059.001",  # PowerShell
            "T1059.003",  # Windows Command Shell
            "T1059.004",  # Unix Shell
        ],
    },
    "T1072": {
        "tactic": "Execution",
        "technique": "Software Deployment Tools",
        "description": "Adversaries use software deployment tools to execute code.",
    },
    "T1053": {
        "tactic": "Execution",
        "technique": "Scheduled Task/Job",
        "description": "Adversaries abuse task scheduling functionality for execution.",
    },
    "T1047": {
        "tactic": "Execution",
        "technique": "Windows Management Instrumentation",
        "description": "Adversaries use WMI to execute code and obtain system information.",
    },
    "T1021": {
        "tactic": "Lateral Movement",
        "technique": "Remote Services",
        "description": "Adversaries use remote services to move laterally through an environment.",
    },
    "T1570": {
        "tactic": "Lateral Movement",
        "technique": "Lateral Tool Transfer",
        "description": "Adversaries move tools between systems during lateral movement.",
    },
    "T1550": {
        "tactic": "Lateral Movement",
        "technique": "Use Alternate Authentication Material",
        "description": "Adversaries use alternate authentication material to move laterally.",
    },
    "T1563": {
        "tactic": "Lateral Movement",
        "technique": "Remote Service Session Hijacking",
        "description": "Adversaries hijack existing remote sessions.",
    },
    "T1040": {
        "tactic": "Credential Access",
        "technique": "Network Sniffing",
        "description": "Adversaries sniff network traffic to capture credentials.",
    },
    "T1110": {
        "tactic": "Credential Access",
        "technique": "Brute Force",
        "description": "Adversaries use brute force to access accounts.",
    },
    "T1187": {
        "tactic": "Credential Access",
        "technique": "Forced Authentication",
        "description": "Adversaries capture credentials through forced authentication.",
    },
    "T1056": {
        "tactic": "Collection",
        "technique": "Input Capture",
        "description": "Adversaries capture user input to collect credentials and sensitive information.",
    },
    "T1123": {
        "tactic": "Collection",
        "technique": "Audio Capture",
        "description": "Adversaries capture audio from the target environment.",
    },
}

# ---------------------------------------------------------------------------
# Convenience exports and lookup functions
# ---------------------------------------------------------------------------


def get_all_frameworks() -> dict[str, dict[str, object]]:
    """Return all framework reference data as a combined dict."""
    return {
        "nist_800_53": NIST_800_53_CONTROLS,
        "iso_27001": ISO_27001_CONTROLS,
        "cis_controls_v8": CIS_CONTROLS_V8,
        "mitre_attack": MITRE_ATTACK_TECHNIQUES,
    }


def lookup_by_id(framework: str, control_id: str) -> dict[str, object] | None:
    """Look up a specific control/technique by ID across frameworks.

    Args:
        framework: Framework name ('nist_800_53', 'iso_27001', 'cis_controls_v8', 'mitre_attack').
        control_id: Control or technique ID.

    Returns:
        Control/technique details dict, or None if not found.
    """
    frameworks = {
        "nist_800_53": NIST_800_53_CONTROLS,
        "iso_27001": ISO_27001_CONTROLS,
        "cis_controls_v8": CIS_CONTROLS_V8,
        "mitre_attack": MITRE_ATTACK_TECHNIQUES,
    }

    framework_dict = frameworks.get(framework)
    if framework_dict:
        return framework_dict.get(control_id)

    return None


def search_framework(framework: str, query: str) -> list[tuple[str, dict[str, object]]]:
    """Search for controls/techniques matching a query string.

    Args:
        framework: Framework name.
        query: Search query (case-insensitive).

    Returns:
        List of (id, details) tuples matching the query.
    """
    frameworks = {
        "nist_800_53": NIST_800_53_CONTROLS,
        "iso_27001": ISO_27001_CONTROLS,
        "cis_controls_v8": CIS_CONTROLS_V8,
        "mitre_attack": MITRE_ATTACK_TECHNIQUES,
    }

    framework_dict = frameworks.get(framework)
    if not framework_dict:
        return []

    query_lower = query.lower()
    results = []

    for control_id, control_data in framework_dict.items():
        control_str = str(control_data).lower()
        if query_lower in control_str:
            results.append((control_id, control_data))

    return results
