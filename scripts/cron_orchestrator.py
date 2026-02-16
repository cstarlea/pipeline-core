#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import subprocess

ROOT = Path('/root/.openclaw/workspace/pipeline-core')
AGENTS = ROOT / 'agents'


def main():
    # Find latest run folder by mtime
    runs = [p for p in AGENTS.iterdir() if p.is_dir()]
    if not runs:
        return
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    run_id = runs[0].name

    # Run orchestrate (writes spawn_request.json when needed)
    subprocess.run(['python3', str(ROOT / 'scripts' / 'pipeline.py'), 'orchestrate', '--run-id', run_id], check=True)

    # If a spawn_request exists, call sessions_spawn via a simple subprocess to a helper (we can't call tools here)
    # Signal via a file for the main agent to pick up (manual until gateway hook is added)
    for req in (AGENTS / run_id).glob('*/inbox/spawn_request.json'):
        # touch a ready marker so the gateway cron can spawn
        ready = req.parent / 'spawn_ready'
        ready.write_text('ready')


if __name__ == '__main__':
    main()
