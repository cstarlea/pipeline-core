# Agent Workspaces

Each role gets a workspace under `agents/<run-id>/<role-id>/`.

Structure:
- `inbox/` instructions and inputs
- `outbox/` summaries
- `workspace/` scratch
- `status.json` state tracking

Agents are expected to write their primary deliverable directly into the run packet output file referenced in `inbox/instructions.md`.
