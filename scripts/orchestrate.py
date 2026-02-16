#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description="Sequential orchestrator (wrapper for pipeline.py orchestrate)")
    p.add_argument("--run-id", required=True)
    args = p.parse_args()

    subprocess.run(
        ["python3", str(ROOT / "scripts" / "pipeline.py"), "orchestrate", "--run-id", args.run_id],
        check=True,
    )


if __name__ == "__main__":
    main()
