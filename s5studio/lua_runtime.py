"""Compile Lua app resources through EasyFace's actual Shape 34 interface."""
from pathlib import Path, PurePosixPath
import struct
from .motion import LUA_SOURCES, ALL_LUA_SOURCES, lua_element, pro_enabled
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
             lua_element(e)]
    if not indices:return []
    span=layers[indices[0]:indices[-1]+1]
    for e in span:
        if isinstance(e,dict) or e.kind not in ('image','text','rect','circle') and not lua_element(e):
            name=e.get('name','Complicazione') if isinstance(e,dict) else e.name
            raise ValueError(f'Sposta il livello dinamico «{name}» sopra o sotto il gruppo di lancette Crono/Decimi. Le lancette Lua devono condividere una scena; immagini, testi e forme possono restare tra loro.')
    return span


def write_pointer(project, e, directory, variant):
    return write_scene(project,[e],directory,variant,key=f'v{variant}_{e.id}')


def write_scene(project, layers, directory, variant, *, key=None):
    """One compiled App entry contains every Lua view and one tap handler."""
    if pro_enabled(project):return write_pro_scene(project,layers,directory,variant,key=key)
    base = directory / 'app/lua'; (base/'gfx').mkdir(parents=True, exist_ok=True)
    (base/'studio_core.lua').write_bytes((resource_root()/'s5studio/lua/studio_core.lua').read_bytes())
    complete_scene=key is None
    key = key or f'v{variant}_scene'
    lines = ['local lvgl = require("lvgl")', 'local core = require("studio_core")',
             'local pro = rawget(_G, "S5StudioChronoPro120")']
    if complete_scene:
        lines += ['if pro then pro:leave() end','core:screen(false)',
                  'core.views = {}; core.state = "reset"; core.elapsed = 0; core.started = 0','core:screen(true)']
    else:lines += ['if pro then pro:leave(); core:screen(true) end']
    lines += [
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


def pro_views(e):
    """Split the analog layer inside the scene without changing its stacking."""
    if e.kind!='analog':return [e]
    from dataclasses import replace
    result=[]
    for hand,source,period in (('hour','studioTimeHour',12),('minute','studioTimeMinute',60),('second','studioIntegratedSecond',60)):
        changes={k:getattr(e,hand+k[6:]) for k in e.__dataclass_fields__ if k.startswith('second_') and k!='second_hand'}
        result.append(replace(e,**changes,kind='pointer',id=e.id+'_'+hand,source=source,
                              chrono_pro=False,second_hand=False,pointer_end_pivot=False,
                              value_start=0,value_range=period,angle_start=0,angle_range=360))
    return result


def scene_bindings(project):
    return [v for e in scene_layers(project) if lua_element(e) for v in (pro_views(e) if pro_enabled(project) else [e])]


def write_pro_scene(project,layers,directory,variant,*,key=None):
    from PIL import Image,ImageDraw
    from .render import analog_face,rgba
    base=directory/'app/lua';(base/'gfx').mkdir(parents=True,exist_ok=True)
    for module in ('studio_core','studio_core_pro'):
        (base/(module+'.lua')).write_bytes((resource_root()/f's5studio/lua/{module}.lua').read_bytes())
    key=key or f'v{variant}_scene'
    views=scene_bindings(project)
    lines=['local lvgl = require("lvgl")','local core = require("studio_core_pro")',
           'local widgets = debug.getregistry()["widgets"].__index',
           'local scene = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
           'scene:clear_flag(lvgl.FLAG.SCROLLABLE)','scene:clear_flag(lvgl.FLAG.CLICKABLE)',
           f'core:configure(scene, {str(any(v.source=="studioChronoDecisecond" for v in views)).lower()})']
    def bitmap(image,x,y,name):
        (base/'gfx'/name).write_bytes(png_bytes(image))
        lines.extend([f'local img = scene:Image {{x={x},y={y},src=SCRIPT_PATH.."gfx/{name}"}}','img:clear_flag(lvgl.FLAG.CLICKABLE)'])
    for e in layers:
        if not lua_element(e):
            pair=canvas_image(project,e) if e.kind=='image' else (static_image(project,e),e.x,e.y)
            if pair:bitmap(*pair,f'v{variant}_{e.id}_static.png')
            continue
        if e.kind=='analog':
            bitmap(analog_face(e),e.x,e.y,f'v{variant}_{e.id}_ticks.png')
            lines+=['do','local root = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
                    'root:clear_flag(lvgl.FLAG.SCROLLABLE)','root:clear_flag(lvgl.FLAG.CLICKABLE)','local groups = {{},{},{}}']
            analog_views=pro_views(e)
            # Match the native analog stack: all shadows precede all mothers.
            for shadow in ([True,False] if e.show_shadows else [False]):
                for index,view in enumerate(analog_views,1):
                    lines+=['do',f'local hands = groups[{index}]']
                    lines+=pointer_lines(project,view,base,variant,shadow_modes=[shadow],value_scale=1000)
                    lines+=['end']
            for index,view in enumerate(analog_views,1):
                lines += [f'core:add {{id="{view.id}",root=root,hands=groups[{index}],source="{view.source}",range={view.value_range},valueStart=0,valueRange={view.value_range},angleRange=360,scale=1000,smooth={str(view.smooth_seconds).lower()}}}']
            lines+=['end']
            dot=Image.new('RGBA',(14,14));ImageDraw.Draw(dot).ellipse((1,1,13,13),fill=rgba(e))
            bitmap(dot,e.x+e.width//2-7,e.y+e.height//2-7,f'v{variant}_{e.id}_center.png')
            continue
        for view in pro_views(e):
            lines+=['do','local root = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
                    'root:clear_flag(lvgl.FLAG.SCROLLABLE)','root:clear_flag(lvgl.FLAG.CLICKABLE)','local hands = {}']
            scale=max(1,min(1000,65535//max(1,view.value_start+view.value_range)))
            lines+=pointer_lines(project,view,base,variant,value_scale=scale)
            period=ALL_LUA_SOURCES[view.source][1] if view.source in ALL_LUA_SOURCES else (12 if view.source=='studioTimeHour' else 60)
            lines += [f'core:add {{id="{view.id}",root=root,hands=hands,source="{view.source}",range={period},valueStart={view.value_start},valueRange={view.value_range},angleStart={view.angle_start},angleRange={view.angle_range},scale={scale},smooth={str(view.smooth_seconds).lower()}}}','end']
    lines+=['local tap = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
            'tap:clear_flag(lvgl.FLAG.SCROLLABLE)','tap:add_flag(lvgl.FLAG.CLICKABLE)',
            'tap:onevent(lvgl.EVENT.PRESSED or lvgl.EVENT.CLICKED, function() core:tap() end)']
    name=f'lua/studio_{key}.lua';(directory/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name


def pointer_lines(project,e,base,variant,*,shadow_modes=None,value_scale=1):
    key=f'v{variant}_{e.id}';lines=[]
    for shadow in (shadow_modes if shadow_modes is not None else [True, False] if e.show_shadows else [False]):
        pair = hand_image(e, 'second', project, shadow=shadow)
        if pair is None: continue
        image, anchor = pair
        name = key + ('_shadow.png' if shadow else '.png')
        (base/'gfx'/name).write_bytes(png_bytes(image))
        dx, dy = hand_shadow_offset(e, 'second', project) if shadow else (0,0)
        x,y=e.x+e.width//2-anchor[0]+dx,e.y+e.height//2-anchor[1]+dy
        lines += [f'local h = widgets.Pointer(root, {{x={x},y={y},pivot={{x={anchor[0]},y={anchor[1]}}},value=0,src=SCRIPT_PATH.."gfx/{name}"}})',
                  'h:set {range={angleStart=%d,angleRange=%d,valueStart=%d,valueRange=%d}}' % (e.angle_start*10,e.angle_range*10,e.value_start*value_scale,e.value_range*value_scale),
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
    requested=any(e.visible and not e.aod and lua_element(e)
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
    pro_core=files.get('lua/studio_core_pro.lua',b'')
    if b'S5StudioChrono100' in core and not pro_core:
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
    if pro_core:
        import re
        variants=[]
        for i in range(max(1,len(project.variants))):
            p=project.variant_project(i);views=scene_bindings(p)
            expected=[f'lua/studio_v{i}_scene.lua'] if views else []
            if i>=len(screen_apps) or screen_apps[i]!=expected:
                raise ValueError('Crono-Pro richiede una sola scena Lua per stile.')
            if views:
                code=files[expected[0]].decode('utf8')
                ids=sorted(v.id for v in views)
                if sorted(re.findall(r'core:add\s*\{id="([^"]+)"',code))!=ids or sorted(re.findall(r'core:add[^\n]+source="([^"]+)"',code))!=sorted(v.source for v in views):
                    raise ValueError('Lancette/sorgenti Crono-Pro diverse dal progetto.')
                if ('require("studio_core_pro")' in code)!=pro_enabled(p):
                    raise ValueError('Modalità Crono-Pro diversa dal runtime iniettato.')
                if code.count('tap:onevent(')!=int(pro_enabled(p) or any(v.source!='studioDecisecond' for v in views)):
                    raise ValueError('Crono-Pro deve avere un solo gestore del tap.')
            variants.append({'variant':i,'mode':'pro' if pro_enabled(p) else 'separate',
                             'entry':expected[0] if views else None,'pointerIds':sorted(v.id for v in views)})
        result['luaArchitecture']={'type':'single-scene-per-theme','crossWidgetVmSharingRequired':False,'scenes':variants}
        result['chronoPro']={'injected':True,'runtime':'studio_core_pro.lua','states':['rest','arming','ready','running','stopped','resetting'],
                            'runningSmoothForcedOff':True,'runningPeriodMsWithDeciseconds':100,'runningPeriodMsWithoutDeciseconds':1000,
                            'writesOnlyChangedValues':True,'transitionSmoothForcedOn':True,'transitionDurationMs':int(re.search(rb'\btransitionMs=(\d+)',pro_core).group(1)),'transitionTargetFps':25,
                            'pointerValueDomain':'scaled-integer','defaultPointerValueScale':1000,
                            'aodCancelsTransitions':True,'aodNativeScreenPreserved':True,'mainSecondsSingleController':'Lua',
                            'civilHandsInSameSceneToPreserveStacking':True,'clockFallback':'LVGL animation phase; os.time for sleep with one-second precision'}
        if b'never reverse the sweep' in pro_core:
            result['chronoPro']['transitionDirection']='clockwise-only'
            result['limitations'][0]='Crono-Pro 1.2: test reale superato, inclusi rientri orari e varianti indipendenti.'
        result['limitations']=['Crono-Pro 1.2 collaudato sul S5; la 1.4 porta la durata comune dei rientri a 720 ms. Crono separato 1.0 collaudato.',
                               'Fallback fase Anim: precisione durante sospensioni limitata da os.time; senza clock civile non misura il tempo a schermo spento.',
                               'Cronografo locale: ricreazione della VM/cambio quadrante azzerano il conteggio. Consumo non misurato.']
    return result
