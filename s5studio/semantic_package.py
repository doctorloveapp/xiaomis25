"""Template preservation plus regenerated metadata, with semantic validation."""
from io import BytesIO
from pathlib import Path
import hashlib,json,re,struct,xml.etree.ElementTree as ET,zipfile
from PIL import Image
from .native import inspect_binary
from .watchface_library import read_tables,directory_bases
from .model import SOURCES,archive_members
from .native_graph import uid_name

EDITABLE={'resource.bin','description.xml','resources/manifest.xml','editor.config.json','uidmap.map'}

def validate_semantics(z):
    data=z.read('resource.bin');info=inspect_binary(data)
    manifest=ET.fromstring(z.read('resources/manifest.xml'));themes=manifest.findall('Theme')
    if manifest.get('id')!=info['faceId'] or manifest.get('width')!='480' or manifest.get('height')!='480':
        raise ValueError('Identità/geometria del manifest diverse dal binario.')
    if len(themes)!=info['screenCount']:raise ValueError('Manifest: numero temi diverso dal binario.')
    nodes={n.get('name'):n for n in manifest.find('Resources')}
    uidmap={name:int(uid,16) for name,uid in re.findall(r'^([^:\r\n]+):\s*([a-fA-F0-9]+)\s*$',z.read('uidmap.map').decode('utf8'),re.M)}
    editor=json.loads(z.read('editor.config.json'));ethemes=editor.get('themes',[])
    if len(ethemes)!=len(themes):raise ValueError('Editor: numero temi diverso dal binario.')
    for si,(screen,theme,etheme) in enumerate(zip(info['screens'],themes,ethemes)):
        expected_type='AOD' if screen['aod'] else 'normal'
        if screen['title']!=theme.get('name') or screen['title']!=etheme.get('name') or theme.get('type')!=expected_type or etheme.get('type')!=expected_type:
            raise ValueError('Nomi/tipi dei temi incoerenti tra binario, manifest ed editor: '+str(si))
        table=read_tables(data,si);resources={uid:(index,b) for index,rows in enumerate(table) if index for uid,_,b in rows}
        preview_name=theme.get('preview','').lstrip('@');preview_uid=uidmap.get(preview_name)
        if preview_uid not in resources or resources[preview_uid][0]!=2:raise ValueError('Anteprima tema senza risorsa nativa.')
        preview_src=nodes[preview_name].get('src')
        if etheme.get('preview')!=preview_src:raise ValueError('Anteprima editor diversa dal manifest.')
        animation=etheme.get('previewAni')
        if animation and (screen['aod'] or 'preview/'+animation not in z.namelist()):
            raise ValueError('Anteprima animata editor inesistente o attribuita ad AOD.')
        if not screen['aod']:
            pos=struct.unpack_from('<I',data,directory_bases(data)[si]+4)[0]
            blob=resources[preview_uid][1]
            if data[pos:pos+len(blob)]!=blob:raise ValueError('Anteprima del selettore firmware diversa dalla risorsa del tema.')
        editor_slots=[c for c in etheme['children'] if c.get('type')=='Slot']
        if len(editor_slots)!=len(table[8]):raise ValueError('Numero slot editor diverso dal binario.')
        editor_slots_by_id={c['id']:c for c in editor_slots}
        for slot_uid,_,_ in table[8]:
            eslot=editor_slots_by_id.get(uid_name(slot_uid))
            if eslot is None:raise ValueError('Identità dello slot editor diversa dal binario.')
            slot_node=nodes[uid_name(slot_uid)]
            choices=[n.get('ref')[1:] for n in slot_node]
            if eslot['attrs'].get('followingGroupName')!=slot_node.get('SlotGroupName') or eslot['attrs'].get('widgetIdToDisplay')!=choices[0] or [c['id'] for c in eslot['children']]!=choices:raise ValueError('Scelte/identità dello slot editor incoerenti.')
            for egroup in eslot['children']:
                group_node=nodes[egroup['id']];expected=nodes[group_node.get('preview')[1:]].get('src')
                if egroup['attrs']['resources']['widgetPreview']['studio']!=[expected]:raise ValueError('Anteprima opzione editor incoerente.')
        layouts=theme.findall('Layout')
        if len(layouts)!=len(table[0]):raise ValueError('Layout del manifest incoerenti con il binario.')
        for node,(_,_,payload) in zip(layouts,table[0]):
            uid,x,y,_,_=struct.unpack('<IhhII',payload)
            if uidmap.get(node.get('ref','').lstrip('@'))!=uid or (int(node.get('x')),int(node.get('y')))!=(x,y):raise ValueError('Posizione/riferimento del layout incoerente.')
        for uid,(index,b) in resources.items():
            name=uid_name(uid)
            if uidmap.get(name)!=uid or name not in nodes:raise ValueError('Risorsa senza corrispondenza XML/uidmap: '+hex(uid))
            node=nodes[name]
            if index==7:
                source=node.get('source');target=struct.unpack_from('<I',b,8)[0]
                if source not in SOURCES or SOURCES[source][1]!=b[:2].hex().upper() or uidmap.get(node.get('ref','').lstrip('@'))!=target:raise ValueError('Sorgente/riferimento dati incoerente: '+name)
                if node.tag=='DataItemImageNumber' and (int(node.get('totalDigits'))!=(b[2]&15) or int(node.get('decimalDigits'))!=(b[2]>>4) or int(node.get('parameter'))!=struct.unpack_from('<H',b,6)[0]):raise ValueError('Formato/parametro numerico diverso dal binario.')
                if node.tag=='DataItemImageValues':
                    values=[int(n.get('value')) for n in node]
                    if len(b)!=16+4*len(values) or list(struct.unpack_from('<'+'i'*len(values),b,16))!=values:raise ValueError('Mappa valori/icone diversa dal binario.')
                if node.tag=='DataItemPointer':
                    period=struct.unpack_from('<H',b,6)[0]
                    if node.get('pointerFps') is not None and (int(node.get('parameter'))!=period or int(node.get('pointerFps'))!=1000//period):
                        raise ValueError('Frequenza lancetta diversa dal binario.')
                    if tuple(int(node.get(k)) for k in ('pivotX','pivotY'))!=struct.unpack_from('<HH',b,20):raise ValueError('Pivot lancetta diverso dal binario.')
                    if tuple(round(float(node.get(k))*10) for k in ('angleStart','angleRange'))!=struct.unpack_from('<hh',b,24):raise ValueError('Rotazione lancetta diversa dal binario.')
                    for attr,pos in (('valueStart',12),('valueRange',16)):
                        if node.get(attr) is not None and int(node.get(attr))!=struct.unpack_from('<I',b,pos)[0]>>8:raise ValueError('Intervallo lancetta diverso dal binario.')
            if index==8:
                count=struct.unpack_from('<H',b)[0];choices=list(struct.unpack_from('<'+'I'*count,b,4))
                if [uidmap.get(n.get('ref','').lstrip('@')) for n in node]!=choices:raise ValueError('Opzioni dello slot diverse dal binario.')
                pos=4+4*count;length=struct.unpack_from('<I',b,pos)[0]
                if b[pos+4:pos+4+length].rstrip(b'\0').decode('utf8')!=node.get('SlotGroupName'):raise ValueError('Identità del gruppo slot incoerente.')
            if index==9:
                count=struct.unpack_from('<H',b,40)[0];children=[struct.unpack_from('<hhII',b,44+12*n) for n in range(count)]
                if [(int(n.get('x')),int(n.get('y')),uidmap.get(n.get('ref','').lstrip('@')),0) for n in node]!=children:raise ValueError('Grafica del gruppo modificabile diversa dal binario.')
                for attr,pos in (('widgetName',4),('preview',36),('editBox',44+12*count)):
                    if uidmap.get(node.get(attr,'').lstrip('@'))!=struct.unpack_from('<I',b,pos)[0]:raise ValueError('Anteprima/etichetta gruppo incoerente.')
            if index in (2,3):
                paths=[node.get('src')] if index==2 else [n.get('src') for n in node]
                for path in paths:
                    with Image.open(BytesIO(z.read('resources/'+path))) as image:
                        image.load()
                        if image.size!=struct.unpack_from('<HH',b,4):raise ValueError('Dimensioni bitmap/metadati diverse dal binario.')
            if index==5:
                from .lua_runtime import unpack_app
                app_name,content=unpack_app(b)
                if node.tag!='App' or node.get('src')!='app/'+app_name or z.read('app/'+app_name)!=content:
                    raise ValueError('Script/risorsa Lua diversi dal binario.')
    schema=json.loads(z.read('s5studio-schema.json'))
    for path,digest in {**schema['resourceFiles'],**schema['metadataHashes'],**schema['previewFiles']}.items():
        if hashlib.sha256(z.read(path)).hexdigest()!=digest:raise ValueError('Risorsa/anteprima modificata dopo la compilazione: '+path)
    if 'build-report.json' in z.namelist():
        from .model import Project,Element
        from .lua_runtime import interaction_report
        d=schema['project'];project=Project(elements=[Element.from_dict(e) for e in d['elements']],variants=d['variants'])
        expected=interaction_report(project,data,z.read('resources/manifest.xml'))
        report=json.loads(z.read('build-report.json'))
        from .motion import native_motion_report
        if report.get('binarySha256')!=info['sha256'] or report.get('interactive')!=expected or report.get('secondsMotion')!=native_motion_report(data):
            raise ValueError('Rapporto interattività diverso dal contenuto del pacchetto.')
    elif manifest.get('interactive')=='true':raise ValueError('Rapporto build interattiva mancante.')
    return info

def validate_package(template,output,expected=None):
    from .template_package import local_records,entry_metadata,preview_member
    with zipfile.ZipFile(template) as base,zipfile.ZipFile(output) as actual:
        old=archive_members(base);new=archive_members(actual)
        if set(old)-set(new):raise ValueError('File del template eliminati.')
        additions=set(new)-set(old)
        if any(n not in ('s5studio-schema.json','build-report.json') and not n.startswith(('resources/studio/','app/lua/')) for n in additions):raise ValueError('Aggiunta estranea al packaging Studio.')
        original_records=local_records(base,Path(template).read_bytes());new_records=local_records(actual,Path(output).read_bytes())
        preserved=0
        for name,item in old.items():
            if entry_metadata(item)!=entry_metadata(new[name]):raise ValueError('Attributi ZIP del template alterati: '+name)
            if name in EDITABLE or preview_member(name):continue
            if original_records[name]!=new_records[name]:raise ValueError('Record protetto del template alterato: '+name)
            if not item.is_dir():preserved+=1
        if expected:
            for name,data in expected.items():
                if actual.read(name)!=data:raise ValueError('Sostituzione non corrispondente: '+name)
        if actual.read('capability.json')!=base.read('capability.json'):raise ValueError('Capability alterate.')
        binary=validate_semantics(actual)
        description=ET.fromstring(actual.read('description.xml'))
        schema=json.loads(actual.read('s5studio-schema.json'))
        if description.findtext('pkgName')!=binary['faceId'] or schema['project']['faceId']!=binary['faceId'] or description.findtext('name')!=schema['project']['name']:raise ValueError('Identità descrizione incoerente.')
        signature=hashlib.sha256(json.dumps({'template':hashlib.sha256(Path(template).read_bytes()).hexdigest(),'protected':sorted(set(old)-EDITABLE-{n for n in old if preview_member(n)})},sort_keys=True).encode()).hexdigest()
        return {'status':'passed','scope':'CRC, record protetti del template, geometrie, UID, sorgenti, temi, gruppi selezionabili e hash anteprime/risorse del progetto.',
                'packaging':'template-surgery-with-generated-metadata','templateSha256':hashlib.sha256(Path(template).read_bytes()).hexdigest(),
                'outputSha256':hashlib.sha256(Path(output).read_bytes()).hexdigest(),'structuralFingerprint':signature,'preservedFiles':preserved,'entries':len(new),
                'mutableMembers':sorted(EDITABLE|{n for n in old if preview_member(n)}),'addedFiles':len(additions),'binary':binary,'hardwareVerified':False,
                'warnings':['Capability e hashCode opachi conservati: firma Xiaomi e accettazione capabilities non attestate.','Funzionamento delle nuove selezioni da provare sul S5.']}

def package(template,data,preview,output,aod_preview,variant_previews,project,generated):
    from .template_package import template_profile,preview_member,is_aod_preview,_encode_preview,_surgery_bytes
    output=Path(output)
    if output.exists() or Path(template).resolve()==output.resolve():raise ValueError('Scegli un output nuovo.')
    profile=template_profile(template);replacements={'resource.bin':data,**generated}
    with zipfile.ZipFile(template) as z:
        description=ET.fromstring(z.read('description.xml'))
        for key,value in (('name',project.name),('author',project.author or 'S5 Studio'),('version',project.version),('pkgName',project.face_id)):
            description.find(key).text=value
        ET.indent(description);replacements['description.xml']=ET.tostring(description,encoding='utf-8',xml_declaration=True)
        old_names=set(z.namelist())
    if aod_preview is None:
        from .render import png_bytes
        aod_preview=png_bytes(Image.new('RGB',(480,480),'black'))
    for entry in profile['signature']['entries']:
        name=entry['name']
        if not preview_member(name):continue
        source=aod_preview if is_aod_preview(name) else preview
        match=re.search(r'(?:style[_-]?|Theme|样式)([1-5])',name,re.I)
        if match and not is_aod_preview(name):source=variant_previews[min(int(match[1])-1,len(variant_previews)-1)]
        replacements[name]=_encode_preview(source,entry)
    schema=json.loads(replacements['s5studio-schema.json'])
    schema['previewFiles']={n:hashlib.sha256(b).hexdigest() for n,b in replacements.items() if preview_member(n)}
    replacements['s5studio-schema.json']=json.dumps(schema,ensure_ascii=False,indent=2).encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.checking')
    if temporary.exists():raise ValueError('File temporaneo di export già presente.')
    try:
        temporary.write_bytes(_surgery_bytes(template,{n:b for n,b in replacements.items() if n in old_names}))
        with zipfile.ZipFile(temporary,'a',zipfile.ZIP_DEFLATED) as z:
            for name,b in replacements.items():
                if name not in old_names:z.writestr(name,b)
        report=validate_package(template,temporary,replacements)
        temporary.replace(output)
        return {**report,'output':str(output)}
    finally:temporary.unlink(missing_ok=True)
