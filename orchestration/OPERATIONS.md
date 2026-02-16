# Operations Runbook

## Run packet creation
```bash
python3 orchestration/run_packet.py \
  --objective "<objective>" \
  --criterion "<criterion 1>" \
  --criterion "<criterion 2>" \
  --scope "<scope>"
```

## Execution order
1) architect
2) builder + data
3) qa
4) docs

Use `python3 scripts/pipeline.py orchestrate --run-id <run-id>` to spawn one role at a time.
Run `python3 scripts/pipeline.py watchdog --run-id <run-id> --minutes <N>` to fail stale running roles.

## Gates (deterministic)
- fast tests
- full tests
- build/health check (if applicable)

Use repo-specific scripts to implement gates.
