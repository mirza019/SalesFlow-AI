# Prototype security

SalesOps AI enforces authentication, role permissions, exact-payload approvals, audit logging, and secret redaction in Python services. The AI agent can invoke only registered tools with Pydantic-validated arguments; it has no arbitrary SQL, Python, shell, or browser access. CRM-changing operations require an approval that matches the action type, target record, and canonical payload hash.

Local demo passwords are stored as Argon2id hashes. Failed sign-in attempts are throttled, and Streamlit sessions expire after 30 minutes. Demo credentials are intended only for local evaluation and must be replaced before shared or production deployment.

## Current limitations

- Sessions rely on Streamlit state rather than an enterprise session service.
- SQLite is intended for a single-host demonstration.
- Local transport uses plain HTTP unless a reverse proxy provides TLS.
- The prototype has no enterprise identity provider, row-level database policy, or external immutable audit store.
- The separate CRM simulator and browser RPA require their own deployment and security controls.

Before production use, add SSO through an enterprise identity provider, TLS, centralized secret management, CSRF protections, managed database roles, monitoring, backups, access recertification, and immutable audit retention.
