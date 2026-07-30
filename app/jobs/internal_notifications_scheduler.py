from __future__ import annotations

import argparse
import json
import sys

from app.bootstrap import build_services


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materializuje brakujace wewnetrzne powiadomienia.")
    parser.add_argument("--once", action="store_true", help="Wykonaj jeden przebieg i zakoncz proces.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.once:
        print("Wymagany jest jawny tryb --once.", file=sys.stderr)
        return 2
    try:
        services = build_services()
        report = services["internal_notification_scheduler_service"].run_once()
    except Exception as error:
        print(
            json.dumps(
                {"status": "initialization_error", "error_code": type(error).__name__},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
