"""Compile Lua app resources through EasyFace's actual Shape 34 interface."""
from pathlib import Path, PurePosixPath
import struct
from .motion import LUA_SOURCES
from .render import hand_image, hand_shadow_offset, png_bytes
from .paths import resource_root


def unpack_app(payload):
    if len(payload) < 20: raise ValueError('Risorsa Lua troncata.')
    header = struct.unpack_from('<I', payload)[0]
    size, length = header & 0xffffff, header >> 24
    if 20 + length + size != len(payload): raise ValueError('Dimensioni della risorsa Lua incoerenti.')
    name = payload[20:20+length].decode('ascii')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or not name.startswith('lua/'):
        raise ValueError('Percorso della risorsa Lua non valido.')
    return name, payload[20+length:]


def write_pointer(project, e, directory, variant):
    base = directory / 'app/lua'; (base/'gfx').mkdir(parents=True, exist_ok=True)
    (base/'studio_core.lua').write_bytes((resource_root()/'s5studio/lua/studio_core.lua').read_bytes())
    key = f'v{variant}_{e.id}'
    lines = ['local lvgl = require("lvgl")', 'local core = require("studio_core")',
             'local widgets = debug.getregistry()["widgets"].__index',
             'local root = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
             'root:clear_flag(lvgl.FLAG.SCROLLABLE)', 'root:clear_flag(lvgl.FLAG.CLICKABLE)',
             'local hands = {}']
    for shadow in ([True, False] if e.show_shadows else [False]):
        pair = hand_image(e, 'second', project, shadow=shadow)
        if pair is None: continue
        image, anchor = pair
        name = key + ('_shadow.png' if shadow else '.png')
        (base/'gfx'/name).write_bytes(png_bytes(image))
        dx, dy = hand_shadow_offset(e, 'second', project) if shadow else (0,0)
        x,y=e.x+e.width//2-anchor[0]+dx,e.y+e.height//2-anchor[1]+dy
        lines += [f'local h = widgets.Pointer(root, {{x={x},y={y},pivot={{x={anchor[0]},y={anchor[1]}}},value=0,src=SCRIPT_PATH.."gfx/{name}"}})',
                  'h:set {range={angleStart=%d,angleRange=%d,valueStart=%d,valueRange=%d}}' % (e.angle_start*10,e.angle_range*10,e.value_start,e.value_range),
                  'h:clear_flag(lvgl.FLAG.CLICKABLE)', 'hands[#hands+1] = h']
    if e.source != 'studioDecisecond':
        lines += [f'local tap = lvgl.Object(root, {{x={e.x},y={e.y},w={e.width},h={e.height},bg_opa=0,border_width=0,pad_all=0}})',
                  'tap:clear_flag(lvgl.FLAG.SCROLLABLE)', 'tap:add_flag(lvgl.FLAG.CLICKABLE)',
                  'tap:onevent(lvgl.EVENT.CLICKED, function() core:tap() end)']
    lines += [f'core:add {{root=root,hands=hands,source="{e.source}",range={LUA_SOURCES[e.source][1]},smooth={str(e.smooth_seconds).lower()}}}']
    name=f'lua/studio_{key}.lua'
    (directory/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name


def interaction_report(project, data, manifest_bytes):
    import xml.etree.ElementTree as ET
    from .watchface_library import read_tables
    from .native import inspect_binary
    files={}; app_layouts=0
    for screen in inspect_binary(data)['screens']:
        tables=read_tables(data,screen['index'])
        if screen['aod'] and tables[5]: raise ValueError('Script Lua presente in AOD.')
        for uid, _, payload in tables[5]:
            name,content=unpack_app(payload)
            if name in files and files[name]!=content: raise ValueError('File Lua omonimi con contenuti diversi.')
            files[name]=content
        apps={uid for uid,_,_ in tables[5]}
        app_layouts+=sum(struct.unpack_from('<I',b)[0] in apps for _,_,b in tables[0])
        if screen['aod']:
            from .motion import SECOND_SOURCES
            from .model import SOURCES
            codes={bytes.fromhex(SOURCES[k][1]) for k in SECOND_SOURCES if k in SOURCES}
            if any(b[3]>>4==3 and b[:2] in codes for _,_,b in tables[7]):
                raise ValueError('Lancetta secondi presente in AOD.')
    manifest=ET.fromstring(manifest_bytes)
    requested=any(e.visible and not e.aod and e.source in LUA_SOURCES and e.kind=='pointer'
                  for i in range(max(1,len(project.variants))) for e in project.variant_project(i).elements)
    if requested != bool(app_layouts) or manifest.get('interactive')!=str(requested).lower():
        raise ValueError('Interattività richiesta ma script/layout/manifest incoerenti.')
    import hashlib
    return {'requested':requested,'injected':bool(app_layouts),'status':'injected-and-structurally-verified' if requested else 'not-requested',
            'appLayoutCount':app_layouts,'files':{f'app/{n}':hashlib.sha256(b).hexdigest() for n,b in files.items()},
            'manifestInteractive':manifest.get('interactive'),'aodSecondsExcluded':True,'hardwareVerified':False,
            'limitations':(['Runtime Lua, clock monotono e VM condivisa da verificare sul firmware S5.',
                            'Cronografo locale al quadrante; cambio quadrante o ricreazione della VM resetta il conteggio.'] if requested else [])}
