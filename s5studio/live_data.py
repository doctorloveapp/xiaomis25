"""Pre-warp font glyphs, then select them on real sensor notifications.

No preview value is exported as a sensor value. Glyph positions use exactly
the full-field mesh used by the editor, including alignment and clipping.
"""
import hashlib,json,struct,xml.etree.ElementTree as ET
from PIL import Image
from .calendar_labels import labels_for
from .paths import resource_root
from .render import digit_image,digit_metrics,number_parts,png_bytes
from .transforms import active,raster
from .complications import ALIASES


def live_element(e):
    return e.kind=='number' and active(e) and not labels_for(e)


def lua_value(value):
    if isinstance(value,bool):return str(value).lower()
    if isinstance(value,(int,float)):return str(value)
    if isinstance(value,str):return json.dumps(value,ensure_ascii=True)
    if isinstance(value,list):return '{'+','.join(lua_value(v) for v in value)+'}'
    return '{'+','.join('['+lua_value(k)+']='+lua_value(v) for k,v in value.items())+'}'


def live_lines(project,e,base,variant):
    (base/'gfx').mkdir(parents=True,exist_ok=True)
    (base/'studio_live_data.lua').write_bytes((resource_root()/'s5studio/lua/studio_live_data.lua').read_bytes())
    cw,_,_=digit_metrics(project,e)
    (_,count,x,y),=number_parts(project,e)[0]
    cache={};glyphs={}
    chars={char:digit_image(project,e,char) for char in '0123456789-.'}
    for length in range(1,count+1):
        offset=(count-length)*cw if e.align=='right' else count*cw//2-length*cw//2 if e.align=='center' else 0
        rows=[]
        for index in range(length):
            row={}
            for char,graphic in chars.items():
                position=(x+offset+index*cw,y,char)
                if position not in cache:
                    source=Image.new('RGBA',(e.width,e.height));source.alpha_composite(graphic,position[:2])
                    pair=raster(project,e,source)
                    box=pair[0].getchannel('A').getbbox() if pair else None
                    if box:
                        bitmap=pair[0].crop(box);px,py=pair[1]+box[0],pair[2]+box[1]
                    else:bitmap=Image.new('RGBA',(1,1));px=py=0
                    raw=png_bytes(bitmap);name='live_'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
                    (base/'gfx'/name).write_bytes(raw)
                    cache[position]={'x':px,'y':py,'src':'gfx/'+name}
                row[char]=cache[position]
            rows.append(row)
        glyphs[length]=rows
    config={'id':e.id,'source':ALIASES.get(e.source,e.source),'count':e.digits,
            'decimals':e.decimals,'leadingZero':e.leading_zero,'aod':e.aod,'glyphs':glyphs}
    return ['require("studio_live_data").add(scene, '+lua_value(config)+')']


def write_live(project,e,directory,variant):
    base=directory/'app/lua'
    lines=['local lvgl = require("lvgl")',
           'local scene = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
           'scene:clear_flag(lvgl.FLAG.SCROLLABLE)','scene:clear_flag(lvgl.FLAG.CLICKABLE)']
    lines+=live_lines(project,e,base,variant)
    name=f'lua/studio_v{variant}_live_{e.id}.lua'
    (directory/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name


def complete_aod_apps(data,source_path):
    """EasyFace 4.23 allocates App rows in AOD but never calls SetupApp there.

    Fill ONLY its reserved empty rows with already compiled common App records;
    resolve AOD App layout references by the exact generated entry filename.
    No sensor descriptor, image encoding or proprietary header is invented.
    """
    from .watchface_library import directory_bases,directory_stride,read_tables
    from .lua_runtime import unpack_app
    from urllib.parse import unquote
    paths=list(source_path.parent.joinpath('AOD').glob('*.fprj'))
    if not paths:return data
    widgets=ET.parse(paths[0]).getroot().find('Screen').findall('Widget')
    if not any(w.get('Shape')=='34' for w in widgets):return data
    if directory_stride(data)[1]!=88 or data[28]<2:raise ValueError('Directory AOD EasyFace inattesa.')
    bases=directory_bases(data);main,aod=bases[0],bases[1]
    count,offset=struct.unpack_from('<II',data,main+48)
    reserved,target=struct.unpack_from('<II',data,aod+48)
    if not count or reserved!=count or any(data[target:target+reserved*16]):
        raise ValueError('Tabella App AOD diversa dai record vuoti attesi da EasyFace 4.23.')
    names={unpack_app(payload)[0]:uid for uid,_,payload in read_tables(data,0)[5]}
    result=bytearray(data);result[target:target+count*16]=data[offset:offset+count*16]
    layout_count,layout_offset=struct.unpack_from('<II',data,aod+8)
    cursor=0
    for w in widgets:
        if w.get('Shape')=='34':
            name=unquote(w.get('Name','')[4:])
            if name not in names or '_live_' not in name:raise ValueError('Entry point AOD live assente dalle risorse compilate.')
            pos=struct.unpack_from('<I',result,layout_offset+cursor*16+8)[0]
            if struct.unpack_from('<I',result,pos)[0]!=0:raise ValueError('Riferimento App AOD inatteso.')
            struct.pack_into('<I',result,pos,names[name])
        cursor+=sum(bool(w.get(k)) for k in ('HourHand_ImageName','MinuteHand_Image','SecondHand_Image')) if w.get('Shape')=='27' else 1
    if cursor!=layout_count:raise ValueError('Layout AOD diverso dai sorgenti.')
    return bytes(result)
