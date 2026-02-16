#!/usr/bin/env python3
from __future__ import annotations
import argparse
import datetime as dt
from pathlib import Path

ROLES = {
    "architect": {"responsibilities": "Define architecture changes, contracts, non-goals.", "output": "01-architecture.md"},
    "builder": {"responsibilities": "Implement approved scope (code/config).", "output": "02-implementation.md"},
    "data": {"responsibilities": "Schema/seed/migrations if needed.", "output": "03-data-notes.md"},
    "qa": {"responsibilities": "Add/execute tests and report evidence.", "output": "04-qa-report.md"},
    "docs": {"responsibilities": "Update README/runbook/release notes.", "output": "05-release-notes.md"},
}


def render(template: str, values: dict[str, str]) -> str:
    out = template
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def create_run(base: Path, objective: str, criteria: list[str], scope: str, run_id: str | None):
    now = dt.datetime.now(dt.UTC)
    run_id = run_id or now.strftime("run-%Y%m%d-%H%M%S")
    run_dir = base / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    template = (base / "templates" / "brief.md.tmpl").read_text()
    ac_text = "\n".join([f"- {c}" for c in criteria]) if criteria else "- (none provided)"

    (run_dir / "RUN.md").write_text(
        "# Run\n\n"
        f"- ID: {run_id}\n"
        f"- Created (UTC): {now.isoformat()}\n"
        f"- Objective: {objective}\n\n"
        "## Acceptance criteria\n"
        f"{ac_text}\n\n"
        "## Scope\n"
        f"{scope}\n"
    )

    for role, meta in ROLES.items():
        content = render(template, {
            "role": role,
            "run_id": run_id,
            "objective": objective,
            "acceptance_criteria": ac_text,
            "scope": scope,
            "responsibilities": meta["responsibilities"],
            "output_file": meta["output"],
        })
        (run_dir / f"brief-{role}.md").write_text(content)
        (run_dir / meta["output"]).write_text(f"# {role} output\n\nPending.\n")

    (run_dir / "CHECKLIST.md").write_text(
        "# Integration Checklist\n\n"
        "- [ ] Architecture output complete\n"
        "- [ ] Implementation complete\n"
        "- [ ] Data compatibility confirmed\n"
        "- [ ] Tests added/executed\n"
        "- [ ] Docs updated\n"
        "- [ ] Gates passed\n"
        "- [ ] FINAL.md written\n"
    )

    (run_dir / "FINAL.md").write_text(
        "# Final Summary\n\n"
        "## Changes\n- TBD\n\n"
        "## Deferred\n- TBD\n\n"
        "## Blockers\n- None\n"
    )

    print(run_dir)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Create a deterministic run packet")
    p.add_argument("--objective", required=True)
    p.add_argument("--criterion", action="append", default=[])
    p.add_argument("--scope", default="Project scope")
    p.add_argument("--run-id")
    p.add_argument("--base", default=str(Path(__file__).resolve().parent))
    args = p.parse_args()

    create_run(Path(args.base), args.objective, args.criterion, args.scope, args.run_id)
