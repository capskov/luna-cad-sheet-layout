"""Read existing COM state only. No open/close/activate/SendCommand/save."""
import argparse
import json
from pathlib import Path
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dwg', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--progid', required=True, choices=['AutoCAD.Application.24.1', 'AutoCAD.Application.25.1'])
    args = ap.parse_args()
    target, output = Path(args.dwg), Path(args.out)
    if not target.is_absolute() or not output.is_absolute() or output.exists():
        ap.error('Use absolute paths and a new output path.')
    result = {'target': str(target), 'progid': args.progid, 'mode': 'non-mutating-inventory', 'errors': []}
    try:
        from cad_session import Session, get, call, retry
        s = Session(target, output.parent, allow_read_only=True, progid=args.progid)

        def read(obj, name, row):
            try:
                row[name] = get(obj, name)
            except Exception as exc:
                row.setdefault('read_errors', {})[name] = str(exc)

        result.update({'file': get(s.doc, 'FullName'), 'read_only': s.read_only,
                       'DBMOD': s.var('DBMOD'), 'active_layout': get(get(s.doc, 'ActiveLayout'), 'Name')})
        layouts = get(s.doc, 'Layouts')
        result['layouts'] = []
        for i in range(get(layouts, 'Count')):
            lay = call(layouts, 'Item', i)
            record = {'name': get(lay, 'Name'), 'model': get(lay, 'ModelType'), 'entities': []}
            block = get(lay, 'Block')
            for j in range(get(block, 'Count')):
                e = call(block, 'Item', j)
                row = {k: get(e, k) for k in ('Handle', 'ObjectName', 'Layer')}
                typ = row['ObjectName']
                props = []
                if typ in ('AcDbText', 'AcDbMText'):
                    props = ['TextString', 'InsertionPoint', 'Height', 'StyleName', 'Rotation']
                elif typ == 'AcDbViewport':
                    props = ['Center', 'Width', 'Height', 'CustomScale', 'DisplayLocked', 'ViewportOn']
                    row['identity'] = 'unverified: select this layout and query DXF69 before writes'
                elif typ == 'AcDbBlockReference':
                    props = ['Name', 'InsertionPoint', 'Rotation', 'XScaleFactor', 'YScaleFactor']
                    definition = call(get(s.doc, 'Blocks'), 'Item', get(e, 'Name'))
                    if get(definition, 'IsXRef'):
                        props.append('Path')
                        row['is_xref'] = True
                    try:
                        row['attributes'] = [{'tag': get(a, 'TagString'), 'text': get(a, 'TextString')}
                                             for a in e.GetAttributes()]
                    except Exception as exc:
                        row.setdefault('read_errors', {})['attributes'] = str(exc)
                elif 'Polyline' in typ:
                    props = ['Coordinates', 'Closed']
                elif typ == 'AcDbLine':
                    props = ['StartPoint', 'EndPoint']
                elif typ in ('AcDbCircle', 'AcDbArc'):
                    props = ['Center', 'Radius']
                    if typ == 'AcDbArc':
                        props += ['StartAngle', 'EndAngle']
                for name in props:
                    read(e, name, row)
                if typ != 'AcDbViewport':
                    try:
                        row['bbox'] = retry(lambda: e.GetBoundingBox(), 'inventory:GetBoundingBox')
                    except Exception as exc:
                        row.setdefault('read_errors', {})['bbox'] = str(exc)
                record['entities'].append(row)
            result['layouts'].append(record)
        result['status'] = 'read_complete'
        result['coverage'] = 'Not a full DWG semantic diff; proxy geometry/block internals need targeted inspection.'
    except Exception as exc:
        result['status'] = 'blocked'
        result['errors'].append({'type': type(exc).__name__, 'message': str(exc)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({'status': result['status'], 'output': str(output), 'errors': result['errors']}, ensure_ascii=False))
    return 0 if result['status'] == 'read_complete' else 2


if __name__ == '__main__':
    sys.exit(main())
