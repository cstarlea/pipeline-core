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

## Gates (deterministic)
- fast tests
- full tests
- build/health check (if applicable)

Use repo-specific scripts to implement gates.
