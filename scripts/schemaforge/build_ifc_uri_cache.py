from __future__ import annotations

import json
import re
import time
from pathlib import Path

SOURCE_TTL = Path('/home/Dave/.openclaw/shared/ontologies/bsdd/ifc4.3-bsdd-harvested-official-api.ttl.tmp')
CACHE_JSON = Path('/home/Dave/.openclaw/shared/ontologies/bsdd/ifc4.3-uri-cache.json')
URI_RE = re.compile(r'https://identifier\.buildingsmart\.org/uri/buildingsmart/ifc/4\.3(?:\.0)?/[^\s<>"]+')


def build_cache(source: Path = SOURCE_TTL, target: Path = CACHE_JSON) -> dict:
    start = time.time()
    uris = set()
    with source.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            for m in URI_RE.findall(line):
                # normalize obsolete '/ifc/4.3.0/' → '/ifc/4.3/' in extracted URIs only
                norm = m.replace('/ifc/4.3.0/','/ifc/4.3/')
                uris.add(norm)
    payload = {
        'source': str(source),
        'uri_count': len(uris),
        'uris': sorted(uris),
        'generated_at_epoch': time.time(),
        'elapsed_seconds': round(time.time() - start, 3),
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


if __name__ == '__main__':
    payload = build_cache()
    print(json.dumps({
        'source': payload['source'],
        'cache': str(CACHE_JSON),
        'uri_count': payload['uri_count'],
        'elapsed_seconds': payload['elapsed_seconds'],
        'cache_size_bytes': CACHE_JSON.stat().st_size,
    }, indent=2))
