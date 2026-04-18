from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from typing import Any


def _fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def _asset_versions(html: str) -> list[str]:
    pattern = re.compile(r"/(styles\.css\?v=[^\"']+|workspace-shell\.css\?v=[^\"']+|knowledge-overrides\.css\?v=[^\"']+)")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Porownuje zgodnosc lokalnej i zdalnej instancji aplikacji.")
    parser.add_argument("--local-base", default="http://127.0.0.1:8000")
    parser.add_argument("--remote-base", required=True)
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

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
