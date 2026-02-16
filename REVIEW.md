# Pipeline-Core Review & Improvement Plan

Date: 2026-02-16

## What went wrong (root causes)
1) **No enforced sequential handoff**
   - Orchestrator cron spawned multiple roles in parallel and set them to `running` without gating.
   - Roles were not required to update status/outputs before next role started.

2) **Missing agent completion contracts**
   - Some agents never wrote outputs or `status.json`, leaving runs stuck.
   - No watchdog to detect stale `running` state.

3) **Inconsistent orchestration mechanism**
   - `scripts/orchestrate.py` only prepared workspaces (no spawn), while cron tried to spawn roles without clear guardrails.

4) **QA gates ran too late**
   - CI failures (Node 18 + webidl/resizable crash; audit threshold) only discovered after PR open.

5) **PR comment missing**
   - No deterministic summary/comment generated from FINAL + CHECKLIST.

## Design principles (kept)
- Deterministic-first (scripts/cron over LLMs) [memory/semantic/ops-principles.md]
- File-based handoffs (inbox/outbox/status)
- Sequential role order (architect → implement → qa → docs)
- PR only when checklist complete

## Required safeguards (before next run)
### A) Orchestrator (sequential)
- **Single role at a time**: spawn next role only when previous role is `completed`.
- **No parallel runs** for the same run-id unless explicitly allowed.
- **Stale-running timeout**: if a role is `running` for >N minutes, mark `failed` and pause.

### B) Agent completion contract
- Each role must produce:
  - output file in run packet
  - `outbox/summary.md`
  - `status.json` = completed
- If not met, orchestrator halts and logs failure.

### C) Deterministic QA gates before PR
- `astro check`
- `npm run build`
- `npm audit --audit-level=high`
- **Fail gate → stop PR**

### D) PR comment (deterministic)
- On PR open, add comment:
  - Objective
  - Scope
  - Checklist status
  - Tests run
  - Links to FINAL + outputs

### E) Run lifecycle
- `create` → `orchestrate` → `gates` → `approve` → `pr` → `archive`
- Archive only after PR created or failure recorded.

## Implementation plan (ordered)
1) **Replace cron orchestrator** with a deterministic CLI `pipeline orchestrate --run-id`:
   - Reads roster order
   - Spawns *one* role at a time
   - Enforces status completion
   - Writes `orchestration/logs/<run-id>.log`

2) **Add watchdog**:
   - `pipeline watchdog --run-id` detects stale running > X minutes and marks failed

3) **Add deterministic PR commenter**:
   - `pipeline pr-comment --run-id` uses FINAL.md + CHECKLIST

4) **Wire CI gates** in `pipeline run` **before** commit/PR

5) **Add run manifest** (`runs/<id>/manifest.json`)
   - Track current role, start times, gates status

6) **Re-enable cron** only after steps 1–5 are complete

## Open decisions
- Timeout threshold for stale roles
- Whether QA gates should run locally or via CI only

## Next step (recommended)
Implement steps 1–3, then do a dry run on a small task.
