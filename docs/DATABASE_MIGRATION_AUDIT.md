# Database migration audit

This read-only audit checks whether the declared SQLite schema, PostgreSQL schema, and canonical migration manifest remain aligned. It does not connect to PostgreSQL, open a user database, migrate data, read `.env.local`, seed, reset, or touch storage.

## Run

```powershell
python scripts/audit_database_migration.py
python run_quality_checks.py --profile database-migration-audit
```

Optional sanitized reports are written to `reports/database_migration_audit.json` and `reports/database_migration_audit.md`.

## Current contract

- 78 SQLite application tables.
- 78 PostgreSQL application tables.
- 73 explicitly migrated persistent tables.
- 5 explicitly excluded runtime/environment-bound tables.
- 0 unclassified tables.
- 0 persistent tables missing from the migrator.

The audit derives current migration decisions from `app/data_migration_manifest.py`; it does not maintain a competing allowlist. Any new schema table without a manifest decision is a blocker. Any persistent manifest table missing from the migration order, any manifest table missing from the schema, or any dependency ordered after its child is also a blocker.

The excluded tables are:

- `casi_schema_metadata` — recreated by the idempotent schema bootstrap;
- `google_calendar_oauth_states` — short-lived OAuth state; authorization is restarted;
- `system_email_oauth_states` — short-lived OAuth state; authorization is restarted;
- `task_reminder_worker_heartbeats` — process-local lease/heartbeat state;
- `user_sessions` — environment-bound session/token hashes; users sign in again.

All other current tables are treated as durable business or operational/audit data and are migrated. The complete per-table classification, dependencies, transformations, verification rules, limitations, and future-table checklist are documented in `docs/SQLITE_POSTGRESQL_MIGRATION_COVERAGE.md`.

The audit also relies on a separate KSeF override integrity regression. Approval-linked overrides must point to an existing approval for the same invoice and organization; only directly approved corrections may have a NULL approval reference. Orphans and cross-context links remain migration blockers.

The audit is static. Executable PostgreSQL verification remains a mandatory gate on a newly created disposable PostgreSQL database before staging activation.
