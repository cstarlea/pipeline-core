#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "orchestration" / "runs"

REQUIRED = {
    "01-architecture.md",
    "02-implementation.md",
    "03-data-notes.md",
    "04-qa-report.md",
    "05-release-notes.md",
    "FINAL.md",
    "CHECKLIST.md",
}


def ready(run_dir: Path) -> bool:
    if not REQUIRED.issubset({p.name for p in run_dir.iterdir() if p.is_file()}):
        return False
    text = (run_dir / "CHECKLIST.md").read_text()
    return "- [ ]" in text  # only approve if not already complete


def main():
    if not RUNS.exists():
        return
    for run_dir in RUNS.iterdir():
        if not run_dir.is_dir():
            continue
        if ready(run_dir):
            subprocess.run([
                "python3",
                str(ROOT / "scripts" / "pipeline.py"),
                "approve",
                "--run-id",
                run_dir.name,
            ], check=True)


if __name__ == "__main__":
    main()
