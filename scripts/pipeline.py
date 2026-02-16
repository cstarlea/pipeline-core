#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def write_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def task_create(project_path: Path, goal: str, accepts: list[str]):
    project = load_yaml(project_path)
    now = dt.datetime.now(dt.UTC)
    run_id = now.strftime("run-%Y%m%d-%H%M%S")
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    task = {
        "id": run_id,
        "goal": goal,
        "scope": [project["project"], project["path"]],
        "acceptance": accepts or ["(none provided)"],
        "files_touched": [],
        "tests": [],
        "llm_required": False,
        "model_policy": project.get("model_policy", "subagent_policy"),
        "project": project["project"],
        "repo": project["repo"],
        "path": project["path"],
    }

    write_yaml(run_dir / "task.yaml", task)
    (run_dir / "REPORT.md").write_text("# Run Report\n\nPending.\n")

    # auto-create orchestration run packet with same run_id
    orch_script = ROOT / "orchestration" / "run_packet.py"
    if orch_script.exists():
        import subprocess
        subprocess.run([
            "python3",
            str(orch_script),
            "--objective", goal,
            "--scope", project["project"],
            "--run-id", run_id,
            *sum([["--criterion", c] for c in (accepts or [])], [])
        ], check=True)

    print(run_dir)


def main():
    p = argparse.ArgumentParser(description="Deterministic pipeline runner")
    sp = p.add_subparsers(dest="cmd", required=True)

    c = sp.add_parser("task-create")
    c.add_argument("project")
    c.add_argument("--goal", required=True)
    c.add_argument("--accept", action="append", default=[])

    r = sp.add_parser("run")
    r.add_argument("--task", required=True)

    args = p.parse_args()

    if args.cmd == "task-create":
        task_create(Path(args.project), args.goal, args.accept)
        return

    if args.cmd == "run":
        task = load_yaml(Path(args.task))
        # deterministic-only placeholder; integrate steps here
        print(f"Run {task['id']} for {task['project']} — deterministic placeholder")
        return


if __name__ == "__main__":
    main()
