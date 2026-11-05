# Citizen developer guide

Start from one of the three governed templates in Workflow Studio. Configure only registered triggers, sources, conditions, and actions. Preview before saving, run in test mode, and request approval whenever an action changes CRM data. An approval is cryptographically bound to its target and payload; editing the proposed task invalidates reuse of that approval.

The application intentionally generates structured JSON configuration rather than executable Python. Review execution history and audit evidence after each run. Escalate failures instead of bypassing validation.

