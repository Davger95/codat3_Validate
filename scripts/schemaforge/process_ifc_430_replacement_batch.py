from __future__ import annotations

import json
from pathlib import Path

FILELIST = Path('/home/Dave/.openclaw/workspace-datadict/SchemaForge_output/ifc_430_replacement_filelist.txt')
PROGRESS = Path('/home/Dave/.openclaw/workspace-datadict/SchemaForge_output/ifc_430_replacement_progress.json')
OLD = '/ifc/4.3.0/'
NEW = '/ifc/4.3/'
BATCH_SIZE = 25


def main():
    files = [line for line in FILELIST.read_text().splitlines() if line.strip()]
    progress = json.loads(PROGRESS.read_text())
    start = int(progress.get('processed_files', 0))
    batch_no = int(progress.get('current_batch_number', 0)) + 1
    batch = files[start:start + BATCH_SIZE]

    changed_files = int(progress.get('changed_files', 0))
    total_replacements = int(progress.get('total_replacements', 0))
    failed_files = list(progress.get('failed_files', []))
    replacements_this_batch = 0
    processed_this_batch = 0

    for fp in batch:
        p = Path(fp)
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
            count = text.count(OLD)
            if count:
                replaced = text.replace(OLD, NEW)
                if replaced != text:
                    p.write_text(replaced, encoding='utf-8')
                    changed_files += 1
                    total_replacements += count
                    replacements_this_batch += count
            processed_this_batch += 1
        except Exception as e:
            failed_files.append({'file': fp, 'error': str(e), 'batch': batch_no})
            processed_this_batch += 1

    processed_total = start + processed_this_batch
    progress = {
        'total_files': len(files),
        'processed_files': processed_total,
        'remaining_files': max(0, len(files) - processed_total),
        'current_batch_number': batch_no,
        'failed_files': failed_files,
        'changed_files': changed_files,
        'total_replacements': total_replacements,
        'last_batch': {
            'batch_number': batch_no,
            'batch_size': len(batch),
            'processed_in_batch': processed_this_batch,
            'replacements_in_batch': replacements_this_batch,
            'start_index': start,
            'end_index_exclusive': processed_total,
        }
    }
    PROGRESS.write_text(json.dumps(progress, indent=2))
    print(json.dumps(progress['last_batch'], indent=2))
    print(json.dumps({
        'processed_total': progress['processed_files'],
        'remaining_files': progress['remaining_files'],
        'failed_files_count': len(progress['failed_files'])
    }, indent=2))


if __name__ == '__main__':
    main()
