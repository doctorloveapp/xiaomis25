"""Compass graphics with observed sensor bindings, not time-hand substitutes."""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import hashlib
import json
from PIL import Image


def create_compass_catalog(root: Path, library: dict):
    models=[];groups=defaultdict(list)
    for hand in library['hands']:
        if hand['source']!='systemSensorCompass':continue
        raw=(root/hand['assetPath']).read_bytes()
        with Image.open(BytesIO(raw)) as im:
            size=im.size
        if tuple(hand['pivot'])!=(size[0]//2,size[1]//2):
            raise ValueError('Grafica bussola con perno non centrale: '+hand['resource'])
        if hand['name']=='Bouldering':kind='Rosa cardinali' if hand['resource']=='Pointer1' else 'Ghiera graduata'
        elif hand['name']=='Ferrari':kind='Ago nord' if size==(20,28) else 'Rosa cardinali e tacche'
        elif hand['name']=='Gear jungle':kind='Rosa dei venti'
        else:kind='Ago bussola'
        digest=hashlib.sha256(raw).hexdigest();asset=root/'data/compass-presets'/f'{digest[:24]}.png'
        asset.parent.mkdir(parents=True,exist_ok=True);asset.write_bytes(raw)
        model={k:hand[k] for k in ('id','name','author','face','theme','source','resource','sourceSha256','path','imageSize','pivot')}
        model.update(label=f"{hand['name']} · {kind} · {hand['theme']}",kind=kind,
                     assetPath=asset.relative_to(root).as_posix(),angleStart=0,angleRange=-360,valueStart=0,valueRange=360,
                     bindingCode=library['sources']['systemSensorCompass']['code'])
        model['label']+=' · '+hand['id'][:4]
        models.append(model);groups[(hand['face'],hand['setId'])].append(model)
    # Some real dials have separate cardinal lettering and tick-ring bitmaps.
    # Also offer those complete compositions, preserving the shared centre.
    for members in groups.values():
        if len(members)<2 or members[0]['name'] not in ('Bouldering','Ferrari'):continue
        size=max(max(m['imageSize']) for m in members)
        size+=size%2
        im=Image.new('RGBA',(size,size))
        for member in members:
            with Image.open(root/member['assetPath']) as raw:
                im.alpha_composite(raw.convert('RGBA'),(size//2-member['pivot'][0],size//2-member['pivot'][1]))
        out=BytesIO();im.save(out,'PNG');raw=out.getvalue();digest=hashlib.sha256(raw).hexdigest()
        asset=root/'data/compass-presets'/f'{digest[:24]}.png';asset.write_bytes(raw)
        models.append({**members[0],'id':digest[:24],'label':members[0]['name']+' · Rosa completa',
                       'kind':'Rosa completa','assetPath':asset.relative_to(root).as_posix(),'sourceSha256':digest,
                       'imageSize':[size,size],'pivot':[size//2,size//2],
                       'components':[m['id'] for m in members]})
    unique={m['sourceSha256']:m for m in models}
    models=list(unique.values())
    library['compasses']=models
    (root/'data/watchface-library.json').write_text(json.dumps(library,ensure_ascii=False,indent=2),encoding='utf8')
    report={'graphics':len(models),'originalGraphics':sum('components' not in m for m in models),
            'completeCompositions':sum('components' in m for m in models),'binding':'systemSensorCompass',
            'angleRange':-360,'models':models,'hardwareTested':False}
    (root/'docs/library-analysis/compasses-0.9.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report


def preset_changes(project, root, preset):
    path=(root/preset['assetPath']).resolve()
    if not path.is_relative_to((root/'data/compass-presets').resolve()):raise ValueError('Percorso bussola non valido.')
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if digest!=preset['sourceSha256']:raise ValueError('Grafica bussola alterata.')
    key='assets/'+digest[:24]+'.png';project.assets[key]=raw
    return {'asset':key,'compass_preset':preset['id'],'source':'systemSensorCompass',
            'value_start':0,'value_range':360,'angle_start':0,'angle_range':-360,
            'show_shadows':False,'pointer_end_pivot':False}
