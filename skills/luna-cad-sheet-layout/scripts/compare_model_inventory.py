"""Compare readable model-space fields from two inspect_cad JSON inventories.

This is a partial semantic check, not a full DWG comparator. Proxy/inaccessible
fields remain explicitly outside coverage. Layout changes are excluded.
"""
import argparse
import json
import math
from pathlib import Path

def equal(a,b):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        return math.isclose(a,b,rel_tol=0,abs_tol=1e-6)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    return a==b

def compare(before,after):
    def model(data):
        if data.get('status')!='read_complete':raise ValueError('Inventory did not complete')
        rows=[x for x in data['layouts'] if x['model']]
        if len(rows)!=1:raise ValueError('Expected one model space')
        entities=rows[0]['entities'];result={x['Handle']:x for x in entities}
        if len(result)!=len(entities):raise ValueError('Duplicate model handles')
        return result
    b,a=model(before),model(after);changes=[];limitations=[]
    for h in sorted(b.keys() & a.keys()):
        fields=set(b[h])|set(a[h]);fields.discard('read_errors')
        for field in sorted(fields):
            if not equal(b[h].get(field),a[h].get(field)):
                changes.append({'handle':h,'field':field,'before':b[h].get(field),'after':a[h].get(field)})
        if b[h].get('read_errors') or a[h].get('read_errors') or 'Zombie' in b[h].get('ObjectName',''):
            limitations.append({'handle':h,'type':b[h].get('ObjectName'),'before_errors':b[h].get('read_errors',{}),'after_errors':a[h].get('read_errors',{})})
    removed=sorted(b.keys()-a.keys());added=sorted(a.keys()-b.keys())
    return {'before_file':before.get('file'),'after_file':after.get('file'),'original_count':len(b),'final_count':len(a),'removed_handles':removed,'added_entities':[a[h] for h in added],'changed_original_fields':changes,'original_readable_fields_unchanged':not removed and not changes,'limitations':limitations,'coverage':'Only fields exported by inspect_cad; excludes unexported dimension/hatch/block internals and proxy geometry. Added entities require separate authorization/visual check.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--before',required=True);ap.add_argument('--after',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    paths=[Path(args.before),Path(args.after),Path(args.out)]
    if not all(p.is_absolute() for p in paths) or paths[2].exists():ap.error('Use absolute paths and a new output file')
    report=compare(*(json.loads(p.read_text(encoding='utf-8-sig')) for p in paths[:2]))
    paths[2].parent.mkdir(parents=True,exist_ok=True);paths[2].write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'original_readable_fields_unchanged':report['original_readable_fields_unchanged'],'added':len(report['added_entities']),'removed':len(report['removed_handles']),'changed_fields':len(report['changed_original_fields']),'limitations':len(report['limitations']),'out':str(paths[2])},ensure_ascii=False))
    return 0 if report['original_readable_fields_unchanged'] else 2

if __name__=='__main__':raise SystemExit(main())
