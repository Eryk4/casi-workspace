param(
    [switch]$SkipDockerStart,
    [switch]$KeepContainer
)

$ErrorActionPreference = "Stop"

$ComposeFile = "docker-compose.postgres-migration-test.yml"
$DatabaseUrl = "postgresql://casi_test:casi_test_password@localhost:55432/casi_migration_test"
$SafeDatabaseLabel = "postgresql://casi_test:***@localhost:55432/casi_migration_test"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "== $Message =="
}

function Test-CommandAvailable {
    param([string]$CommandName)
    return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Assert-TestDatabaseUrl {
    param([string]$Url)

    if (-not $Url.Contains("casi_migration_test")) {
        throw "Refusing to run: database URL must point to casi_migration_test."
    }
    if ($Url -match "digitalocean|ondigitalocean|railway|rlwy|prod|production") {
        throw "Refusing to run: database URL looks production-like or managed."
    }
    if ($Url -match "5432/(postgres|template0|template1)$") {
        throw "Refusing to run: database URL points to a default PostgreSQL database."
    }
}

Write-Step "CASI local PostgreSQL migration check"
Write-Host "This script uses only the synthetic SQLite created by scripts/check_postgres_migration.py."
Write-Host "It does not set DATABASE_URL or INVOICE_DATABASE_URL."
Write-Host "It does not touch data/magazyn, S3, DigitalOcean, or production data."
Write-Host "Test PostgreSQL target: $SafeDatabaseLabel"

Assert-TestDatabaseUrl -Url $DatabaseUrl

if (-not $SkipDockerStart) {
    if (-not (Test-CommandAvailable "docker")) {
        Write-Host ""
        Write-Host "Docker is not available. No container was started."
        Write-Host "Install/start Docker Desktop, or run PostgreSQL manually and set CASI_TEST_POSTGRES_DATABASE_URL yourself."
        exit 2
    }
    if (-not (Test-Path $ComposeFile)) {
        throw "Missing $ComposeFile. Run this script from the CASI Workspace repository root."
    }

    Write-Step "Starting isolated test PostgreSQL"
    docker compose -f $ComposeFile up -d

    Write-Step "Waiting for PostgreSQL readiness"
    $ready = $false
    for ($attempt = 1; $attempt -le 40; $attempt++) {
        docker exec casi-postgres-migration-test pg_isready -U casi_test -d casi_migration_test | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        throw "Test PostgreSQL did not become ready in time."
    }
}

Write-Step "Running postgres-migration-check"
$env:CASI_TEST_POSTGRES_DATABASE_URL = $DatabaseUrl
python run_quality_checks.py --profile postgres-migration-check
$exitCode = $LASTEXITCODE

if (-not $KeepContainer -and -not $SkipDockerStart -and (Test-CommandAvailable "docker")) {
    Write-Step "Stopping test PostgreSQL container"
    docker compose -f $ComposeFile down
}

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "postgres-migration-check failed with exit code $exitCode."
    exit $exitCode
}

Write-Step "Done"
Write-Host "postgres-migration-check passed on the isolated local test database."
