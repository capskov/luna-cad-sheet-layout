"""List DWG frame candidates and date clues; never choose a revision or change CAD."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def date_clues(name):
    result = []
    for match in re.finditer(r'(?<!\d)(20\d{2})[-_.年]?(\d{2})[-_.月]?(\d{2})(?:日)?(?!\d)', name):
        try:
            value = date(*(int(x) for x in match.groups())).isoformat()
        except ValueError:
            continue
        if value not in result:
            result.append(value)
    return result


def candidates(root, recursive=False, with_hash=False):
    root = Path(root)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError('Use an existing absolute candidate directory.')
    result = []
    for path in sorted(root.rglob('*') if recursive else root.iterdir()):
        if not path.is_file() or path.suffix.lower() != '.dwg':
            continue
        stat = path.stat()
        row = {'path': str(path.resolve()), 'filename_dates': date_clues(path.stem),
               'modified_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
               'bytes': stat.st_size}
        if with_hash:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            row['sha256'] = digest.hexdigest()
        result.append(row)
    return {'status': 'candidates_only', 'selected': None, 'candidates': result,
            'note': 'Filename dates and modification times are clues, not proof of the authoritative revision.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--recursive', action='store_true')
    parser.add_argument('--hash', action='store_true', dest='with_hash')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if not output.is_absolute() or output.exists():
        parser.error('Use a new absolute output path.')
    report = candidates(args.root, args.recursive, args.with_hash)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'count': len(report['candidates']), 'selected': None, 'out': str(output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
