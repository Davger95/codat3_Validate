# GitHub Actions wrapper for Data Dictionary validation

This folder contains a portable GitHub Actions setup for validating Excel-based data dictionaries.

## Main workflow
- `.github/workflows/validate-data-dictionary.yml`

## Expected companion scripts
- `scripts/schemaforge/validate_strukturvorlage.py`
- `scripts/schemaforge/run_github_validation.py`

## Outputs
The workflow writes and uploads:
- `SchemaForge_output/github_validation_report.json`
- `SchemaForge_output/github_validation_report.md`
- `SchemaForge_output/github_validation_summary.json`

## Behavior
- auto-detects the newest active workbook if no workbook path is provided
- generates both machine-readable and layman-readable reports
- fails the job only when blocking validation errors exist
