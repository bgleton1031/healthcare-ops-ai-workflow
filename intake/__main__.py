"""Run with python -m intake path/to/record.json."""

import argparse
import json
from pathlib import Path

from .rules import IntakeRecord, evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Recommend a queue for a synthetic intake record; no routing occurs.")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.record.read_text(encoding="utf-8-sig"))
        result = evaluate(IntakeRecord.from_dict(payload))
    except (OSError, ValueError) as error:
        parser.exit(2, f"Unable to evaluate record: {error}\n")
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
