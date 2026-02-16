#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
ORCH = ROOT / "orchestration"
ORCH_RUNS = ORCH / "runs"
ORCH_LOGS = ORCH / "logs"
AGENTS = ROOT / "agents"
ROSTER = ROOT / "roster" / "roles.yaml"


MANIFESTS = ROOT / "manifests"


def manifest_path(run_id: str) -> Path:
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    return MANIFESTS / f"{run_id}.json"


def load_manifest(run_id: str) -> dict:
    mp = manifest_path(run_id)
    if mp.exists():
        return json.loads(mp.read_text())
    return {"run_id": run_id, "current_role": None, "last_spawned_at": None}


def save_manifest(run_id: str, data: dict):
    mp = manifest_path(run_id)
    mp.write_text(json.dumps(data, indent=2))


def log_line(run_id: str, message: str):
    ORCH_LOGS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).isoformat()
    (ORCH_LOGS / f"{run_id}.log").open("a").write(f"[{stamp}] {message}\n")


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def write_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def load_roster():
    if ROSTER.exists():
        return yaml.safe_load(ROSTER.read_text()) or {}
    return {}


def ensure_agent_workspace(role_id: str, run_id: str):
    base = AGENTS / run_id / role_id
    (base / "inbox").mkdir(parents=True, exist_ok=True)
    (base / "outbox").mkdir(parents=True, exist_ok=True)
    (base / "workspace").mkdir(parents=True, exist_ok=True)
    status_path = base / "status.json"
    if not status_path.exists():
        status = {
            "state": "pending",
            "started": None,
            "completed": None,
            "error": None,
            "role": role_id,
            "run_id": run_id,
        }
        status_path.write_text(json.dumps(status, indent=2))
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


def load_status(agent_dir: Path):
    status_path = agent_dir / "status.json"
    if not status_path.exists():
        return None
    return json.loads(status_path.read_text())


def update_status(agent_dir: Path, state: str, error: str | None = None):
    status_path = agent_dir / "status.json"
    status = load_status(agent_dir) or {}
    status["state"] = state
    status["error"] = error
    if state == "running":
        status["started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if state in ("completed", "failed"):
        status["completed"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    status_path.write_text(json.dumps(status, indent=2))


def spawn_role(role: dict, run_dir: Path):
    agent_dir = ensure_agent_workspace(role["id"], run_dir.name)
    write_instructions(agent_dir, role, run_dir)
    update_status(agent_dir, "pending")

    prompt = f"""You are a role-specific subagent.

ROLE: {role['id']}
RUN_ID: {run_dir.name}
OBJECTIVE: Write the role output for this run.

SCOPE:
- Allowed files/paths: {run_dir}
- Do not touch anything else.

DELIVERABLES (required):
1) Write output to: {run_dir / role['output']}
2) Write summary to: {agent_dir / 'outbox'}/summary.md
3) Update {agent_dir / 'status.json'} with state=completed or failed.

RULES:
- Deterministic first; no unnecessary tool use.
- If blocked, write a short blocker note in summary.md and set state=failed.
- Do not message the user.
"""

    (agent_dir / "inbox" / "spawn_prompt.txt").write_text(prompt)
    # request file for orchestrator cron to spawn
    req = {
        "role": role["id"],
        "run_id": run_dir.name,
        "agent_dir": str(agent_dir),
        "prompt": prompt,
        "status_path": str(agent_dir / "status.json"),
        "summary_path": str(agent_dir / "outbox" / "summary.md"),
        "output_path": str(run_dir / role["output"]),
    }
    (agent_dir / "inbox" / "spawn_request.json").write_text(json.dumps(req, indent=2))
    return agent_dir


def completion_ok(role: dict, run_dir: Path, agent_dir: Path) -> tuple[bool, str | None]:
    missing = []
    output_path = run_dir / role["output"]
    summary_path = agent_dir / "outbox" / "summary.md"
    if not output_path.exists():
        missing.append(str(output_path))
    if not summary_path.exists():
        missing.append(str(summary_path))
    if missing:
        return False, f"Missing outputs: {', '.join(missing)}"
    return True, None


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
        subprocess.run([
            "python3",
            str(orch_script),
            "--objective", goal,
            "--scope", project["project"],
            "--run-id", run_id,
            *sum([["--criterion", c] for c in (accepts or [])], [])
        ], check=True)

    print(run_dir)


def orchestrate(run_id: str):
    run_dir = ORCH_RUNS / run_id
    if not run_dir.exists():
        raise SystemExit(f"Run not found: {run_dir}")

    roster = load_roster()
    roles = roster.get("roles", [])
    manifest = load_manifest(run_id)

    running_roles = []
    for role in roles:
        agent_dir = AGENTS / run_id / role["id"]
        status = load_status(agent_dir) if agent_dir.exists() else None
        if status and status.get("state") == "running":
            running_roles.append(role["id"])

    if len(running_roles) > 1:
        log_line(run_id, f"ERROR: Multiple roles running: {', '.join(running_roles)}")
        raise SystemExit("Multiple roles running; aborting orchestrate.")

    for role in roles:
        agent_dir = AGENTS / run_id / role["id"]
        status = load_status(agent_dir) if agent_dir.exists() else None

        if status and status.get("state") == "completed":
            ok, err = completion_ok(role, run_dir, agent_dir)
            if not ok:
                update_status(agent_dir, "failed", err)
                log_line(run_id, f"FAILED {role['id']}: {err}")
                raise SystemExit(err)
            continue

        if status and status.get("state") == "failed":
            log_line(run_id, f"HALT: {role['id']} failed: {status.get('error')}")
            raise SystemExit(f"Role failed: {role['id']}")

        if status and status.get("state") == "running":
            log_line(run_id, f"WAIT: {role['id']} still running")
            return

        # pending or missing: spawn next role
        agent_dir = spawn_role(role, run_dir)
        manifest["current_role"] = role["id"]
        manifest["last_spawned_at"] = dt.datetime.now(dt.UTC).isoformat()
        save_manifest(run_id, manifest)
        log_line(run_id, f"SPAWN: {role['id']} -> {agent_dir}")
        return

    log_line(run_id, "DONE: all roles completed")


def watchdog(run_id: str, minutes: int):
    run_dir = ORCH_RUNS / run_id
    if not run_dir.exists():
        raise SystemExit(f"Run not found: {run_dir}")

    threshold = minutes * 60
    now = dt.datetime.now(dt.UTC)
    roster = load_roster()
    roles = roster.get("roles", [])
    manifest = load_manifest(run_id)

    for role in roles:
        agent_dir = AGENTS / run_id / role["id"]
        status = load_status(agent_dir) if agent_dir.exists() else None
        if not status or status.get("state") != "running":
            continue
        started = status.get("started")
        if not started:
            update_status(agent_dir, "failed", "Missing started timestamp")
            log_line(run_id, f"FAILED {role['id']}: missing started timestamp")
            continue
        try:
            started_dt = dt.datetime.fromisoformat(started.replace("Z", "+00:00"))
        except Exception:
            update_status(agent_dir, "failed", "Invalid started timestamp")
            log_line(run_id, f"FAILED {role['id']}: invalid started timestamp")
            continue
        elapsed = (now - started_dt).total_seconds()
        if elapsed > threshold:
            update_status(agent_dir, "failed", f"Stale running > {minutes} minutes")
            log_line(run_id, f"FAILED {role['id']}: stale running ({elapsed:.0f}s)")




def run_gates(run_id: str):
    # run project gates for a given run id
    task_path = RUNS / run_id / "task.yaml"
    if not task_path.exists():
        raise SystemExit(f"Task not found: {task_path}")
    task = load_yaml(task_path)
    project_path = Path(task["path"])
    project_cfg = load_yaml(ROOT / "projects" / f"{task['project']}.yaml")
    for cmd in project_cfg.get("gates", {}).get("commands", []):
        subprocess.run(cmd, shell=True, check=True, cwd=project_path)



def pr_comment(run_id: str):
    task_path = RUNS / run_id / "task.yaml"
    if not task_path.exists():
        raise SystemExit(f"Task not found: {task_path}")
    task = load_yaml(task_path)

    run_dir = ORCH_RUNS / run_id
    checklist_path = run_dir / "CHECKLIST.md"
    final_path = run_dir / "FINAL.md"
    if not checklist_path.exists() or not final_path.exists():
        raise SystemExit("Missing CHECKLIST.md or FINAL.md")

    checklist = checklist_path.read_text().strip()
    final_text = final_path.read_text().strip()

    repo = task["repo"]
    branch = f"run/{run_id}"
    pr_info = subprocess.run(
        [
            "gh", "pr", "list",
            "--repo", repo,
            "--head", branch,
            "--json", "number,url",
            "--jq", ".[0]",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if not pr_info or pr_info == "null":
        raise SystemExit(f"No PR found for head {branch}")

    pr = json.loads(pr_info)
    body = (
        f"## Pipeline Run {run_id}\n\n"
        f"**Objective:** {task['goal']}\n\n"
        f"### Checklist\n\n{checklist}\n\n"
        f"### Final Summary\n\n{final_text}\n"
    )

    subprocess.run(
        ["gh", "pr", "comment", str(pr["number"]), "--repo", repo, "--body", body],
        check=True,
    )
    log_line(run_id, f"PR COMMENTED: {pr['url']}")


def main():
    p = argparse.ArgumentParser(description="Deterministic pipeline runner")
    sp = p.add_subparsers(dest="cmd", required=True)

    c = sp.add_parser("task-create")
    c.add_argument("project")
    c.add_argument("--goal", required=True)
    c.add_argument("--accept", action="append", default=[])

    r = sp.add_parser("run")
    r.add_argument("--task", required=True)

    a = sp.add_parser("approve")
    a.add_argument("--run-id", required=True)

    o = sp.add_parser("orchestrate")
    o.add_argument("--run-id", required=True)

    w = sp.add_parser("watchdog")
    w.add_argument("--run-id", required=True)
    w.add_argument("--minutes", type=int, default=60)

    pc = sp.add_parser("pr-comment")
    pc.add_argument("--run-id", required=True)

    g = sp.add_parser("gates")
    g.add_argument("--run-id", required=True)

    args = p.parse_args()

    if args.cmd == "task-create":
        task_create(Path(args.project), args.goal, args.accept)
        return

    if args.cmd == "approve":
        run_id = args.run_id
        run_dir = ROOT / "orchestration" / "runs" / run_id
        checklist = run_dir / "CHECKLIST.md"
        if not checklist.exists():
            raise SystemExit(f"Checklist not found for {run_id}")

        # auto-check when required outputs exist
        required = [
            "01-architecture.md",
            "02-implementation.md",
            "03-data-notes.md",
            "04-qa-report.md",
            "05-release-notes.md",
            "FINAL.md",
        ]
        roster = ROOT / "roster" / "roles.yaml"
        if roster.exists():
            try:
                data = yaml.safe_load(roster.read_text()) or {}
                required = data.get("approval", {}).get("required_outputs", required)
            except Exception:
                pass
        missing = [f for f in required if not (run_dir / f).exists()]
        if missing:
            raise SystemExit(f"Missing required outputs: {', '.join(missing)}")

        text = checklist.read_text()
        text = text.replace("- [ ]", "- [x]")
        checklist.write_text(text)
        print(f"Approved {run_id} (checklist completed).")
        return

    if args.cmd == "run":
        task = load_yaml(Path(args.task))
        run_id = task["id"]
        project_path = Path(task["path"])
        project_cfg = load_yaml(ROOT / "projects" / f"{task['project']}.yaml")

        # deterministic gates
        for cmd in project_cfg.get("gates", {}).get("commands", []):
            subprocess.run(cmd, shell=True, check=True, cwd=project_path)

        # check orchestration approval (CHECKLIST all checked)
        checklist = ROOT / "orchestration" / "runs" / run_id / "CHECKLIST.md"
        approved = False
        if checklist.exists():
            text = checklist.read_text()
            approved = "- [ ]" not in text

        # git diff
        diff = subprocess.run(["git", "status", "--porcelain"], cwd=project_path, capture_output=True, text=True, check=True).stdout.strip()

        if not diff:
            print(f"No changes for {run_id}. Nothing to commit.")
            return

        branch = f"run/{run_id}"
        subprocess.run(["git", "checkout", "-b", branch], cwd=project_path, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_path, check=True)
        subprocess.run(["git", "commit", "-m", f"{task['goal']}"], cwd=project_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=project_path, check=True)

        if project_cfg.get("autopr", False) and approved:
            # Build deterministic PR body from FINAL + CHECKLIST
            run_dir = ORCH_RUNS / run_id
            checklist_path = run_dir / "CHECKLIST.md"
            final_path = run_dir / "FINAL.md"
            body = f"Run: {run_id}\n\nAuto-generated by pipeline-core."
            if checklist_path.exists() and final_path.exists():
                checklist = checklist_path.read_text().strip()
                final_text = final_path.read_text().strip()
                body = (
                    f"## Pipeline Run {run_id}\n\n"
                    f"**Objective:** {task['goal']}\n\n"
                    f"### Checklist\n\n{checklist}\n\n"
                    f"### Final Summary\n\n{final_text}\n"
                )

            subprocess.run([
                "gh", "pr", "create",
                "--repo", project_cfg["repo"],
                "--title", task["goal"],
                "--body", body
            ], cwd=project_path, check=True)
            print(f"PR opened for {run_id}.")
        else:
            print(f"Branch pushed for {run_id}. PR not opened (approved={approved}).")
        return

    if args.cmd == "orchestrate":
        orchestrate(args.run_id)
        return

    if args.cmd == "watchdog":
        watchdog(args.run_id, args.minutes)
        return

    if args.cmd == "pr-comment":
        pr_comment(args.run_id)
        return

    if args.cmd == "gates":
        run_gates(args.run_id)
        return


if __name__ == "__main__":
    main()
