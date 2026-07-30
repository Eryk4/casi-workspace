# Internal Notification Scheduler Runtime v1

## Status and scope

This document is a provider-neutral operational contract for invoking the existing one-shot worker:

```bash
python -m app.jobs.internal_notifications_scheduler --once
```

It does not activate a cron, platform scheduled job, Windows Task Scheduler task, deploy, or background loop. The repository currently contains a Railway web configuration and planning documentation for DigitalOcean, but it does not identify one confirmed target platform or one verified scheduled-job schema. For that reason this stage intentionally adds no provider-specific deployment file.

An external scheduler may invoke CASI, but it must not implement schedule selection, local-time calculations, materialization, deduplication, claim, lease, or retry. Those rules remain inside CASI Workspace.

## Two independent opt-ins

Both conditions are required before a notification can be materialized automatically:

1. The environment runtime gate is enabled.
2. The recipient's stored schedule is enabled.

The environment kill switch is:

```text
INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=false
```

Missing, empty, `false`, `0`, `no`, `off`, and unknown values fail closed. Only `true`, `1`, `yes`, `tak`, or `on` enable the runtime. The safe repository example is `false`.

When disabled, both `--check` and `--once` exit with code `0` and a sanitized `status=disabled` report before importing application bootstrap code or opening a database connection. No run, notification, audit event, claim, or transaction is created.

## Commands

Diagnostic command:

```bash
python -m app.jobs.internal_notifications_scheduler --check
```

One-shot production command:

```bash
python -m app.jobs.internal_notifications_scheduler --once
```

Both commands are bounded processes. There is no loop or `sleep(300)`. `--once` processes at most 100 due schedules in one invocation. The next invocation handles remaining due schedules. Database uniqueness and the existing claim/lease contract remain the final concurrency protection.

The recommended external invocation interval is every five minutes. This interval is operational configuration, not a recipient materialization frequency. A recipient is still evaluated using their stored local time and IANA timezone, at most once per local calendar day.

## `--check` contract

When the runtime gate is enabled, `--check`:

- validates the explicit database engine and required connection configuration;
- loads `ZoneInfo("Europe/Warsaw")`;
- opens SQLite with `mode=ro` and `PRAGMA query_only=ON`, or PostgreSQL with `default_transaction_read_only=on`;
- counts due enabled schedules with the same due predicate used by the worker;
- reports the fixed batch limit;
- does not initialize or migrate the schema;
- does not create schedule runs or notifications;
- does not materialize attention;
- does not write `event_logs`, billing tables, or any other table.

A missing scheduler schema is an operational error. Apply and verify migrations in the deployment workflow before using `--check`; the diagnostic command never applies them.

## Configuration

### Required to enable the runtime

```text
INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=true
INVOICE_DB_ENGINE=postgresql
INVOICE_DATABASE_URL=<platform secret>
```

`DATABASE_URL` may be used instead of `INVOICE_DATABASE_URL` for PostgreSQL. The connection URL is a secret and must be configured only on the platform.

For an explicitly controlled SQLite environment:

```text
INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=true
INVOICE_DB_ENGINE=sqlite
INVOICE_SQLITE_PATH=<absolute controlled path>
```

The SQLite path is mandatory when the runtime is enabled. The worker must not rely on the repository's local default path.

### Recommended shared runtime settings

```text
INVOICE_ENABLE_DEMO_SEED=0
INVOICE_DB_CONNECT_TIMEOUT_SECONDS=10
INVOICE_DB_INIT_MAX_RETRIES=6
INVOICE_DB_INIT_RETRY_SLEEP_SECONDS=2
```

The scheduler command does not seed, reset, or migrate the database. Existing platform storage settings may still be present because the application service graph is shared, but the notification materializer does not read or write document storage.

There is no environment batch-limit setting in v1. The existing internal limit of 100 is already bounded and avoids another operational knob. The repository enforces an additional maximum of 500 for internal callers.

## Reports and exit codes

Reports are single-line JSON and contain operational fields only. Normal reports include:

- `status` and `runtime_status`;
- `mode`;
- `started_at_utc` and `duration_ms`;
- due, claimed, skipped, succeeded, and failed counts where applicable;
- created and existing notification counts for `--once`;
- `batch_limit`;
- `exit_code`.

Reports do not include connection strings, secrets, cookies, notification bodies, full payloads, or stack traces.

Exit codes:

- `0`: runtime disabled; successful `--check`; or completed `--once`, including a correctly persisted failed schedule;
- `1`: invalid required configuration, database/check initialization failure, or an unhandled process-level error;
- `2`: invalid CLI usage reported by `argparse`.

A single failed schedule does not create a process-level failure or restart loop. Its sanitized failure is stored in run history and other schedules remain eligible for processing.

## Pre-activation checklist

- Deploy code containing the scheduler runtime without enabling it.
- Apply the additive schema on staging through the normal migration/bootstrap procedure.
- Keep `INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=false`.
- Confirm user schedules remain disabled by default.
- Configure platform database secrets without copying local `.env.local` values.
- Run the diagnostic command and confirm `status=disabled`.
- Temporarily enable the flag only in a controlled staging process and run `--check`.

## Controlled staging activation

1. Create or select a separate staging environment and staging database.
2. Set `INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=false`.
3. Apply and verify the scheduler schema on staging.
4. Run `python -m app.jobs.internal_notifications_scheduler --check`; expect `disabled`.
5. Configure one test recipient schedule while the runtime gate remains disabled.
6. Set the runtime flag to `true` for the dedicated staging job only.
7. Run `--check`; verify read-only database connectivity, timezone availability, and the due count.
8. Run `--once` manually once.
9. Inspect sanitized process output, schedule run history, and internal notifications.
10. Run `--once` again and confirm no duplicate logical run or notification.
11. Test two simultaneous manual invocations and confirm one logical claim.
12. Set the runtime flag back to `false` and confirm `--once` returns `disabled` without a new run.
13. Only after this review, create a separate platform scheduled job invoking the exact `--once` command, initially at a configurable five-minute interval.

Do not expose a public port or add an HTTP health check to a one-shot job. Do not copy business logic into platform configuration.

## Emergency shutdown

Primary kill switch:

```text
INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=false
```

After the platform applies that value, later invocations exit before new claims. A run that already owns a lease may finish; the kill switch does not corrupt or delete in-flight history. If necessary:

1. disable the affected user's schedule;
2. stop or pause the external scheduled job;
3. wait for an active lease to finish or expire;
4. keep schedule and run-history rows intact.

No reset, destructive migration, or data deletion is required.

## Diagnostics

- `status=disabled`: environment gate is off; no database was opened.
- `status=ok`, `mode=check`: configuration, timezone, and read-only database query succeeded.
- `status=completed`, `mode=once`: the batch completed; inspect claimed/succeeded/failed/skipped counts.
- `status=configuration_error`: required environment configuration is missing or invalid.
- `status=system_error`: the process could not initialize or complete. The report contains only a sanitized error class.
- A run-history row with `status=failed` is a schedule-level failure and does not imply a process-level failure.

Use internal notification run history and sanitized logs for diagnosis. Never paste connection URLs, tokens, cookies, or `.env.local` content into tickets or logs.

## Rollback

1. Set the runtime flag to `false`.
2. Stop or pause the external scheduled invocation.
3. Leave scheduler tables and run history intact.
4. Do not reverse the additive migration destructively.
5. Roll back application code through the normal deployment mechanism only after the gate is confirmed disabled.

## Provider-neutral deployment example (inactive)

The following is documentation, not an active platform configuration:

```text
kind: one-shot scheduled job
command: python -m app.jobs.internal_notifications_scheduler --once
schedule: every 5 minutes (configurable externally)
public port: none
HTTP health check: none
restart on exit 0: no
runtime flag at creation: false
database claim/lease: remains authoritative
```

Before translating this example to Railway, DigitalOcean, cron, Windows Task Scheduler, or another provider, validate that provider's current official schema and test it in staging. Do not infer syntax from this document.
