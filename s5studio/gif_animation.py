"""GIF decoding, editable frame selection and the native S5 sprite schedule."""
from dataclasses import replace
from functools import lru_cache
from io import BytesIO
from math import gcd
from pathlib import Path
import hashlib

from PIL import Image

MAX_FRAMES = 300
MAX_PIXELS = 32_000_000
MIN_INTERVAL = 40  # At most 25 visible frame changes/s.
MAX_SEQUENCE = 6000
MAX_EXPORT_FRAMES = 10
SAFETY_MESSAGE = 'GIF visibile: massimo 10 fotogrammi inclusi per GIF. Lancette dei secondi e cronografo (Crono/Crono Pro) disattivati in questo stile per limitare i salti. Le impostazioni restano salvate.'


def safety_state(project):
    """A style's runtime restrictions, independent of the PC play/pause button."""
    from .motion import SECOND_SOURCES, ALL_LUA_SOURCES
    gifs=[e.id for e in project.elements if e.kind=='gif' and e.visible and not e.aod]
    sources=SECOND_SOURCES | set(ALL_LUA_SOURCES)
    return {'active':bool(gifs),'gifIds':gifs,'message':SAFETY_MESSAGE if gifs else '',
            'suppressedLayerIds':[e.id for e in project.elements if not e.aod and e.kind in ('pointer','disk','compass') and e.source in sources] if gifs else [],
            'secondHandGroupIds':[e.id for e in project.elements if not e.aod and e.kind=='analog'] if gifs else [],
            'chronographDisabled':bool(gifs)}


def safety_report(project):
    return {'policyVersion':1,'scope':'visible-normal-GIF-per-style','maximumIncludedFramesPerGif':MAX_EXPORT_FRAMES,
            'savedPreferencesPreserved':True,'aodIndependent':True,
            'styles':[{'variant':i,**safety_state(project.variant_project(i))} for i in range(max(1,len(project.variants)))]}


def runtime_project(project):
    """Apply GIF exclusions to a detached copy; retain the editable original.

    Materialize legacy style overrides before applying restrictions so an
    unaffected style never inherits the first style's exclusions.
    """
    if not any(safety_state(project.variant_project(i))['active'] for i in range(max(1,len(project.variants)))):
        return project
    result=project.copy()
    if result.variants:result.ensure_independent_variants()
    def restrict(elements):
        from .motion import SECOND_SOURCES, ALL_LUA_SOURCES
        if not any(e.kind=='gif' and e.visible and not e.aod for e in elements):return
        for e in elements:
            if e.aod:continue
            if e.kind=='analog':
                e.second_hand=e.smooth_seconds=e.chrono_pro=e.only_chrono=False
            elif e.kind in ('pointer','disk','compass') and e.source in SECOND_SOURCES | set(ALL_LUA_SOURCES):
                e.visible=False
    restrict(result.elements)
    for variant in result.variants[1:]:restrict(variant['design'].elements)
    return result


def validate_safety(project,data,record):
    """Enforce the advertised GIF restrictions against the final binary."""
    import struct
    from .watchface_library import read_tables
    from .native import inspect_binary
    from .model import SOURCES
    from .motion import SECOND_SOURCES
    from .lua_runtime import unpack_app
    if record!=safety_report(project):raise ValueError('Rapporto limitazioni GIF diverso dal progetto.')
    normal=[s for s in inspect_binary(data)['screens'] if not s['aod']]
    codes={bytes.fromhex(SOURCES[key][1]) for key in SECOND_SOURCES if key in SOURCES}
    for style,screen in zip(record['styles'],normal):
        if not style['active']:continue
        tables=read_tables(data,screen['index'])
        if any(b[3]>>4==3 and b[:2] in codes for _,_,b in tables[7]):
            raise ValueError('Lancetta secondi presente in uno stile con GIF.')
        apps={uid:unpack_app(b) for uid,_,b in tables[5]}
        for _,_,layout in tables[0]:
            app=apps.get(struct.unpack_from('<I',layout)[0])
            if app and any(token in app[1] for token in (b'require("studio_core")',b'require("studio_core_pro")')):
                raise ValueError('Cronografo attivo in uno stile con GIF.')


def export_errors(project):
    """Export policy only: oversized drafts must remain editable/saveable."""
    result=[]
    for vi in range(max(1,len(project.variants))):
        p=project.variant_project(vi)
        style=project.variants[vi]['name'] if project.variants else 'Originale'
        for e in p.elements:
            if e.kind!='gif' or e.aod or not e.visible:continue
            count=sum(f['included'] for f in e.gif_frames)
            if count>MAX_EXPORT_FRAMES:
                result.append('Stile «{style}» · GIF «{name}»: {count} fotogrammi inclusi; massimo {limit}.'.format(
                    style=style,name=e.name,count=count,limit=MAX_EXPORT_FRAMES))
    return result


def import_gif(project, path):
    from .model import Element
    path = Path(path)
    if path.suffix.lower() != '.gif':
        raise ValueError('Seleziona un file .gif.')
    pending = {}; frames = []
    with Image.open(path) as source:
        if source.format != 'GIF':
            raise ValueError('Il file selezionato non è una GIF valida.')
        count = getattr(source, 'n_frames', 1)
        if count > MAX_FRAMES or source.width * source.height * count > MAX_PIXELS:
            raise ValueError('GIF troppo grande: massimo 300 fotogrammi e 32 milioni di pixel complessivi.')
        # Pillow composes GIF deltas/disposal against the logical screen when
        # seeking sequentially. Preserve complete RGBA frames, not raw patches.
        for index in range(count):
            source.seek(index)
            bitmap = source.convert('RGBA')
            bitmap.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            raw = BytesIO(); bitmap.save(raw, 'PNG'); data = raw.getvalue()
            key = 'assets/' + hashlib.sha256(data).hexdigest()[:24] + '.png'
            pending[key] = data
            frames.append({'asset': key, 'duration': max(10, min(60000, int(source.info.get('duration', 100) or 100))), 'included': True})
        width, height = bitmap.size
    element = Element(kind='gif', name=path.stem, asset=frames[0]['asset'], gif_frames=frames,
                      color='#ffffff', tint=False, x=0, y=0,
                      width=min(480, width), height=max(1, round(height * min(480, width) / width)), fit='contain')
    if element.height > 480:
        element.width = max(1, round(element.width * 480 / element.height)); element.height = 480
    element.x=(480-element.width)//2; element.y=(480-element.height)//2
    schedule(element)
    project.assets.update(pending); project.elements.append(element)
    return element


def errors(project, e):
    result = []
    if type(e.gif_speed) is not int or not 25 <= e.gif_speed <= 400:
        result.append('Velocità GIF non valida (25–400%).')
    if not isinstance(e.gif_frames, list) or not 1 <= len(e.gif_frames) <= MAX_FRAMES:
        return result + ['GIF priva di fotogrammi o oltre il limite di 300.']
    for frame in e.gif_frames:
        if (not isinstance(frame, dict) or set(frame) != {'asset', 'duration', 'included'} or
                frame.get('asset') not in project.assets or
                type(frame.get('duration')) is not int or not 10 <= frame['duration'] <= 60000 or
                type(frame.get('included')) is not bool):
            return result + ['Fotogrammi GIF, durate o risorse non validi.']
    if not any(f['included'] for f in e.gif_frames):
        result.append('Mantieni almeno un fotogramma GIF incluso.')
    if not result:
        try: schedule(e)
        except ValueError as exc: result.append(str(exc))
    return result


def schedule(e):
    frames = [(i, f) for i, f in enumerate(e.gif_frames) if f['included']]
    if not frames: raise ValueError('Mantieni almeno un fotogramma GIF incluso.')
    durations = [max(MIN_INTERVAL, round(f['duration'] * 100 / e.gif_speed / 10) * 10) for _, f in frames]
    interval = durations[0]
    for duration in durations[1:]: interval = gcd(interval, duration)
    interval = max(MIN_INTERVAL, interval)
    sequence = []; elapsed = 0
    for (index, _), duration in zip(frames, durations):
        elapsed += duration
        repeats = max(1, round(elapsed / interval) - len(sequence))
        if len(sequence) + repeats > MAX_SEQUENCE:
            raise ValueError('Sequenza GIF troppo lunga: aumenta la velocità o riduci i fotogrammi.')
        sequence.extend([index] * repeats)
    return interval, sequence


def frame_index(e, milliseconds=0):
    interval, sequence = schedule(e)
    return sequence[int(max(0, milliseconds) // interval) % len(sequence)]


def graphic(e, milliseconds=0, index=None):
    index = frame_index(e, milliseconds) if index is None else max(0, min(len(e.gif_frames)-1, int(index)))
    return replace(e, kind='image', asset=e.gif_frames[index]['asset'])


def native_frames(project, e):
    from .render import canvas_static
    interval, sequence = schedule(e)
    bitmaps = {}
    for index in dict.fromkeys(sequence):
        pair = canvas_static(project, graphic(e, index=index))
        if pair is None: return interval, [], {}, (0, 0)
        bitmap, x, y = pair
        bitmaps[index] = bitmap
    return interval, sequence, bitmaps, (x, y)


def uses_lua(e,*,legacy=False):
    # EasyFace's image-array header stores its frame count in one byte.
    if e.kind!='gif':return False
    interval,sequence=schedule(e)
    # Native ImageArray repeats encode the bitmap again, not just a pointer.
    # Variable-delay GIFs therefore use one Lua bitmap per included frame.
    return interval>65535 or len(sequence)>255 or (not legacy and len(sequence)>len(set(sequence)))


def write_scene(project,e,directory,variant):
    base=directory/'app/lua';(base/'gfx').mkdir(parents=True,exist_ok=True)
    lines=['local lvgl = require("lvgl")',
           'local scene = lvgl.Object(nil,{x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
           'scene:clear_flag(lvgl.FLAG.SCROLLABLE)','scene:clear_flag(lvgl.FLAG.CLICKABLE)',
           *lua_lines(project,e,base,variant)]
    name=f'lua/studio_v{variant}_gif_{e.id}.lua'
    (directory/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name


@lru_cache(maxsize=600)
def thumbnail(raw):
    with Image.open(BytesIO(raw)) as source:
        source = source.convert('RGBA'); source.thumbnail((76, 60))
        result = BytesIO(); source.save(result, 'PNG')
        return result.getvalue()


def report(project,*,legacy=False,export_limit=None):
    from .lua_runtime import scene_layers
    records = []
    for vi in range(max(1, len(project.variants))):
        p = project.variant_project(vi)
        inside = {e.id for e in scene_layers(p)}
        for e in p.ordered_layers(False):
            if not hasattr(e, 'kind') or e.kind != 'gif' or not e.visible: continue
            interval, sequence = schedule(e)
            records.append({'variant': vi, 'id': e.id, 'frames': len(e.gif_frames),
                            'includedFrames': sum(f['included'] for f in e.gif_frames),
                            'sequenceLength': len(sequence), 'intervalMs': interval,
                            'cycleMs': interval * len(sequence), 'speedPercent': e.gif_speed,
                            'engine': 'shared-scene-lvgl' if e.id in inside else 'lvgl-frame-sequence' if uses_lua(e,legacy=legacy) else 'native-SpriteGroup',
                            'aod': 'static-first-included-frame'})
    result={'animations': records, 'maximumFps': 25, 'layerOrderPreserved': True,
            'originalGifEmbedded': False, 'hardwareVerified': False}
    if not legacy:result.update(encodingVersion=2,maximumIncludedFramesPerGif=MAX_EXPORT_FRAMES if export_limit is None else export_limit,duplicateBitmapEncoding=False)
    return result


def lua_lines(project, e, base, variant):
    from .paths import resource_root
    from .render import png_bytes
    from .live_data import lua_value
    interval, sequence, bitmaps, (x,y) = native_frames(project,e)
    if not sequence: return []
    (base/'studio_gif.lua').write_bytes((resource_root()/'s5studio/lua/studio_gif.lua').read_bytes())
    paths = {}
    for index, bitmap in bitmaps.items():
        name=f'v{variant}_{e.id}_gif_{index}.png'
        (base/'gfx'/name).write_bytes(png_bytes(bitmap)); paths[index+1]='gfx/'+name
    config={'id':e.id,'x':x,'y':y,'interval':interval,'frames':paths,'sequence':[i+1 for i in sequence]}
    return ['do',f'local config = {lua_value(config)}','require("studio_gif").add(scene,config)','end']


def validate_lua(project, files,*,legacy=False):
    from .lua_runtime import scene_layers
    from .paths import resource_root
    expected = []
    for vi in range(max(1,len(project.variants))):
        p=project.variant_project(vi)
        inside={e.id for e in scene_layers(p)}
        for e in p.elements:
            if e.kind!='gif' or not e.visible or e.aod or not (e.id in inside or uses_lua(e,legacy=legacy)):continue
            entry=f'lua/studio_v{vi}_scene.lua' if e.id in inside else f'lua/studio_v{vi}_gif_{e.id}.lua'
            code=files.get(entry,b'').decode('utf8')
            if 'require("studio_gif").add(scene,config)' not in code or e.id not in code:
                raise ValueError('Animazione GIF mancante nella scena condivisa: '+e.name)
            expected.append(e.id)
    if expected and files.get('lua/studio_gif.lua')!=(resource_root()/'s5studio/lua/studio_gif.lua').read_bytes():
        raise ValueError('Runtime GIF della scena mancante o alterato.')
    return expected
