# documents.py
# These are your source documents
# In real life: PDFs, Word docs, web pages
# Here: plain strings for simplicity

DOCUMENTS = [
    {
        "id":      "doc_1",
        "title":   "PII Policy",
        "content": """
        Personal Identifiable Information (PII) Policy.
        All customer PII including names, emails, phone numbers
        must be encrypted using AES-256 at rest.
        PII must be encrypted using TLS in transit.
        Retention period for PII is 3 years after last transaction.
        Access to PII requires explicit Data Steward approval.
        PII must never be stored in logs or debug outputs.
        Quarterly audits of PII access are mandatory.
        """
    },
    {
        "id":      "doc_2",
        "title":   "GDPR Policy",
        "content": """
        GDPR Compliance Policy.
        Article 17 Right to Erasure: customers can request
        deletion of all their personal data at any time.
        Organisation must complete deletion within 30 days.
        Deletion must cascade to all downstream systems.
        Audit log of every deletion must be kept for 5 years.
        Exceptions apply for legal obligations and public interest.
        Data transfers outside EU require explicit consent.
        """
    },
    {
        "id":      "doc_3",
        "title":   "Data Retention Policy",
        "content": """
        Data Retention Rules.
        Financial transaction data must be retained for 7 years.
        Customer profile data retained for 3 years post relationship.
        Audit logs retained minimum 5 years.
        Marketing and campaign data retained 1 year.
        After retention period data must be securely deleted.
        Retention periods reviewed annually by governance team.
        """
    },
    {
        "id":      "doc_4",
        "title":   "Access Control Policy",
        "content": """
        Access Control and Security Policy.
        Least privilege principle enforced for all systems.
        All access requests require manager approval.
        Quarterly access reviews mandatory for all roles.
        Privileged access requires two-factor authentication.
        All access events logged and monitored.
        Suspicious access patterns trigger automatic alerts.
        """
    },
    {
        "id":      "doc_5",
        "title":   "Insurance Claims Policy",
        "content": """
        Insurance Claims Processing Policy.
        All claims must be registered within 24 hours of receipt.
        Claims data retained for minimum 7 years.
        Claims above 50000 require senior adjuster review.
        Fraud indicators must be flagged within 24 hours.
        Customer must be notified of claim status within 5 days.
        Claims processing must follow FCA guidelines.
        """
    }
]