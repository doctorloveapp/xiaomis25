"""A civil-calendar-driven mechanical moon disc; no fabricated sensor code."""
from datetime import date
import re

SOURCE='studioMoon59'
LABEL='Fasi lunari · 59 posizioni (giornaliero)'
# Full Moon, 26 September 2026, 16:49 UTC (US Naval Observatory).
# This is a civil-date calibration for a 59-day wheel, not an ephemeris.
REFERENCE_DATE='2026-09-26'


def lunar_element(e):
    return e.kind=='disk' and e.source==SOURCE


def parse_date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ValueError('Data lunare: usa una data valida nel formato AAAA-MM-GG.')
    result=date.fromisoformat(value)
    if not 1900<=result.year<=2399:raise ValueError('Data lunare: anno da 1900 a 2399.')
    return result


def calibration_errors(reference,offset):
    errors=[]
    try:parse_date(reference)
    except (ValueError,TypeError):errors.append('Data di riferimento lunare non valida (1900–2399).')
    if type(offset) is not int or not -58<=offset<=58:errors.append('Correzione lunare: da −58 a 58 giorni interi.')
    return errors


def position(reference=REFERENCE_DATE,offset=0,current=None):
    current=date.today() if current is None else parse_date(current) if isinstance(current,str) else current
    return ((current-parse_date(reference)).days+offset)%59


def preview_value(e,values):
    return position(e.moon_reference_date,e.moon_day_offset,values.get('__moonDate'))


def defaults(source):
    if source==SOURCE:
        return {'value_start':0,'value_range':59,'angle_start':0,'angle_range':360,
                'moon_reference_date':REFERENCE_DATE,'moon_day_offset':0}
    if source=='dateMoon':return {'value_start':0,'value_range':8,'angle_start':-90,'angle_range':180}
    return {}


def lines(project,e,base,variant):
    """Bind one disc and its shadow, outside the chronograph's view list."""
    from .lua_runtime import pointer_lines
    from .paths import resource_root
    reference=parse_date(e.moon_reference_date)
    (base/'studio_moon_disk.lua').write_bytes((resource_root()/'s5studio/lua/studio_moon_disk.lua').read_bytes())
    return ['do','local moon = require("studio_moon_disk")',
            'local root = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
            'root:clear_flag(lvgl.FLAG.SCROLLABLE)','root:clear_flag(lvgl.FLAG.CLICKABLE)','local hands = {}',
            *pointer_lines(project,e,base,variant),
            f'moon.bind(root,hands,{{id="{e.id}",reference={{{reference.year},{reference.month},{reference.day}}},offset={e.moon_day_offset},aod={str(e.aod).lower()}}})','end']


def write_scene(project,layers,directory,variant,*,key=None):
    from .render import canvas_static,png_bytes
    base=directory/'app/lua';(base/'gfx').mkdir(parents=True,exist_ok=True)
    code=['local lvgl = require("lvgl")','local widgets = debug.getregistry()["widgets"].__index',
          'local scene = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
          'scene:clear_flag(lvgl.FLAG.SCROLLABLE)','scene:clear_flag(lvgl.FLAG.CLICKABLE)']
    for e in layers:
        if e.kind=='gif':
            from .gif_animation import lua_lines
            code+=lua_lines(project,e,base,variant);continue
        if lunar_element(e):code+=lines(project,e,base,variant)
        else:
            from .scene_data import supported,lines as scene_data_lines
            if supported(e):code+=scene_data_lines(project,e,base,variant);continue
            from .live_data import live_element,live_lines
            if live_element(e):code+=live_lines(project,e,base,variant);continue
            pair=canvas_static(project,e)
            if pair:
                bitmap,x,y=pair;name=f'v{variant}_{e.id}_static.png'
                (base/'gfx'/name).write_bytes(png_bytes(bitmap))
                code += [f'local img = scene:Image {{x={x},y={y},src=SCRIPT_PATH.."gfx/{name}"}}','img:clear_flag(lvgl.FLAG.CLICKABLE)']
    name='lua/studio_'+(key or f'v{variant}_scene')+'.lua'
    (directory/'app'/name).write_text('\n'.join(code)+'\n',encoding='utf8')
    return name


def validate_injection(project,files):
    """Compare packaged bindings and module bytes with every style's settings."""
    from .paths import resource_root
    import hashlib
    discs=[];entries=set()
    for i in range(max(1,len(project.variants))):
        for e in project.variant_project(i).elements:
            if not e.visible or not lunar_element(e) or e.aod and (i or not project.aod_enabled):continue
            name=f'lua/studio_v{i}_moon_{e.id}_aod.lua' if e.aod else f'lua/studio_v{i}_scene.lua'
            if name not in files:raise ValueError('Entry point del disco lunare mancante: '+name)
            expected=next(line for line in lines_signature(e) if line.startswith('moon.bind'))
            code=files[name].decode('utf8').replace('\r\n','\n')
            blocks=re.findall(r'do\nlocal moon = require\("studio_moon_disk"\)\n(.*?)\n(moon\.bind[^\n]+)\nend',code,re.S)
            matches=[body for body,binding in blocks if binding==expected]
            if len(matches)!=1:
                raise ValueError('Calibrazione del disco lunare diversa dal progetto: '+e.name)
            ranges=[line for line in matches[0].splitlines() if line.startswith('h:set {range=')]
            expected_range='h:set {range={angleStart=%d,angleRange=%d,valueStart=0,valueRange=59}}' % (e.angle_start*10,e.angle_range*10)
            if not ranges or any(line!=expected_range for line in ranges):
                raise ValueError('Rotazione del disco lunare diversa dal progetto: '+e.name)
            entries.add(name)
            discs.append({'variant':i,'id':e.id,'aod':e.aod,'referenceDate':e.moon_reference_date,
                          'dayOffset':e.moon_day_offset,'valueRange':59,'angleStart':e.angle_start,'angleRange':e.angle_range})
    if not discs:return None
    key='lua/studio_moon_disk.lua'
    expected=(resource_root()/'s5studio/lua/studio_moon_disk.lua').read_bytes()
    if files.get(key)!=expected:raise ValueError('Modulo del calendario lunare assente o alterato.')
    for entry in entries:
        code=files[entry].decode('utf8')
        for e in discs:
            if e['aod']:continue
            if 'core:add {id="'+e['id']+'"' in code:raise ValueError('Il disco lunare non deve essere controllato dal cronografo.')
    return {'injected':True,'runtime':'studio_moon_disk.lua','moduleSha256':hashlib.sha256(expected).hexdigest(),
            'positions':59,'stepDegrees':360/59,'calendarSources':['dateYear','dateMonth','dateDay'],
            'counter':'civil-date-difference-modulo-59','writesOnlyChangedValues':True,
            'backgroundPolling':False,'animationTimers':False,'fallbackNotificationCoalescingMs':200,
            'fallbackTimerPausedInSteadyState':True,'aodFrozenBetweenActivations':True,
            'chronoIndependent':True,'hardwareVerified':False,'discs':discs}


def lines_signature(e):
    reference=parse_date(e.moon_reference_date)
    return [f'moon.bind(root,hands,{{id="{e.id}",reference={{{reference.year},{reference.month},{reference.day}}},offset={e.moon_day_offset},aod={str(e.aod).lower()}}})']
