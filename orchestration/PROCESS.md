# Pipeline Orchestration Process (Deterministic-First)

## Goal
- Parallelize work without chaos
- Keep artifacts reviewable
- Enforce quality gates before merge
- Prefer deterministic scripts; use LLMs only when required

## Roles and required outputs
1. **architect** → `01-architecture.md`
2. **builder** → `02-implementation.md`
3. **data** → `03-data-notes.md`
4. **qa** → `04-qa-report.md`
5. **docs** → `05-release-notes.md`

## Standard pipeline
1) Define objective + acceptance criteria
2) Create run packet (RUN.md + briefs)
3) Execute roles in order (architect → builder/data → qa → docs)
4) Run deterministic gates (tests/build/health)
5) Write FINAL.md summary

## Definition of Done
- All role outputs exist
- CHECKLIST.md complete
- FINAL.md includes changes, deferred, blockers
