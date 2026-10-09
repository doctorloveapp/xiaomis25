"""Collect new/edited local hand sets before every software release."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from .hand_sets import HandSetCatalog,ROLES


def sync_hand_sets(root,sources=None):
    root=Path(root).resolve();destination=root/'resources/hand-sets'
    library_path=root/'data/watchface-library.json'
    hands=json.loads(library_path.read_text(encoding='utf8'))['hands'] if library_path.exists() else []
    target=HandSetCatalog(destination,library_hands=hands,resources=root)
    records={s['id']:s for s in target.personal_sets()}
    if sources is None:
        sources=[root/'data/hand-sets']
        if os.environ.get('LOCALAPPDATA'):sources.append(Path(os.environ['LOCALAPPDATA'])/'S5Studio/hand-sets')
    checked=[];updates=[];pending_assets={}
    for folder in sources:
        source=HandSetCatalog(folder,library_hands=hands,resources=root)
        if not source.path.exists():
            checked.append({'catalog':str(source.path),'status':'absent'});continue
        imported=source.personal_sets()
        checked.append({'catalog':str(source.path),'status':'checked','sets':len(imported)})
        for original in imported:
            record=deepcopy(original);identity=record['id'];name=record['name']
            if not (identity.startswith('custom-') or identity in target.builtin_by_id):raise ValueError('ID set non riconosciuto: '+identity)
            if not isinstance(name,str) or not 1<=len(name)<=80 or any(ord(c)<32 for c in name):raise ValueError('Nome del set non valido.')
            if type(record['small']) is not bool or not record['hands'] or set(record['hands'])-set(ROLES):raise ValueError('Ruoli del set non validi.')
            if not record['small'] and set(record['hands'])!=set(ROLES) and identity not in target.builtin_by_id:raise ValueError('Set principale incompleto: '+name)
            for mother in record['hands'].values():
                for item in [mother]+([mother['shadow']] if mother.get('shadow') else []):
                    source.validate_item(item)
                    pending_assets[item['assetPath']]=source.bitmap_path(item).read_bytes()
            if records.get(identity)!=record:updates.append({'id':identity,'name':name,'action':'updated' if identity in records else 'added'})
            records[identity]=record
    # Validate retained defaults too. Never silently omit a set with missing PNGs.
    for record in records.values():
        for mother in record['hands'].values():
            for item in [mother]+([mother['shadow']] if mother.get('shadow') else []):
                if item['assetPath'] not in pending_assets:target.validate_item(item)
    for relative,raw in pending_assets.items():
        path=destination/relative
        if not path.exists() or path.read_bytes()!=raw:target._atomic_write(path,raw)
    payload={'schemaVersion':1,'sets':sorted(records.values(),key=lambda s:(s['name'].casefold(),s['id']))}
    raw=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    if not target.path.exists() or target.path.read_bytes()!=raw:target._atomic_write(target.path,raw)
    presets=target.presets()
    assets={i['assetPath'] for r in payload['sets'] for m in r['hands'].values() for i in [m]+([m['shadow']] if m.get('shadow') else [])}
    return {'status':'passed','sourcesChecked':checked,'updates':updates,'bundledSets':len(records),
            'bundledHands':sum(len(s['hands']) for s in records.values()),'bundledAssets':len(assets),
            'sets':[{'id':s['id'],'name':s['name'],'small':s['small']} for s in payload['sets']],
            'catalogSha256':hashlib.sha256(raw).hexdigest(),'originalCatalogHands':len(hands),
            'effectiveCatalogHands':len(presets),'sourceCatalogsModified':False}
