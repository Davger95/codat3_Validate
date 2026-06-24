from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def discover_workbook(workspace: Path) -> Path:
    candidates = []
    preferred_patterns = [
        'templates/*_test.xlsx',
        'templates/*authoring-guidance*.xlsx',
        'HE_SEM_shemaforge/*_test.xlsx',
        'HE_SEM_shemaforge/*authoring-guidance*.xlsx',
        'HE_SEM_shemaforge/Strukturvorlage*.xlsx',
        'HE_SEM_shemaforge/*.xlsx',
        'templates/*.xlsx',
        '*.xlsx',
    ]
    seen = set()
    for pattern in preferred_patterns:
        matches = []
        for p in workspace.glob(pattern):
            normalized = str(p).replace('\\', '/')
            if not p.is_file():
                continue
            if '/archive/' in f'/{normalized}' or normalized.startswith('archive/'):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            matches.append(p)
        if matches:
            candidates = matches
            break
    if not candidates:
        searched = ', '.join(preferred_patterns)
        raise FileNotFoundError(f'No workbook candidate found for validation. Searched patterns: {searched}')
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description='GitHub Actions wrapper for Data Dictionary validation.')
    parser.add_argument('--workspace', default='.', help='Repository/workspace root')
    parser.add_argument('--workbook-path', default='', help='Optional relative or absolute workbook path')
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    workbook = Path(args.workbook_path).resolve() if args.workbook_path else discover_workbook(workspace)
    if not workbook.exists():
        raise FileNotFoundError(f'Workbook not found: {workbook}')

    schemaforge_dir = workspace / 'scripts' / 'schemaforge'
    if str(schemaforge_dir) not in sys.path:
        sys.path.insert(0, str(schemaforge_dir))

    import validate_strukturvorlage as validator_module

    out_dir = workspace / 'SchemaForge_output'
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / 'github_validation_report.json'
    md_out = out_dir / 'github_validation_report.md'
    summary_out = out_dir / 'github_validation_summary.json'

    validator = validator_module.Validator(workbook)
    report = validator.validate()
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    md_out.write_text(validator_module.render_markdown_report(report))
    summary_out.write_text(json.dumps({
        'workbook': str(workbook),
        **report['summary'],
    }, indent=2, ensure_ascii=False))

    print(json.dumps({
        'workbook': str(workbook),
        'json_report': str(json_out),
        'md_report': str(md_out),
        'summary': report['summary'],
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
