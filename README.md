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

## Quick start
```bash
pip install pyyaml

python3 scripts/pipeline.py task-create projects/starleaf.online.static.yaml \
  --goal "<goal>" \
  --accept "<criterion 1>" --accept "<criterion 2>"

python3 scripts/pipeline.py run --task runs/<run-id>/task.yaml
```
