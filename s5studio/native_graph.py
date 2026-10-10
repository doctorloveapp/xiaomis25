"""Build an editable native resource graph and matching editable metadata.

All compressed images/numeric widgets are produced by the pinned compiler.
Only the bounded, observed directory/group/slot containers are written here.
"""
from copy import deepcopy
from pathlib import Path
import hashlib,json,struct,xml.etree.ElementTree as ET
from .model import Element,SOURCES,normalized_slot
from .watchface_library import read_tables
from .complications import option_project,option_image,label,ALIASES

LANGUAGES=['en_US','zh_CN','zh_TW','ja_JP','es_ES','fr_FR','de_DE','ru_RU','pt_BR','pt_PT','it_IT','ko_KR','tr_TR','nl_NL','th_TH','sv_SE','da_DK','vi_VN','nb_NO','pl_PL','fi_FI','in_ID','el_GR','ro_RO','cs_CZ','uk_UA','hu_HU','sk_SK','zh_HK','iw_IL','ar_EG','lt_LT','bg_BG']

def translated(text):
    b=text.encode('utf-8')
    return struct.pack('<II',0xffffffff,1)+struct.pack('<'+'I'*33,*([len(b)]*33))+b*33

def uid_name(uid):return f'Studio_{uid:08x}'

def collect_nodes(data,screen,fprj):
    """Associate compiler layouts with the FPRJ assets, checking every binding."""
    tables=read_tables(data,screen);available={uid:(index,payload) for index,rows in enumerate(tables) if index for uid,_,payload in rows}
    layouts=list(tables[0]);nodes={};cursor=0
    folder=Path(fprj).parent/'images'
    def image(uid,filename):
        raw=(folder/filename).read_bytes()
        nodes[uid]={'tag':'Image','attrs':{},'bitmap':raw}
    from .lua_runtime import unpack_app
    for uid,_,payload in tables[5]:
        name,content=unpack_app(payload)
        nodes[uid]={'tag':'App','attrs':{'src':'app/'+name},'app':content}
    for w in ET.parse(fprj).getroot().find('Screen').findall('Widget'):
        shape=w.get('Shape');hands=[h for h,attr in (('Hour','HourHand_ImageName'),('Minute','MinuteHand_Image'),('Second','SecondHand_Image')) if w.get(attr)]
        count=len(hands) if shape=='27' else 1
        if cursor+count>len(layouts):raise ValueError('Layout del compilatore non corrispondenti ai componenti FPRJ.')
        for sub in range(count):
            _,_,layout=layouts[cursor];cursor+=1;uid=struct.unpack_from('<I',layout)[0]
            index,payload=available[uid]
            if shape=='30':image(uid,w.get('Bitmap'))
            elif shape=='34':
                from urllib.parse import unquote
                if index!=5 or nodes[uid]['attrs']['src']!='app/'+unquote(w.get('Name')[4:]):
                    raise ValueError('Entry point Lua diverso dal layout compilato.')
            elif shape in ('32','31'):
                target=struct.unpack_from('<I',payload,8)[0]
                items=w.get('BitmapList').split('|')
                bitmaps=[(folder/n.split(':')[-1]).read_bytes() for n in items]
                nodes[target]={'tag':'ImageArray','attrs':{},'bitmaps':bitmaps}
                code=payload[:2].hex().upper()
                if code!=w.get('Value_Src',w.get('Index_Src','')).upper():raise ValueError('Binding sorgente cambiato dal compilatore: '+w.get('Name'))
                candidates=[key for key,value in SOURCES.items() if value[1]==code]
                source=ALIASES.get(candidates[0],candidates[0])
                attrs={'source':source,'ref':target,'rotation':'0','supportRecolor':'false'}
                if shape=='32':attrs.update(totalDigits=str(payload[2]&15),decimalDigits=str(payload[2]>>4),align={0:'right',1:'left',2:'center'}[payload[3]&3],space='0',unitIcon='',leadingZero=str(bool(payload[3]&4)).lower(),trailingZero='false',decimalOffsetX='0',parameter='1000',renderRule='alwaysShow')
                nodes[uid]={'tag':'DataItemImageNumber' if shape=='32' else 'DataItemImageValues','attrs':attrs}
                if shape=='31':nodes[uid]['values']=[int(n.split(':')[0].strip('()')) for n in items]
            elif shape=='27':
                hand=hands[sub];target=struct.unpack_from('<I',payload,8)[0]
                image(target,w.get({'Hour':'HourHand_ImageName','Minute':'MinuteHand_Image','Second':'SecondHand_Image'}[hand]))
                nodes[uid]={'tag':'DataItemPointer','attrs':{'source':{'Hour':'timeHour','Minute':'timeMinute','Second':'timeSecond'}[hand],
                           'ref':target,'pivotX':str(struct.unpack_from('<H',payload,20)[0]),'pivotY':str(struct.unpack_from('<H',payload,22)[0]),
                           'angleStart':'0','angleRange':'720' if hand=='Hour' else '360',
                           'parameter':str(struct.unpack_from('<H',payload,6)[0]),
                           'pointerFps':str(1000//struct.unpack_from('<H',payload,6)[0])}}
            else:raise ValueError('Tipo FPRJ senza metadati ricostruibili: '+str(shape))
    if cursor!=len(layouts):raise ValueError('Il compilatore ha aggiunto layout non previsti.')
    missing=set(available)-set(nodes)
    if missing:raise ValueError('Risorse compilate senza metadati: '+str([hex(v) for v in missing]))
    return nodes

class Allocator:
    def __init__(self):self.counts={6:1}
    def new(self,category):
        n=self.counts.get(category,0);self.counts[category]=n+1
        if n>=65535:raise ValueError('Troppi identificatori di risorsa nel progetto.')
        return category<<24|n
    def relocate(self,tables,nodes):
        mapping={uid:self.new(index) for index,rows in enumerate(tables) if index for uid,_,_ in rows}
        output=[[] for _ in range(12)]
        for index,rows in enumerate(tables):
            for uid,flags,payload in rows:
                b=bytearray(payload)
                if index in (0,7):
                    pos=0 if index==0 else 8;old=struct.unpack_from('<I',b,pos)[0]
                    struct.pack_into('<I',b,pos,mapping[old])
                if index==7 and b[3]>>4==1:
                    # Observed S5 numeric descriptors use parameter 1000.
                    # EasyFace leaves this field zero for target 562.
                    struct.pack_into('<H',b,6,1000)
                output[index].append((self.new(0) if index==0 else mapping[uid],flags,bytes(b)))
        rewritten={}
        for uid,node in nodes.items():
            node=deepcopy(node)
            if type(node['attrs'].get('ref')) is int:node['attrs']['ref']=mapping[node['attrs']['ref']]
            rewritten[mapping[uid]]=node
        return output,rewritten

def preview_factory(project,work,run_compiler,progress):
    """Encode complete flattened scenes; EasyFace cannot execute Lua in previews."""
    from .native import generate_fprj
    from .model import Project
    from .render import render,png_bytes
    directory=work/'preview-source';paths=[]
    scenes=[(project.variant_project(i),False) for i in range(max(1,len(project.variants)))]
    if project.aod_enabled:scenes.append((project.variant_project(0),True))
    for index,(scene,aod) in enumerate(scenes):
        bitmap=png_bytes(render(scene,aod=aod,circular=False).convert('RGB'))
        asset='assets/full-preview.png'
        flat=Project(name=f'Anteprima completa {index+1}',elements=[Element(kind='image',name='Tutti i livelli',
                     asset=asset,x=0,y=0,width=480,height=480)],assets={asset:bitmap},variants=[],aod_enabled=False)
        paths.append(generate_fprj(flat,directory,filename=f'preview_{index:03}',variant_index=index).project_path)
    progress(f'Codifica anteprime complete: {len(scenes)} schermate?')
    data=run_compiler(paths[0],'previews.face')
    if data[28]!=len(scenes):raise ValueError('Numero schermate della fabbrica anteprime inatteso.')
    previews=[]
    for index in range(len(scenes)):
        tables=read_tables(data,index)
        if len(tables[0])!=2:raise ValueError('Anteprima completa deve avere sfondo e una sola immagine.')
        image_uid=struct.unpack_from('<I',tables[0][-1][2])[0]
        bitmap=next((b for uid,_,b in tables[2] if uid==image_uid),None)
        if bitmap is None or struct.unpack_from('<HH',bitmap,4)!=(480,480):
            raise ValueError('Bitmap nativa dell?anteprima completa mancante.')
        previews.append(bitmap)
    return previews[:len(scenes)-int(project.aod_enabled)],previews[-1] if project.aod_enabled else None


def factory(project,work,run_compiler,progress):
    """Compile option components in batches; reuse identical visual definitions."""
    from .native import generate_fprj
    from .render import png_bytes,SCENARIOS
    specs={};keys={}
    for vi in range(max(1,len(project.variants))):
        p=project.variant_project(vi)
        for si,slot in enumerate(p.complications):
            if not slot['visible']:continue
            for key in slot['options']:
                definition={k:v for k,v in normalized_slot(slot).items() if k not in ('id','name','x','y','options','default')}
                identity=hashlib.sha256(json.dumps([definition,key],sort_keys=True).encode()).hexdigest()
                specs.setdefault(identity,(slot,key));keys[vi,si,key]=identity
    result={};items=list(specs.items())
    for batch_start in range(0,len(items),32):
        progress(f'Compilazione grafica complicazioni {batch_start+1}–{min(batch_start+32,len(items))}/{len(items)}…')
        directory=work/f'options-{batch_start:04}';paths=[]
        chunk=items[batch_start:batch_start+32]
        for n,(identity,(slot,key)) in enumerate(chunk):
            s=normalized_slot(slot);p=option_project(s,key)
            # Encode selector thumbnails and edit bounds through EasyFace too.
            preview=option_image(s,key,SCENARIOS['Normale'])
            edit=preview.copy();from PIL import ImageDraw
            ImageDraw.Draw(edit).rounded_rectangle((1,1,s['width']-2,s['height']-2),radius=10,outline='#ffffff',width=2)
            for title,bitmap in (('Anteprima selettore',preview),('Bordo selezione',edit)):
                raw=png_bytes(bitmap);asset='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[asset]=raw
                p.elements.append(Element(kind='image',name=title,asset=asset,x=0,y=0,width=s['width'],height=s['height']))
            paths.append(generate_fprj(p,directory,filename=f'option_{n:03}',variant_index=n).project_path)
        data=run_compiler(paths[0],f'options_{batch_start}.face')
        if data[28]!=len(chunk):raise ValueError('Numero schermate della fabbrica risorse inatteso.')
        for n,(identity,(slot,key)) in enumerate(chunk):
            t=read_tables(data,n);nodes=collect_nodes(data,n,paths[n])
            preview_uid=struct.unpack_from('<I',t[0][-2][2])[0];edit_uid=struct.unpack_from('<I',t[0][-1][2])[0]
            # Remove automatic 480x480 background and editor-only images from
            # the runtime children; retain their encoded data for the selector.
            t[0]=t[0][1:-2]
            referenced={preview_uid,edit_uid}|{struct.unpack_from('<I',b)[0] for _,_,b in t[0]}
            for uid,_,b in t[7]:
                if uid in referenced:referenced.add(struct.unpack_from('<I',b,8)[0])
            for index in range(1,12):t[index]=[row for row in t[index] if row[0] in referenced]
            nodes={uid:node for uid,node in nodes.items() if uid in referenced}
            result[identity]=(t,nodes,preview_uid,edit_uid)
    return result,keys

def patch_pointers(normal,nodes,resolved,pointers,aod=False):
    from .motion import pointer_period
    for e in resolved.elements:
        if e.kind not in ('pointer','compass') or not e.visible or e.id not in pointers:continue
        for position in pointers[e.id]:
            uid=struct.unpack_from('<I',normal[0][position][2])[0]
            for row,(key,flags,payload) in enumerate(normal[7]):
                if key!=uid:continue
                b=bytearray(payload);b[:2]=bytes.fromhex(SOURCES[e.source][1])
                period=pointer_period(e,aod)
                struct.pack_into('<H',b,6,period)
                struct.pack_into('<II',b,12,e.value_start<<8,e.value_range<<8)
                struct.pack_into('<hh',b,24,e.angle_start*10,e.angle_range*10)
                normal[7][row]=(key,flags,bytes(b))
                nodes[uid]['attrs'].update(source=ALIASES.get(e.source,e.source),valueStart=str(e.value_start),valueRange=str(e.value_range),angleStart=str(e.angle_start),angleRange=str(e.angle_range),parameter=str(period),pointerFps=str(1000//period),renderRule='alwaysShow')

def compose(compiled,project,reference,source_dir,previews,options,option_keys,source_paths=None,aod_preview=None):
    from .native import inspect_binary
    alloc=Allocator();screens=[];all_nodes={};variants=project.variants or [{'name':'Originale'}]
    for vi,v in enumerate(variants):
        original_index=0 if vi==0 else vi+int(project.aod_enabled)
        path=source_paths[vi] if source_paths else source_dir/('quadrante.fprj' if vi==0 else f'variante_{vi+1:02}.fprj')
        normal,nodes=alloc.relocate(read_tables(compiled,original_index),collect_nodes(compiled,original_index,path))
        resolved=project.variant_project(vi)
        # Preserve the layer stack generated in the FPRJ. Every editable slot
        # has one placeholder layout, including slots above foreground images.
        placeholders={};pointers={};cursor=0
        for widget in ET.parse(path).getroot().find('Screen').findall('Widget'):
            if widget.get('Name','').startswith('slot_'):
                placeholders[widget.get('Name')[5:]]=cursor
            if widget.get('Name','').startswith('pointer_'):
                key=widget.get('Name').removeprefix('pointer_').removeprefix('shadow_')
                pointers.setdefault(key,[]).append(cursor)
            cursor+=sum(bool(widget.get(k)) for k in ('HourHand_ImageName','MinuteHand_Image','SecondHand_Image')) if widget.get('Shape')=='27' else 1
        patch_pointers(normal,nodes,resolved,pointers)
        removed=set()
        for si,slot in enumerate(resolved.complications):
            if not slot['visible']:continue
            choices=[]
            for key in [slot['default']]+[k for k in slot['options'] if k!=slot['default']]:
                original,onodes,preview_old,edit_old=options[option_keys[vi,si,key]]
                graft,gnodes=alloc.relocate(original,onodes)
                # The original->new map is also represented by the source nodes.
                lookup=dict(zip(onodes,gnodes));preview=lookup[preview_old];edit=lookup[edit_old]
                for index in range(1,12):normal[index].extend(graft[index])
                nodes.update(gnodes)
                caption=alloc.new(6);normal[6].append((caption,0,translated(label(key))))
                nodes[caption]={'tag':'Translation','attrs':{},'text':label(key)}
                uid=alloc.new(9);children=[]
                for _,_,b in graft[0]:
                    target,x,y,flags,_=struct.unpack('<IhhII',b)
                    children.append((x,y,target,flags))
                header=bytearray(44);struct.pack_into('<II',header,0,0xffffffff,caption)
                struct.pack_into('<IHH',header,36,preview,len(children),0x1004)
                payload=bytes(header)+b''.join(struct.pack('<hhII',*c) for c in children)+struct.pack('<IHH',edit,slot['height'],slot['width'])
                normal[9].append((uid,0,payload));choices.append(uid)
                nodes[uid]={'tag':'Widget','attrs':{'widgetName':caption,'groupType':'general','preview':preview,'editBox':edit,'w':str(slot['width']),'h':str(slot['height'])},'children':children,'key':key}
            group_name=f'{vi+1}_{si+1}' if v.get('independent') else str(si+1)
            uid=alloc.new(8);group=group_name.encode('utf-8');padded=group.ljust((len(group)+3)//4*4,b'\0')
            payload=struct.pack('<HH',len(choices),2)+struct.pack('<'+'I'*len(choices),*choices)+struct.pack('<I',len(padded))+padded
            normal[8].append((uid,0,payload));nodes[uid]={'tag':'Slot','attrs':{'type':'widget','SlotGroupName':group_name},'choices':choices,'slotId':slot['id'],'width':slot['width'],'height':slot['height']}
            if slot['id'] not in placeholders:raise ValueError('Livello della complicazione assente nei sorgenti FPRJ.')
            position=placeholders[slot['id']]
            old_layout=normal[0][position]
            removed.add(struct.unpack_from('<I',old_layout[2])[0])
            normal[0][position]=(old_layout[0],old_layout[1],struct.pack('<IhhII',uid,slot['x'],slot['y'],0,0))
        retained={struct.unpack_from('<I',b)[0] for _,_,b in normal[0]}
        for _,_,b in normal[7]:retained.add(struct.unpack_from('<I',b,8)[0])
        for uid in removed-retained:
            normal[2]=[row for row in normal[2] if row[0]!=uid];nodes.pop(uid,None)
        from .render import png_bytes,render
        preview_uid=alloc.new(2);normal[2].append((preview_uid,0,previews[vi]));nodes[preview_uid]={'tag':'Image','attrs':{},'bitmap':png_bytes(render(project.variant_project(vi),circular=False))}
        all_nodes.update(nodes);screens.append((normal,v['name'],False,vi,preview_uid))
        if project.aod_enabled:
            aod,anodes=alloc.relocate(read_tables(compiled,1),collect_nodes(compiled,1,next((source_dir/'AOD').glob('*.fprj'))))
            apath=next((source_dir/'AOD').glob('*.fprj'));apointers={};cursor=0
            for widget in ET.parse(apath).getroot().find('Screen').findall('Widget'):
                if widget.get('Name','').startswith('pointer_'):
                    key=widget.get('Name').removeprefix('pointer_').removeprefix('shadow_')
                    apointers.setdefault(key,[]).append(cursor)
                cursor+=sum(bool(widget.get(k)) for k in ('HourHand_ImageName','MinuteHand_Image','SecondHand_Image')) if widget.get('Shape')=='27' else 1
            patch_pointers(aod,anodes,resolved,apointers,aod=True)
            preview_uid=alloc.new(2)
            if aod_preview is None:raise ValueError('Anteprima AOD nativa mancante.')
            aod[2].append((preview_uid,0,aod_preview));anodes[preview_uid]={'tag':'Image','attrs':{},'bitmap':png_bytes(render(project.variant_project(0),aod=True,circular=False))}
            all_nodes.update(anodes);screens.append((aod,v['name'],True,vi,preview_uid))
    out=bytearray(reference[:168])+bytearray(176*len(screens));out[24]=out[29]=0;out[28]=len(screens)
    struct.pack_into('<I',out,16,0x903)
    out[30]=(reference[30]&~6)|(4 if project.aod_enabled else 0)|(2 if len(variants)>1 else 0)
    out[40:104]=compiled[40:104]
    def append(b):
        out.extend(b'\0'*((-len(out))%4));pos=len(out);out.extend(b);return pos
    title=translated(project.name);struct.pack_into('<II',out,116,append(title),len(title))
    offsets=[append(b) for b in previews];struct.pack_into('<I',out,32,offsets[0])
    for n,(screen,name,aod,vi,preview_uid) in enumerate(screens):
        base=168+176*n;struct.pack_into('<II',out,base,0x80000000,0 if aod else offsets[vi])
        out[base+104:base+168]=name.encode('utf-8').ljust(64,b'\0');struct.pack_into('<I',out,base+172,int(aod))
        for index,rows in enumerate(screen):
            offset=append(bytes(len(rows)*16));struct.pack_into('<II',out,base+8+8*index,len(rows),offset)
            for row,(uid,flags,b) in enumerate(rows):struct.pack_into('<IIII',out,offset+16*row,uid,flags,append(b),len(b))
    data=bytes(out);info=inspect_binary(data)
    if info['nativeSlots']!=sum(normalized_slot(s)['visible'] for vi in range(len(variants)) for s in project.variant_project(vi).complications):raise ValueError('Slot mancanti nel risultato nativo.')
    return data,metadata(project,screens,all_nodes,info['faceId'])

def metadata(project,screens,nodes,face_id):
    from .render import render,png_bytes
    manifest=ET.Element('Watchface',name='@watchfaceName',width='480',height='480',id=face_id,compressMethod='RLEReversed',editable=str(bool(any(normalized_slot(s)['visible'] for vi in range(max(1,len(project.variants))) for s in project.variant_project(vi).complications) or len(project.variants)>1)).lower())
    manifest.set('interactive',str(any(node['tag']=='App' for node in nodes.values())).lower())
    manifest.set('advanced',manifest.get('interactive'))
    resources=ET.SubElement(manifest,'Resources');files={};mapping=['watchfaceName: 6000000'];editor={'themes':[],'i18n':{'translations':{'watchfaceName':{language:project.name for language in LANGUAGES}},'locales':LANGUAGES},'formats':{},'dataSource':{},'isSlotFollowing':True,'introData':{},'aodDisplayMode':'multiColor'}
    editor['isSlotFollowing']=not any(v.get('independent') for v in project.variants)
    title=ET.SubElement(resources,'Translation',name='watchfaceName')
    for language in LANGUAGES:ET.SubElement(title,'Item',language=language,str=project.name)
    preview_paths={uid:f'_preview/Style_{vi+1}_{"AOD" if aod else "Normal"}Preview.png' for _,_,aod,vi,uid in screens}
    for uid,node in sorted(nodes.items()):
        name=uid_name(uid);mapping.append(f'{name}: {uid:x}')
        attrs={k:('@'+uid_name(v) if type(v) is int else str(v)) for k,v in node['attrs'].items()}
        el=ET.SubElement(resources,node['tag'],name=name,**attrs)
        if node['tag']=='Image':
            path=preview_paths.get(uid,f'studio/{name}.png');el.set('src',path);files['resources/'+path]=node['bitmap']
            editor['formats'][path]='indexed8'
        elif node['tag']=='App':
            path=node['attrs']['src']
            if path in files and files[path]!=node['app']:raise ValueError('Risorsa Lua condivisa incoerente.')
            files[path]=node['app']
        elif node['tag']=='ImageArray':
            for n,b in enumerate(node['bitmaps']):
                path=f'studio/{name}_{n}.png';ET.SubElement(el,'Image',src=path);files['resources/'+path]=b
                editor['formats'][path]='indexed8'
        elif node['tag']=='Translation':
            for language in LANGUAGES:ET.SubElement(el,'Item',language=language,str=node['text'])
        elif node['tag']=='DataItemImageValues':
            for value in node['values']:ET.SubElement(el,'Item',value=str(value))
        elif node['tag']=='Slot':
            for ref in node['choices']:ET.SubElement(el,'Item',ref='@'+uid_name(ref))
        elif node['tag']=='Widget':
            for x,y,ref,flags in node['children']:ET.SubElement(el,'Item',ref='@'+uid_name(ref),x=str(x),y=str(y))
    for n,(tables,name,aod,vi,preview_uid) in enumerate(screens):
        preview=preview_paths[preview_uid]
        theme=ET.SubElement(manifest,'Theme',name=name,type='AOD' if aod else 'normal',preview='@'+uid_name(preview_uid),bgColor='#000000' if aod else project.variant_project(vi).background,isPhotoAlbumWatchface='false')
        children=[]
        for _,_,payload in tables[0]:
            ref,x,y,flags,_=struct.unpack('<IhhII',payload);node=nodes[ref]
            ET.SubElement(theme,'Layout',ref='@'+uid_name(ref),x=str(x),y=str(y))
            attrs={'name':uid_name(ref),'x':x,'y':y,'_visibility':True,'_isLocked':False}
            if node['tag']=='Slot':
                options=[]
                for group in node['choices']:
                    gn=nodes[group];pn=nodes[gn['attrs']['preview']];path=f'studio/{uid_name(gn["attrs"]["preview"])}.png'
                    options.append({'id':uid_name(group),'type':'Widget','attrs':{'name':label(gn['key']),'w':int(gn['attrs']['w']),'h':int(gn['attrs']['h']),'resources':{'widgetPreview':{'studio':[path]},'editBox':{'studio':[f'studio/{uid_name(gn["attrs"]["editBox"])}.png']}},'relatedDataKey':uid_name(gn['attrs']['widgetName'])},'children':[{'id':uid_name(u),'type':nodes[u]['tag'],'attrs':{'name':uid_name(u),'x':x,'y':y}} for x,y,u,_ in gn['children']]})
                first=nodes[node['choices'][0]]
                attrs.update(SlotGroupName=node['attrs']['SlotGroupName'],slotGroupName=node['attrs']['SlotGroupName'],followingGroupName=node['attrs']['SlotGroupName'],
                             slotType='widget',widgetIdToDisplay=uid_name(node['choices'][0]),includeEmpty=any(nodes[c]['key']=='none' for c in node['choices']),sameEditBox=True,
                             resources={'editBox':{'studio':[f'studio/{uid_name(first["attrs"]["editBox"])}.png']}},positions=[],curSlotPosition=0,
                             w=node['width'],h=node['height'])
                children.append({'id':uid_name(ref),'type':'Slot','attrs':attrs,'children':options})
            else:
                if node['tag']=='Image':
                    from PIL import Image
                    from io import BytesIO
                    with Image.open(BytesIO(node['bitmap'])) as bitmap:width,height=bitmap.size
                    path=preview_paths.get(ref,f'studio/{uid_name(ref)}.png')
                    attrs.update(w=width,h=height,rotation=0,sourceEnabled=False,
                                 resources={'pointer0':{'studio':[path]}})
                children.append({'id':uid_name(ref),'type':node['tag'],'attrs':{**attrs,**{k:v for k,v in node['attrs'].items() if type(v) is not int}}})
        etheme={'id':f'studio_theme_{n:02}','name':name,'type':'AOD' if aod else 'normal','children':children,'bgColor':'#000000' if aod else project.variant_project(vi).background,'colorGroupTable':[{'id':'studio','name':'Studio','color':'#ffffff'}],'ifttts':[],'preview':preview}
        editor['themes'].append(etheme)
    for uid,node in nodes.items():
        if node['tag']=='Translation':editor['i18n']['translations'][uid_name(uid)]={language:node['text'] for language in LANGUAGES}
    ET.indent(manifest);files['resources/manifest.xml']=ET.tostring(manifest,encoding='utf-8',xml_declaration=True)
    files['editor.config.json']=json.dumps(editor,ensure_ascii=False,indent=2).encode();files['uidmap.map']=('\n'.join(mapping)+'\n').encode()
    files['s5studio-schema.json']=json.dumps({'version':1,'generator':'S5 Studio 1.8.1','themes':[{'name':name,'aod':aod} for _,name,aod,_,_ in screens],
         'phonePreview':{'staticOnly':True,'resourceDirectory':'_preview','completeLayers':True,'modHardwareVerified':False},
         'project':project.metadata(),'resourceFiles':{k:hashlib.sha256(v).hexdigest() for k,v in files.items() if k.startswith(('resources/studio/','resources/_preview/','app/lua/'))},
         'metadataHashes':{k:hashlib.sha256(files[k]).hexdigest() for k in ('resources/manifest.xml','editor.config.json','uidmap.map')},
         'hardwareVerified':False},ensure_ascii=False,indent=2).encode()
    return files
