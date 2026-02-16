# Pipeline Core (Deterministic-First)

This repo hosts a deterministic, script-driven pipeline for project work. LLMs are used only when needed for content or ambiguous interpretation.

## Principles
- Deterministic-first: scripts + explicit inputs/outputs.
- Task contracts are required (goal, scope, acceptance criteria).
- Artifacts are stored per run under `runs/<run-id>/`.
- LLM usage is opt-in per task type.

## Structure
- `projects/` — project configs
- `tasks/` — task contract templates
- `scripts/` — pipeline runner
- `orchestration/` — run packets, briefs, checklists
- `roster/` — role definitions + approval rules
- `runs/` — run artifacts (gitignored)
- `agents/` — per-run agent workspaces (inbox/outbox/status)

## Quick start
```bash
pip install pyyaml

python3 scripts/pipeline.py task-create projects/starleaf.online.static.yaml \
  --goal "<goal>" \
  --accept "<criterion 1>" --accept "<criterion 2>"

python3 scripts/pipeline.py run --task runs/<run-id>/task.yaml

# sequential orchestration (one role at a time)
python3 scripts/pipeline.py orchestrate --run-id <run-id>

# watchdog for stale running roles
python3 scripts/pipeline.py watchdog --run-id <run-id> --minutes 60

# post deterministic PR comment from FINAL.md + CHECKLIST
python3 scripts/pipeline.py pr-comment --run-id <run-id>
```

Notes:
- Orchestrator writes to `orchestration/logs/<run-id>.log`.
- Roles communicate only via `agents/<run-id>/<role>/{inbox,outbox,status.json}`.
- Final summary is authored by the `final-summarizer` role (no manual edits).
