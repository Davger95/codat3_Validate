# GitHub validation wrapper

## Canonical command

```bash
python3 scripts/schemaforge/run_github_validation.py \
  --workspace /home/Dave/.openclaw/workspace-datadict \
  --workbook-path "templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx"
```

Expected result for the baseline MVP:

- `parser_valid: true`
- `pipeline_valid: true`
- `governance_valid: true`
- `errors: 0`
- `warnings: 0`
- `normalizations: 0`

This public MVP branch covers the aligned empty-template validation lane only.
