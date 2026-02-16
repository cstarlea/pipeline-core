#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import subprocess
import yaml

ROOT = Path('/root/.openclaw/workspace/pipeline-core')
ORCH_RUNS = ROOT / 'orchestration' / 'runs'
AGENTS = ROOT / 'agents'
ROSTER = ROOT / 'roster' / 'roles.yaml'


def latest_run_id():
    if not ORCH_RUNS.exists():
        return None
    runs = [p for p in ORCH_RUNS.iterdir() if p.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].name


def load_roster():
    if not ROSTER.exists():
        return {}
    return yaml.safe_load(ROSTER.read_text()) or {}


def required_outputs(roster: dict) -> list[str]:
    approval = roster.get('approval', {}) if roster else {}
    outputs = approval.get('required_outputs')
    if outputs:
        return outputs
    # fallback: role outputs
    roles = roster.get('roles', []) if roster else []
    return [r.get('output') for r in roles if r.get('output')]


def outputs_exist(run_id: str, outputs: list[str]) -> bool:
    run_dir = ORCH_RUNS / run_id
    if not run_dir.exists():
        return False
    return all((run_dir / name).exists() for name in outputs)


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

    # If all required outputs exist, proceed with gates -> approve -> run
    roster = load_roster()
    outputs = required_outputs(roster)
    if outputs and outputs_exist(run_id, outputs):
        subprocess.run(['python3', str(ROOT / 'scripts' / 'pipeline.py'), 'gates', '--run-id', run_id], check=True)
        subprocess.run(['python3', str(ROOT / 'scripts' / 'pipeline.py'), 'approve', '--run-id', run_id], check=True)
        task_path = ROOT / 'runs' / run_id / 'task.yaml'
        subprocess.run(['python3', str(ROOT / 'scripts' / 'pipeline.py'), 'run', '--task', str(task_path)], check=True)


if __name__ == '__main__':
    main()
