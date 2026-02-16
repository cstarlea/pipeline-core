#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "roster" / "roles.yaml"
RUNS = ROOT / "orchestration" / "runs"
AGENTS = ROOT / "agents"

try:
    import yaml
except Exception:
    yaml = None


def load_roster():
    if yaml and ROSTER.exists():
        return yaml.safe_load(ROSTER.read_text()) or {}
    return {}


def ensure_agent_workspace(role_id: str, run_id: str):
    base = AGENTS / run_id / role_id
    (base / "inbox").mkdir(parents=True, exist_ok=True)
    (base / "outbox").mkdir(parents=True, exist_ok=True)
    (base / "workspace").mkdir(parents=True, exist_ok=True)
    status = {
        "state": "pending",
        "started": None,
        "completed": None,
        "error": None,
        "role": role_id,
        "run_id": run_id,
    }
    (base / "status.json").write_text(json.dumps(status, indent=2))
    return base


def write_instructions(agent_dir: Path, role: dict, run_dir: Path):
    instructions = f"""# Task: {role['id']}

## Objective
Write the role output for this run.

## Run packet
{run_dir}

## Output file
{run_dir / role['output']}

## Requirements
- Read RUN.md and acceptance criteria
- Only touch files in scope described in RUN.md
- Write your deliverable to the output file above
- Write a short summary to outbox/summary.md
- Update status.json to state=completed when done
"""
    (agent_dir / "inbox" / "instructions.md").write_text(instructions)


def update_status(agent_dir: Path, state: str):
    status_path = agent_dir / "status.json"
    status = json.loads(status_path.read_text())
    status["state"] = state
    if state == "running":
        status["started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if state in ("completed", "failed"):
        status["completed"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    status_path.write_text(json.dumps(status, indent=2))


def spawn_role(role: dict, run_dir: Path):
    agent_dir = ensure_agent_workspace(role["id"], run_dir.name)
    write_instructions(agent_dir, role, run_dir)
    update_status(agent_dir, "running")

    print(f"Prepared agent workspace: {agent_dir}")


def main():
    p = argparse.ArgumentParser(description="Prepare agent workspaces (sequential flow handled by orchestrator)")
    p.add_argument("--run-id", required=True)
    args = p.parse_args()

    run_dir = RUNS / args.run_id
    if not run_dir.exists():
        raise SystemExit(f"Run not found: {run_dir}")

    roster = load_roster()
    roles = roster.get("roles", [])

    # default order: as listed
    for role in roles:
        spawn_role(role, run_dir)


if __name__ == "__main__":
    main()
