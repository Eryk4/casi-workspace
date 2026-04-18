from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _git_candidates() -> list[str]:
    candidates = ["git"]
    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        desktop_root = Path(local_app_data) / "GitHubDesktop"
        if desktop_root.exists():
            versions = sorted(desktop_root.glob("app-*"), reverse=True)
            for version in versions:
                git_path = version / "resources" / "app" / "git" / "cmd" / "git.exe"
                if git_path.exists():
                    candidates.append(str(git_path))
    # deduplicate while preserving order
    return list(dict.fromkeys(candidates))


def _run_git(arguments: list[str]) -> tuple[str, str]:
    last_error: str | None = None
    for git_exe in _git_candidates():
        try:
            completed = subprocess.run(
                [git_exe, *arguments],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except OSError as error:
            last_error = str(error)
            continue
        except subprocess.SubprocessError as error:
            last_error = str(error)
            continue

        if completed.returncode == 0:
            return completed.stdout.strip(), git_exe
        last_error = completed.stderr.strip() or completed.stdout.strip() or f"git exited {completed.returncode}"

    raise RuntimeError(f"Nie udalo sie uruchomic git: {last_error or 'brak wykonania polecenia'}")


def _build_default_release_id() -> str:
    short_sha, _ = _run_git(["rev-parse", "--short", "HEAD"])
    today = datetime.now().strftime("%Y-%m-%d")
    return f"{today}.{short_sha}"


def _is_worktree_dirty() -> bool:
    status_output, _ = _run_git(["status", "--porcelain"])
    return bool(status_output.strip())


def _upsert_env_key(path: Path, key: str, value: str) -> None:
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    key_pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    updated: list[str] = []
    replaced = False

    for line in lines:
        if key_pattern.match(line):
            if not replaced:
                updated.append(f"{key}={value}")
                replaced = True
            continue
        updated.append(line)

    if not replaced:
        if updated and updated[-1].strip():
            updated.append("")
        updated.append(f"{key}={value}")

    path.write_text("\n".join(updated).rstrip("\n") + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ustawia INVOICE_APP_RELEASE_ID w .env.local na release oparty o aktualny commit, "
            "aby latwiej utrzymac zgodnosc wersji lokalnie i na Railway."
        )
    )
    parser.add_argument(
        "--release-id",
        help="Wymusza konkretny release id zamiast automatycznie generowanego YYYY-MM-DD.<shortsha>.",
    )
    parser.add_argument(
        "--env-file",
        default=".env.local",
        help="Sciezka do pliku env wzgledem katalogu repo (domyslnie: .env.local).",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Tylko wypisuje release id, bez zapisu do pliku env.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    release_id = (args.release_id or "").strip() or _build_default_release_id()
    env_path = (ROOT / args.env_file).resolve()

    if not args.print_only:
        _upsert_env_key(env_path, "INVOICE_APP_RELEASE_ID", release_id)
        print(f"[OK] Zapisano INVOICE_APP_RELEASE_ID={release_id} w {env_path}")
    else:
        print(f"[INFO] INVOICE_APP_RELEASE_ID={release_id}")

    _, git_exe = _run_git(["rev-parse", "--short", "HEAD"])
    print(f"[INFO] Git executable: {git_exe}")

    if _is_worktree_dirty():
        print("[WARN] Repo ma niezacommitowane zmiany. Zadbaj, by deploy szedl z przetestowanego commita.")

    print("")
    print("Na Railway ustaw ta sama wartosc:")
    print(f"INVOICE_APP_RELEASE_ID={release_id}")
    print("")
    print("Po deployu sprawdz parity:")
    print("python compare_environment_parity.py --remote-base https://<twoj-adres-railway> --require-same-release --require-same-assets")


if __name__ == "__main__":
    main()
