# ADR 0002 - Initial schema (MVP)

Minimal tables:
- orgs
- users
- memberships
- transactions
- tasks
- timeline_items
- audit_events

Notes:
- Prefer UUID primary keys
- Add indexes on transaction_id, due_at, org_id
