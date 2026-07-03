# Storage Migration Plan

This document describes the local dry-run planning step for a future migration from `data/magazyn` to S3-compatible object storage such as DigitalOcean Spaces.

This is not a migration.

The planning script:

- does not connect to DigitalOcean,
- does not require Spaces credentials,
- does not upload files,
- does not delete files,
- does not move files,
- does not update database storage keys.

## Script

```powershell
python scripts/plan_storage_migration.py
```

By default the script scans the configured local storage root, normally:

```text
data/magazyn
```

It writes:

```text
reports/storage_migration_plan.json
reports/storage_migration_plan.md
```

The default report-only S3 prefix is:

```text
casi/dev-test
```

If `INVOICE_S3_PREFIX` is set, the script uses it for the report. The logical `storage_key` in the report never includes this prefix. The `s3_object_key` is shown separately as:

```text
<prefix>/<storage_key>
```

## CLI Options

```powershell
python scripts/plan_storage_migration.py `
  --storage-root data/magazyn `
  --s3-prefix casi/dev-test `
  --output-json reports/storage_migration_plan.json `
  --output-md reports/storage_migration_plan.md
```

Available options:

- `--storage-root <path>`: local storage root to scan.
- `--s3-prefix <prefix>`: report-only target prefix.
- `--output-json <path>`: JSON report path.
- `--output-md <path>`: Markdown summary path.
- `--include-backups`: mark backup files as planned instead of skipped.
- `--fail-on-warnings`: exit with code `1` if warnings are found.
- `--max-large-file-mb <number>`: threshold for `large_file` warnings.

## Areas

The script recognizes these top-level areas:

- `dokumenty`
- `ocr`
- `wiedza`
- `tablica`
- `backup`
- `organizacje`

Other top-level folders are included as `unknown_area`.

Backups are included in the report but are marked as `skipped_backup` by default. Use `--include-backups` only when you intentionally want backup files to be part of the future migration plan. The script never deletes backup files.

## Warnings

The report can include warnings such as:

- `zero_size_file`
- `duplicate_sha256`
- `storage_key_conflict`
- `path_contains_parent_reference`
- `unknown_area`
- `large_file`
- `temporary_file`
- `backup_skipped_by_default`
- `storage_root_missing`

Warnings do not stop the scan. The script records the problem and continues.

## Severity

Each issue is classified as one of:

- `info`: useful context, not a migration risk by itself.
- `warning`: should be reviewed before migration, but does not block the dry-run.
- `error`: filesystem or scan problem that should be fixed or consciously accepted.
- `blocker`: must be fixed before any real migration.

Examples:

- `duplicate_sha256` is `info`; duplicate file content is common for generated placeholders and does not block object migration while storage keys remain unique.
- `backup_skipped_by_default` is `info`.
- `temporary_file`, `large_file`, `unknown_area`, and `zero_size_file` are `warning`.
- `storage_root_missing` is `error`.
- `storage_key_conflict`, `path_contains_parent_reference`, and `invalid_relative_path` are `blocker`.

The JSON report contains:

- `issue_count_by_category`,
- `issue_count_by_severity`,
- `blocker_count`,
- `migration_blocked`,
- `recommended_next_actions`.

The Markdown report redacts the full local storage root and shows relative file paths. The full `storage_root` remains available only in JSON metadata for local operator use.

## Quality Check Profile

```powershell
python run_quality_checks.py --profile storage-migration-plan
```

This profile runs unit tests for the planning script and then runs a dry-run against local `data/magazyn` if that directory exists.

It does not connect to DigitalOcean and does not require secrets.

## Next Step After This Stage

After the dry-run report is clean enough, the next separate stage is a manual test against a private DigitalOcean Spaces bucket using a safe prefix such as:

```text
casi/dev-test
```

Only after the real private bucket test passes should a true migration script be designed.
