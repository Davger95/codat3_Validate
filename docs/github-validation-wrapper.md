# GitHub validation wrapper — baseline MVP

## Canonical command

```bash
python3 scripts/schemaforge/run_github_validation.py \
  --workspace /home/Dave/.openclaw/workspace-datadict \
  --workbook-path templates/Strukturvorlage\ Datenkataloge_Abgeglichen_v2__empty.xlsx
```

## Baseline expectation

For the current baseline MVP, the canonical empty aligned template should validate with:

- `parser_valid: true`
- `pipeline_valid: true`
- `governance_valid: true`
- `errors: 0`
- `warnings: 0`

## Scope note

This baseline verifies the aligned template/validator lane only.

Authored workbook validation and export/publish verification are not claimed in this baseline unless separately tested and documented.
