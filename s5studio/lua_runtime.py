"""Compile Lua app resources through EasyFace's actual Shape 34 interface."""
from pathlib import Path, PurePosixPath
import struct
from .motion import LUA_SOURCES
from .render import hand_image, hand_shadow_offset, png_bytes, canvas_image, static_image
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


def scene_layers(project, aod=False):
    """Keep Lua pointers in one VM, preserving static layers between them.

    Moving a native dynamic widget into the Lua scene would change its binding;
    fail explicitly instead of silently changing its layering or sensor API.
    """
    if aod:return []
    layers=[e for e in project.ordered_layers(False)
            if (e.get('visible') if isinstance(e,dict) else e.visible)]
    indices=[i for i,e in enumerate(layers) if not isinstance(e,dict) and
             e.kind=='pointer' and e.source in LUA_SOURCES]
    if not indices:return []
    span=layers[indices[0]:indices[-1]+1]
    for e in span:
        if isinstance(e,dict) or e.kind not in ('image','text','rect','circle') and not (e.kind=='pointer' and e.source in LUA_SOURCES):
            name=e.get('name','Complicazione') if isinstance(e,dict) else e.name
            raise ValueError(f'Sposta il livello dinamico «{name}» sopra o sotto il gruppo di lancette Crono/Decimi. Le lancette Lua devono condividere una scena; immagini, testi e forme possono restare tra loro.')
    return span


def write_pointer(project, e, directory, variant):
    return write_scene(project,[e],directory,variant,key=f'v{variant}_{e.id}')


def write_scene(project, layers, directory, variant, *, key=None):
    """One compiled App entry contains every Lua view and one tap handler."""
    base = directory / 'app/lua'; (base/'gfx').mkdir(parents=True, exist_ok=True)
    (base/'studio_core.lua').write_bytes((resource_root()/'s5studio/lua/studio_core.lua').read_bytes())
    key = key or f'v{variant}_scene'
    lines = ['local lvgl = require("lvgl")', 'local core = require("studio_core")',
             'local widgets = debug.getregistry()["widgets"].__index',
             'local scene = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
             'scene:clear_flag(lvgl.FLAG.SCROLLABLE)', 'scene:clear_flag(lvgl.FLAG.CLICKABLE)']
    pointers=[e for e in layers if e.kind=='pointer' and e.source in LUA_SOURCES]
    for e in layers:
        if e not in pointers:
            pair=canvas_image(project,e) if e.kind=='image' else (static_image(project,e),e.x,e.y)
            if pair:
                bitmap,x,y=pair;name=f'v{variant}_{e.id}_static.png'
                (base/'gfx'/name).write_bytes(png_bytes(bitmap))
                lines += [f'local img = scene:Image {{x={x},y={y},src=SCRIPT_PATH.."gfx/{name}"}}',
                          'img:clear_flag(lvgl.FLAG.CLICKABLE)']
            continue
        lines += ['do',('local root = scene' if len(pointers)==1 else
                        'local root = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})'),
                  'root:clear_flag(lvgl.FLAG.SCROLLABLE)', 'root:clear_flag(lvgl.FLAG.CLICKABLE)', 'local hands = {}']
        lines += pointer_lines(project,e,base,variant)
        lines += [f'core:add {{id="{e.id}",root=root,hands=hands,source="{e.source}",range={LUA_SOURCES[e.source][1]},valueStart={e.value_start},valueRange={e.value_range},smooth={str(e.smooth_seconds).lower()}}}', 'end']
    if any(e.source!='studioDecisecond' for e in pointers):
        lines += ['local tap = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
                  'tap:clear_flag(lvgl.FLAG.SCROLLABLE)', 'tap:add_flag(lvgl.FLAG.CLICKABLE)',
                  'tap:onevent(lvgl.EVENT.PRESSED or lvgl.EVENT.CLICKED, function() core:tap() end)']
    name=f'lua/studio_{key}.lua'
    (directory/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name


def pointer_lines(project,e,base,variant):
    key=f'v{variant}_{e.id}';lines=[]
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
    return lines


def interaction_report(project, data, manifest_bytes):
    import xml.etree.ElementTree as ET
    from .watchface_library import read_tables
    from .native import inspect_binary
    files={}; app_layouts=0;screen_apps=[]
    for screen in inspect_binary(data)['screens']:
        tables=read_tables(data,screen['index'])
        if screen['aod'] and tables[5]: raise ValueError('Script Lua presente in AOD.')
        for uid, _, payload in tables[5]:
            name,content=unpack_app(payload)
            if name in files and files[name]!=content: raise ValueError('File Lua omonimi con contenuti diversi.')
            files[name]=content
        apps={uid for uid,_,_ in tables[5]}
        entries=[unpack_app(next(payload for uid,_,payload in tables[5] if uid==struct.unpack_from('<I',b)[0]))[0]
                 for _,_,b in tables[0] if struct.unpack_from('<I',b)[0] in apps]
        app_layouts+=len(entries)
        if not screen['aod']:screen_apps.append(entries)
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
    result = {'requested':requested,'injected':bool(app_layouts),'status':'injected-and-structurally-verified' if requested else 'not-requested',
            'appLayoutCount':app_layouts,'files':{f'app/{n}':hashlib.sha256(b).hexdigest() for n,b in files.items()},
            'manifestInteractive':manifest.get('interactive'),'aodSecondsExcluded':True,'hardwareVerified':False,
            'limitations':(['Runtime Lua, clock monotono e VM condivisa da verificare sul firmware S5.',
                            'Cronografo locale al quadrante; cambio quadrante o ricreazione della VM resetta il conteggio.'] if requested else [])}
    # Keep old exports independently verifiable with their original report.
    core=files.get('lua/studio_core.lua',b'')
    if b'S5StudioChrono011' in core or b'S5StudioChrono100' in core:
        result['decisecondTiming']={'engine':'lvgl-animation','durationMs':1000,'requiresExternalClock':False,'scalesToConfiguredRange':True}
        result['chronoTiming']={'clockPriority':['lvgl.tick_get','/proc/uptime','os.time'],
                               'wallClockFallbackPrecisionMs':1000,'tapArea':'full-face',
                               'tapEvent':'PRESSED (CLICKED fallback)','pagePausePreservesTap':True,
                               'hardwareVerified':False}
        result['limitations']=['Runtime Lua, Anim, eventi di tap e VM condivisa da verificare sul firmware S5.',
                               'Fallback os.time: precisione di un secondo; sincronizzazione dell’ora può alterare il conteggio.',
                               'Cronografo locale al quadrante; cambio quadrante o ricreazione della VM resetta il conteggio.']
    if b'S5StudioChrono100' in core:
        import re
        variants=[]
        for i in range(max(1,len(project.variants))):
            p=project.variant_project(i)
            ids=sorted(e.id for e in p.elements if e.visible and not e.aod and e.kind=='pointer' and e.source in LUA_SOURCES)
            expected=[f'lua/studio_v{i}_scene.lua'] if ids else []
            if i>=len(screen_apps) or screen_apps[i]!=expected:
                raise ValueError('Il tema Lua deve avere una sola scena con tutte le lancette sincronizzate.')
            if ids:
                code=files[expected[0]].decode('utf8')
                actual=sorted(re.findall(r'core:add\s*\{id="([^"]+)"',code))
                sources=re.findall(r'core:add[^\n]+source="([^"]+)"',code)
                if actual!=ids or sorted(sources)!=sorted(e.source for e in p.elements if e.id in ids):
                    raise ValueError('La scena Lua non contiene tutti gli abbinamenti delle lancette del progetto.')
                taps=code.count('tap:onevent(')
                if taps!=int(any(s!='studioDecisecond' for s in sources)):
                    raise ValueError('La scena Crono deve avere un solo gestore del tap.')
            variants.append({'variant':i,'entry':expected[0] if ids else None,'pointerIds':ids})
        result['luaArchitecture']={'type':'single-scene-per-theme','crossWidgetVmSharingRequired':False,'scenes':variants}
        result['chronoTiming']['sharedStateScope']='one entry point / one VM per theme'
        result['limitations']=['Nuovo runtime 1.0 da confermare sul firmware S5 per minuti e ore Crono.',
                               'Fallback os.time: precisione di un secondo; sincronizzazione dell’ora può alterare il conteggio.',
                               'Cronografo locale al quadrante; cambio quadrante o ricreazione della VM resetta il conteggio.']
    return result
