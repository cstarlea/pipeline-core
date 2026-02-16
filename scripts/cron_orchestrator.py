#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import subprocess

ROOT = Path('/root/.openclaw/workspace/pipeline-core')
ORCH_RUNS = ROOT / 'orchestration' / 'runs'
AGENTS = ROOT / 'agents'


def latest_run_id():
    if not ORCH_RUNS.exists():
        return None
    runs = [p for p in ORCH_RUNS.iterdir() if p.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


def main():
    run_id = latest_run_id()
    if not run_id:
        return

    # Run orchestrate (writes spawn_request.json when needed)
    subprocess.run(['python3', str(ROOT / 'scripts' / 'pipeline.py'), 'orchestrate', '--run-id', run_id], check=True)

    # Mark any spawn_request for cron agent to pick up
    for req in (AGENTS / run_id).glob('*/inbox/spawn_request.json'):
        ready = req.parent / 'spawn_ready'
        ready.write_text('ready')


if __name__ == '__main__':
    main()
