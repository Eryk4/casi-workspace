# Staging prerequisites — provider-neutral contract

## Purpose

This contract prepares CASI Workspace for a staging environment on any PaaS with PostgreSQL and S3-compatible durable storage. It does not deploy resources and contains no provider credentials.

The application must never silently replace PostgreSQL with SQLite or S3 with local storage in staging.

## Runtime versions

- Python: `3.11.9` in `.python-version`.
- Node.js: `24.18.0` in `.nvmrc`.
- Node engine: `>=24.18.0 <25`.
- npm engine: `>=11.16.0 <12`.

Local development, CI, staging, and later production should use the same runtime lines. Upgrade these files and `frontend/package.json` together, then rerun the complete regression suite before deployment.

## Database lifecycle

Schema migration, schema validation, administrator creation, demo seed, filesystem preparation, and HTTP startup are separate operations.

### Explicit schema command

```bash
python -m app.cli.database_migrate --check
python -m app.cli.database_migrate --apply
```

Both commands disable local env-file loading before importing application configuration. They require an explicit PostgreSQL engine and DSN. They never create a default administrator, seed data, reset data, start HTTP, or initialize storage.

`--check` opens the database read-only and returns:

- exit `0` when the current schema marker is ready;
- exit `3` when an explicit migration is required;
- exit `1` for unsafe configuration or a system-level failure;
- exit `2` for invalid CLI usage.

`--apply` runs only the existing additive/idempotent schema bootstrap and records the current schema marker.

### Backend bootstrap modes

`INVOICE_DATABASE_BOOTSTRAP_MODE` supports:

- `auto` — compatible local development: prepare local directories, migrate schema, create the local default administrator, and optionally seed;
- `validate` — staging contract: read-only schema readiness check, no migration, no administrator, no seed, no storage directory creation;
- `off` — no migration and no validation; reserved for controlled diagnostics, not recommended for staging.

Staging must use `validate`. A missing schema stops the backend before services or HTTP start.

The provider-neutral backend command is:

```bash
python run.py --mode web --host 0.0.0.0 --port <platform port>
```

`web` does not start the legacy email, task-reminder, or knowledge polling loops. The first staging administrator remains a separate future security workflow; never use the local default password.

## Frontend

```bash
cd frontend
npm run build
npm run start:paas
```

`start:paas` runs the production Next.js server on `0.0.0.0` and reads `PORT`. Missing `PORT` uses local smoke-test port `3000`. Invalid ports fail before Next.js starts. The wrapper is Node-based and works on Windows and Unix-like PaaS environments.

## Durable S3-compatible storage

The storage provider is selected with:

```text
INVOICE_STORAGE_BACKEND=s3
INVOICE_REQUIRE_DURABLE_STORAGE=true
INVOICE_S3_REQUIRE_TLS=true
```

Required S3-compatible configuration:

- `INVOICE_S3_ENDPOINT_URL` using HTTPS;
- `INVOICE_S3_REGION`;
- `INVOICE_S3_BUCKET`;
- `INVOICE_S3_ACCESS_KEY_ID`;
- `INVOICE_S3_SECRET_ACCESS_KEY`;
- optional `INVOICE_S3_PREFIX`.

No provider name appears in the domain or storage implementation. AWS S3, DigitalOcean Spaces, Cloudflare R2, and other compatible services differ only in endpoint, region, credentials, and addressing provided by their standard S3 endpoint.

When durable storage is required, `local` is rejected and incomplete S3 configuration stops startup. S3 errors never create a local fallback copy. Documents, invoice artifacts, OCR output, knowledge uploads, whiteboard files, and entity attachments use the shared storage abstraction.

The watched local knowledge-folder integration is deliberately unavailable with S3. Normal knowledge listing no longer creates a local organization folder. OCR may use an operating-system temporary directory for transient processing only; it is not durable storage or a cache.

The current storage protocol has no delete operation. Object lifecycle/deletion policy remains a separate future decision.

## Staging preflight

```bash
python -m app.cli.staging_preflight
```

Preflight is read-only. It does not load `.env.local`, migrate, seed, create users, start HTTP, write to S3, or create storage directories.

It checks:

- exact Python runtime and required modules;
- explicit PostgreSQL and DSN;
- read-only database connectivity and schema marker;
- bootstrap mode `validate`;
- durable S3 storage and required configuration;
- HTTPS storage endpoint;
- `Europe/Warsaw` from `tzdata`;
- disabled seed and reset;
- scheduler runtime state;
- absence of SQLite and local-storage fallbacks.

The JSON report contains statuses only, never DSNs, access keys, secret keys, or endpoint credentials.

## Safe staging sequence

1. Pin and verify Python, Node, and npm.
2. Provision an empty staging PostgreSQL and a private staging S3-compatible bucket.
3. Put DSN and S3 credentials only in the platform secret store.
4. Set `INVOICE_LOAD_LOCAL_ENV=0`, PostgreSQL, durable S3, seed off, reset off, bootstrap `validate`, and scheduler runtime `false`.
5. Run `database_migrate --check`; expect migration required for an empty database.
6. Run `database_migrate --apply`.
7. Run `database_migrate --check`; expect ready.
8. Run `staging_preflight`; require full PASS.
9. Start backend in `web` mode and verify read-only `/health`.
10. Build and start the frontend with `start:paas`.
11. Create the first staging administrator through a separately reviewed secure workflow.
12. Run scheduler `--check` while its runtime gate is false.
13. Enable one test user schedule only after application and organization isolation checks pass.
14. Enable the scheduler runtime only for its dedicated job and perform one controlled `--once`.

## Environment contract

Required staging values:

```text
INVOICE_LOAD_LOCAL_ENV=0
INVOICE_DB_ENGINE=postgresql
INVOICE_DATABASE_URL=<platform secret>
INVOICE_DATABASE_BOOTSTRAP_MODE=validate
INVOICE_ENABLE_DEMO_SEED=0
CASI_ALLOW_LOCAL_SANDBOX_RESET=0
INVOICE_STORAGE_BACKEND=s3
INVOICE_REQUIRE_DURABLE_STORAGE=true
INVOICE_S3_REQUIRE_TLS=true
INVOICE_S3_ENDPOINT_URL=<HTTPS endpoint>
INVOICE_S3_REGION=<region>
INVOICE_S3_BUCKET=<staging bucket>
INVOICE_S3_ACCESS_KEY_ID=<platform secret>
INVOICE_S3_SECRET_ACCESS_KEY=<platform secret>
INVOICE_S3_PREFIX=casi/staging
INVOICE_SECURE_COOKIES=1
INTERNAL_NOTIFICATION_SCHEDULER_RUNTIME_ENABLED=false
```

Use `INVOICE_APP_RELEASE_ID` for an immutable release identifier. Keep Telegram, email autocheck, Slack, and other external delivery credentials unset until separately validated.

## Moving between platforms

Moving between DigitalOcean, Railway, or another PaaS changes mainly:

- environment-variable mapping;
- component build/run commands;
- scheduled-job configuration;
- PostgreSQL DSN binding;
- S3-compatible endpoint and credentials.

CASI domain logic, schema migrator, backend, frontend, storage interface, scheduler, and preflight remain shared.

## Remaining staging-only verification

Before real staging activation, run the migrator and preflight against an empty disposable PostgreSQL and validate the selected S3 provider with a private test bucket. These checks require real staging credentials and are intentionally not performed locally.
