# Validation-only aligned data dictionary MVP

This public branch ships only the aligned validation lane.

- Canonical template: `templates/Strukturvorlage Datenkataloge_Abgeglichen_v2__empty.xlsx`
- Validator entrypoint: `scripts/schemaforge/run_github_validation.py`
- GitHub Actions validates the canonical empty template.
- Authored workbook validation comes next.
- Export/publish support is intentionally not part of this public MVP branch.
