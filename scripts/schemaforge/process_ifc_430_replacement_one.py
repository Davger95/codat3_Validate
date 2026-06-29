from __future__ import annotations
import json
from pathlib import Path
FILELIST = Path('/home/Dave/.openclaw/workspace-datadict/SchemaForge_output/ifc_430_replacement_filelist.txt')
PROGRESS = Path('/home/Dave/.openclaw/workspace-datadict/SchemaForge_output/ifc_430_replacement_progress.json')
OLD = '/ifc/4.3.0/'
NEW = '/ifc/4.3/'

def main():
    files = [line for line in FILELIST.read_text().splitlines() if line.strip()]
    progress = json.loads(PROGRESS.read_text())
    start = int(progress.get('processed_files', 0))
    if start >= len(files):
        print('NO_WORK', {'total': len(files)})
        return
    fp = files[start]
    p = Path(fp)
    replacements = 0
    failed = progress.get('failed_files', [])
    changed_files = int(progress.get('changed_files', 0))
    total_replacements = int(progress.get('total_replacements', 0))
    try:
        text = p.read_text(encoding='utf-8', errors='ignore')
        count = text.count(OLD)
        if count:
            newtext = text.replace(OLD, NEW)
            if newtext != text:
                p.write_text(newtext, encoding='utf-8')
                changed_files += 1
                total_replacements += count
                replacements = count
    except Exception as e:
        failed.append({'file': fp, 'error': str(e)})
    processed_total = start + 1
    progress.update({
        'processed_files': processed_total,
        'remaining_files': max(0, len(files) - processed_total),
        'current_batch_number': int(progress.get('current_batch_number', 0)) + 1,
        'failed_files': failed,
        'changed_files': changed_files,
        'total_replacements': total_replacements,
        'last_file': fp,
        'last_replacements': replacements,
    })
    PROGRESS.write_text(json.dumps(progress, indent=2))
    print(json.dumps({
        'file': fp,
        'replacements_in_file': replacements,
        'processed_total': processed_total,
        'remaining_files': progress['remaining_files'],
        'failed_files_count': len(failed)
    }, indent=2))

if __name__ == '__main__':
    main()
