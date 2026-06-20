from __future__ import annotations

from game.engine.validation import DataValidationError, validate_data_dir


def main() -> int:
    try:
        validate_data_dir()
    except DataValidationError as exc:
        print("Data validation failed:")
        for issue in exc.issues:
            print(f"- {issue}")
        return 1

    print("Data validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
