from __future__ import annotations

import argparse
import json
import re
import urllib.request
from typing import Any


def _fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def _asset_versions(html: str) -> list[str]:
    pattern = re.compile(
        r"/(styles\.css\?v=[^\"']+|workspace-shell\.css\?v=[^\"']+|knowledge-overrides\.css\?v=[^\"']+)"
    )
    return sorted({match.group(1) for match in pattern.finditer(html)})


def _compare_maps(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    local_keys = set(local.keys())
    remote_keys = set(remote.keys())
    only_local = sorted(local_keys - remote_keys)
    only_remote = sorted(remote_keys - local_keys)

    shared_diff: list[str] = []
    for key in sorted(local_keys & remote_keys):
        if local[key] != remote[key]:
            shared_diff.append(key)

    return {
        "only_local": only_local,
        "only_remote": only_remote,
        "shared_value_diff": shared_diff,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Porownuje zgodnosc lokalnej i zdalnej instancji aplikacji.")
    parser.add_argument("--local-base", default="http://127.0.0.1:8000")
    parser.add_argument("--remote-base", required=True)
    parser.add_argument(
        "--require-same-release",
        action="store_true",
        help="Zwraca kod wyjscia 1, jesli app_release_id lokalnie i zdalnie sie roznia.",
    )
    parser.add_argument(
        "--require-same-assets",
        action="store_true",
        help="Zwraca kod wyjscia 1, jesli wersje kluczowych assetow CSS lokalnie i zdalnie sie roznia.",
    )
    parser.add_argument(
        "--fail-on-meta-diff",
        action="store_true",
        help="Zwraca kod wyjscia 1, jesli /api/meta ma roznice poza dozwolonymi kluczami.",
    )
    parser.add_argument(
        "--meta-allow-diff-key",
        action="append",
        default=[],
        help="Klucz /api/meta dopuszczony do roznicy przy --fail-on-meta-diff (mozna podac wiele razy).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    local_base = args.local_base.rstrip("/")
    remote_base = args.remote_base.rstrip("/")

    report: dict[str, Any] = {
        "local_base": local_base,
        "remote_base": remote_base,
    }

    try:
        local_meta = _fetch_json(f"{local_base}/api/meta")
    except Exception as error:  # noqa: BLE001
        report["local_meta_error"] = str(error)
        local_meta = None

    try:
        remote_meta = _fetch_json(f"{remote_base}/api/meta")
    except Exception as error:  # noqa: BLE001
        report["remote_meta_error"] = str(error)
        remote_meta = None

    if local_meta is not None:
        report["local_meta_keys"] = sorted(local_meta.keys())
        report["local_release"] = local_meta.get("app_release_id")
        report["local_database_label"] = local_meta.get("database_label")
        report["local_db_engine"] = local_meta.get("db_engine")

    if remote_meta is not None:
        report["remote_meta_keys"] = sorted(remote_meta.keys())
        report["remote_release"] = remote_meta.get("app_release_id")
        report["remote_database_label"] = remote_meta.get("database_label")
        report["remote_db_engine"] = remote_meta.get("db_engine")

    if local_meta is not None and remote_meta is not None:
        report["meta_diff"] = _compare_maps(local_meta, remote_meta)

    try:
        local_html = _fetch_text(f"{local_base}/")
        report["local_assets"] = _asset_versions(local_html)
    except Exception as error:  # noqa: BLE001
        report["local_assets_error"] = str(error)

    try:
        remote_html = _fetch_text(f"{remote_base}/")
        report["remote_assets"] = _asset_versions(remote_html)
    except Exception as error:  # noqa: BLE001
        report["remote_assets_error"] = str(error)

    allow_keys = sorted({item.strip() for item in args.meta_allow_diff_key if item.strip()})
    failures: list[str] = []
    checks: dict[str, Any] = {
        "require_same_release": bool(args.require_same_release),
        "require_same_assets": bool(args.require_same_assets),
        "fail_on_meta_diff": bool(args.fail_on_meta_diff),
        "meta_allow_diff_keys": allow_keys,
        "passed": True,
        "failures": failures,
    }

    if args.require_same_release:
        local_release = report.get("local_release")
        remote_release = report.get("remote_release")
        if not local_release or not remote_release:
            failures.append("Brak app_release_id po jednej ze stron (local lub remote).")
        elif local_release != remote_release:
            failures.append(f"Niezgodny app_release_id: local={local_release}, remote={remote_release}")

    if args.require_same_assets:
        local_assets = report.get("local_assets")
        remote_assets = report.get("remote_assets")
        if local_assets is None or remote_assets is None:
            failures.append("Brak listy assetow lokalnie lub zdalnie.")
        elif local_assets != remote_assets:
            failures.append("Niezgodne wersje assetow frontendowych.")

    if args.fail_on_meta_diff:
        meta_diff = report.get("meta_diff")
        if meta_diff is None:
            failures.append("Brak porownania /api/meta (blad pobrania local lub remote).")
        else:
            allow_set = set(allow_keys)
            only_local = [key for key in meta_diff.get("only_local", []) if key not in allow_set]
            only_remote = [key for key in meta_diff.get("only_remote", []) if key not in allow_set]
            shared_value_diff = [key for key in meta_diff.get("shared_value_diff", []) if key not in allow_set]
            if only_local or only_remote or shared_value_diff:
                failures.append(
                    "Niezgodne /api/meta poza dozwolonymi kluczami: "
                    f"only_local={only_local}, only_remote={only_remote}, shared_value_diff={shared_value_diff}"
                )

    checks["passed"] = not failures
    report["checks"] = checks

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
