"""Extract real mother graphics, matched shadows and sets from the local corpus.

Follow layout/slot/widget references, including AOD and segmented rotations.
Dark graphics are shadows only when a corresponding coloured graphic exists
in the same source/position/container. Standalone dark needles remain models.
"""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import hashlib,json,math,re,struct
from PIL import Image
from .watchface_library import resource_path,read_tables

ROLES={'timeHour':'hour','timeMinute':'minute','timeSecond':'second'}

def extract_hand_models(root,catalog):
    models=[];audit=[];errors=[];image_cache={}
    def image_info(base,node):
        path=resource_path(base,node['src']);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest not in image_cache:
            with Image.open(BytesIO(raw)) as original:
                im=original.convert('RGBA');bounds=im.getchannel('A').getbbox()
                # Ignore transparent RGB padding when distinguishing black shadows.
                bright=max((max(r,g,b) for r,g,b,a in im.getdata() if a>=24),default=0)
                image_cache[digest]={'raw':raw,'size':list(im.size),'bounds':bounds,'dark':bright<=32}
        return {'path':path.relative_to(root).as_posix(),'sha256':digest,**image_cache[digest]}
    def export(info):
        target=root/'data/hand-presets'/f"{info['sha256'][:24]}.png"
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(info['raw'])
        return {'assetPath':target.relative_to(root).as_posix(),'sourceSha256':info['sha256'],
                'path':info['path'],'imageSize':info['size']}
    for face in catalog['watchfaces']:
        base=root/face['base'];binary=base/'resource.bin'
        if not binary.is_file():continue
        nodes={n['name']:n for n in face['resources'] if n.get('name')}
        data=binary.read_bytes();native=defaultdict(list)
        for screen in range(data[28]):
            for uid,_,payload in read_tables(data,screen)[7]:
                if len(payload)>=32 and payload[3]>>4==3:native[uid].append(payload)
        mapping={name:int(uid,16) for name,uid in re.findall(r'^([^:\r\n]+):\s*([a-fA-F0-9]+)\s*$',(base/'uidmap.map').read_text(encoding='utf8'),re.M)}
        reachable=set();families=[]
        themes=face['themes'] or [{'attributes':{'type':'normal','name':'Risorse'},'layouts':[]}]
        for ti,theme in enumerate(themes):
            occurrences=[]
            def walk(ref,x,y,context,stack=()):
                name=ref.lstrip('@');n=nodes.get(name)
                if n is None or name in stack:return
                if n['tag']=='DataItemPointer':
                    try:
                        image=nodes[n['ref'].lstrip('@')]
                        if image['tag']!='Image':raise ValueError('Un puntatore non riferisce una bitmap singola.')
                        info=image_info(base,image)
                        if not info['bounds']:return
                        xml=[float(n.get('pivotX',0)),float(n.get('pivotY',0))]
                        # Some vendor uidmaps reuse a UID for unrelated sources.
                        # Accept binary evidence only when it agrees with the
                        # XML pivot and the actual image dimensions.
                        candidates=[b for b in native.get(mapping.get(name),[]) if
                                    all(0<=v<480 and abs(v-w)<=1 for v,w,s in
                                        zip(struct.unpack_from('<HH',b,20),xml,info['size']))]
                        payload=min(candidates,key=lambda b:sum(abs(v-w) for v,w in zip(struct.unpack_from('<HH',b,20),xml))) if candidates else None
                        pivot=list(struct.unpack_from('<HH',payload,20)) if payload else [int(v) for v in xml]
                        # Arc markers can legitimately rotate about a point
                        # outside their bitmap (e.g. LLATH's 23x19 indicators).
                        if not all(0<=p<480 for p in pivot):raise ValueError('Perno fuori dal canvas supportato.')
                        occurrences.append({'node':n,'info':info,'pivot':pivot,'x':x,'y':y,'context':context,
                                            'centre':(x+pivot[0],y+pivot[1]),'nativePivot':payload is not None})
                        reachable.add(name)
                    except Exception as exc:errors.append({'face':face['folder'],'resource':name,'error':str(exc)})
                    return
                if n['tag'] in ('Slot','Widget','Group'):
                    for child in n.get('items',[]):
                        if child.get('ref'):
                            walk(child['ref'],x+float(child.get('x',0)),y+float(child.get('y',0)),context+'/'+name,stack+(name,))
            for layout in theme['layouts']:walk(layout.get('ref',''),float(layout.get('x',0)),float(layout.get('y',0)),'root')
            # Include exported pointer resources not referenced by any theme.
            if ti==len(themes)-1:
                for name,n in nodes.items():
                    if n['tag']=='DataItemPointer' and name not in reachable:walk('@'+name,0,0,'unplaced/'+name)
            clusters=[]
            for o in occurrences:
                source=o['node'].get('source','')
                cluster=next((g for g in clusters if g[0]['context']==o['context'] and g[0]['node'].get('source')==source and math.dist(g[0]['centre'],o['centre'])<=24),None)
                if cluster is None:clusters.append([o])
                else:cluster.append(o)
            for cluster in clusters:
                coloured=[o for o in cluster if not o['info']['dark']]
                shadows=[o for o in cluster if o['info']['dark']] if coloured else []
                mothers=coloured or cluster
                # Match roles at the same dial centre/container to form a set.
                centre=mothers[0]['centre'];context=mothers[0]['context']
                family=next((f for f in families if f['themeIndex']==ti and f['context']==context and math.dist(f['centre'],centre)<=24),None)
                if family is None:
                    family={'themeIndex':ti,'context':context,'centre':centre,'members':defaultdict(list)};families.append(family)
                role=ROLES.get(mothers[0]['node'].get('source'),'indicator');seen=set()
                for o in mothers:
                    key=(o['info']['sha256'],tuple(o['pivot']))
                    if key in seen:continue
                    seen.add(key)
                    source=o['node'].get('source','')
                    # Small source indicators and peripheral clock subdials.
                    small=role=='indicator' or max(o['info']['bounds'][2]-o['info']['bounds'][0],o['info']['bounds'][3]-o['info']['bounds'][1])<120 or math.dist(o['centre'],(240,240))>70
                    shadow=min(shadows,key=lambda s:math.dist(s['centre'],o['centre'])) if shadows else None
                    matched={**export(shadow['info']),'pivot':shadow['pivot'],
                             'offset':[round(shadow['centre'][i]-o['centre'][i]) for i in (0,1)],'resource':shadow['node']['name']} if shadow else None
                    identity=json.dumps([face['folder'],ti,context,role,key,source,matched and matched['sourceSha256']],sort_keys=True)
                    item={'id':hashlib.sha256(identity.encode()).hexdigest()[:24],
                          'name':face['description'].get('name',face['folder']),'author':face['description'].get('author',''),
                          'face':face['folder'],'theme':theme['attributes'].get('name',''),
                          'aod':theme['attributes'].get('type')=='AOD','hand':role,'small':small,
                          'source':source,'resource':o['node']['name'],'pivot':o['pivot'],'shadow':matched,
                          'variant':len(family['members'][role])+1,'nativePivot':o['nativePivot'],
                          'externalPivot':any(v>=s for v,s in zip(o['pivot'],o['info']['size'])),**export(o['info'])}
                    family['members'][role].append(item);models.append(item)
                audit.append({'face':face['folder'],'theme':theme['attributes'].get('name'),
                              'aod':theme['attributes'].get('type')=='AOD','source':mothers[0]['node'].get('source'),
                              'resources':[o['node']['name'] for o in cluster],
                              'motherResources':[o['node']['name'] for o in mothers],
                              'shadowResources':[o['node']['name'] for o in shadows],
                              'segmentedRotations':any(float(o['node'].get('angleRange',0)) not in (360,720) for o in mothers)})
        for index,family in enumerate(families):
            set_id=f"{face['folder']}-{family['themeIndex']}-{index}"
            members=family['members']
            for role,entries in members.items():
                for i,item in enumerate(entries):
                    item['setId']=set_id
                    item['setMembers']={h:choices[min(i,len(choices)-1)]['id'] for h,choices in members.items() if h in ('hour','minute','second')}
    # A shared bitmap may occur in many slot choices; retain actual distinct sets.
    dedup=[];seen={};aliases={};by_id={m['id']:m for m in models}
    for m in models:
        def graphic(item):
            shadow=item['shadow']
            return [item['sourceSha256'],item['pivot'],
                    [shadow['sourceSha256'],shadow['pivot'],shadow['offset']] if shadow else None]
        partners=[(h,graphic(by_id[i])) for h,i in sorted(m['setMembers'].items())]
        signature=json.dumps([m['hand'],graphic(m),m['small'],partners],sort_keys=True)
        if signature in seen:
            aliases[m['id']]=seen[signature]['id'];seen[signature].setdefault('alsoFrom',[]).append({'face':m['face'],'theme':m['theme'],'resource':m['resource']})
        else:seen[signature]=m;dedup.append(m)
    for m in dedup:m['setMembers']={h:aliases.get(i,i) for h,i in m['setMembers'].items()}
    report={'status':'passed' if not errors else 'errors','watchfaces':len(catalog['watchfaces']),
            'pointerNodes':sum(f['resourceTags'].get('DataItemPointer',0) for f in catalog['watchfaces']),
            'models':len(dedup),'smallModels':sum(m['small'] for m in dedup),
            'modelsWithShadows':sum(bool(m['shadow']) for m in dedup),'roles':{h:sum(m['hand']==h for m in dedup) for h in ('hour','minute','second','indicator')},
            'coverage':audit,'errors':errors}
    report_path=root/'docs/library-analysis/hands-0.8.json';report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return dedup,report
