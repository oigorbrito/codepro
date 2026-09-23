"""Allow `python -m arkx` to use the Dekon CLI boundary."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
