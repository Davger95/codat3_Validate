# Baseline MVP — aligned validation lane

This repository currently ships one canonical aligned MVP validation path.

## Canonical template

- `templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx`

## Canonical validator entrypoint

- `scripts/schemaforge/run_github_validation.py`

## Current baseline scope

The current baseline MVP verifies:

- canonical workbook structure
- required aligned tabs
- aligned header/row assumptions
- dropdown/guidance-ready template wiring
- validator/parser/governance pipeline stability for the canonical empty template
- GitHub Actions triggerability for the canonical empty template

The current baseline MVP does **not** yet claim verified authored-content validation or verified export/publish support for i14y, bSDD, or LINDAS. Those will be tested next once an authored workbook with 1–2 real rows is added.

## Validation usage

Run locally:

```bash
python3 scripts/schemaforge/run_github_validation.py \
  --workspace /home/Dave/.openclaw/workspace-datadict \
  --workbook-path templates/Strukturvorlage\ Datenkataloge_Abgeglichen_v2__empty.xlsx
```

Outputs:

- `SchemaForge_output/github_validation_report.json`
- `SchemaForge_output/github_validation_report.md`
- `SchemaForge_output/github_validation_summary.json`

## Template filling note

The canonical empty template is the current baseline artifact. Authored-data validation will be exercised next with a separate workbook containing 1–2 real test rows.

## GitHub Actions

Default CI validates the canonical empty aligned template via:

- `.github/workflows/validate-data-dictionary.yml`
- `scripts/schemaforge/run_github_validation.py`
