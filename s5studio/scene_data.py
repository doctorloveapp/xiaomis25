"""Keep native-source pointers and calendar labels live inside a chrono scene."""
from .calendar_labels import labels_for
from .complications import ALIASES
from .paths import resource_root
from .live_data import lua_value


def supported(e):
    from .model import SOURCES
    return bool(labels_for(e)) or (e.kind in ('pointer','compass','disk') and
        not (e.kind=='disk' and e.disk_mode=='values') and e.source in SOURCES)


def config(e):
    result={'id':e.id,'source':ALIASES.get(e.source,e.source)}
    if not labels_for(e):
        result.update(valueStart=e.value_start,valueRange=e.value_range,
                      angleStart=e.angle_start,angleRange=e.angle_range,
                      smooth=e.smooth_seconds and result['source']=='timeSecond')
    return result


def lines(project,e,base,variant):
    from .lua_runtime import pointer_lines
    from .render import calendar_image,canvas_static,png_bytes
    (base/'studio_scene_data.lua').write_bytes((resource_root()/'s5studio/lua/studio_scene_data.lua').read_bytes())
    settings=config(e)
    if labels_for(e):
        choices={}
        for value,word in labels_for(e).items():
            pair=canvas_static(project,e,calendar_image(project,e,word))
            if not pair:continue
            bitmap,x,y=pair;name=f'v{variant}_{e.id}_calendar_{value}.png'
            (base/'gfx'/name).write_bytes(png_bytes(bitmap))
            choices[value]={'x':x,'y':y,'src':'gfx/'+name}
        return ['do',f'local config = {lua_value(settings)}',
                f'config.choices = {lua_value(choices)}',
                'require("studio_scene_data").images(scene,config)','end']
    scale=max(1,min(1000,65535//max(1,e.value_start+e.value_range))) if settings['smooth'] else 1
    settings['scale']=scale
    return ['do',f'local config = {lua_value(settings)}',
            'local root = lvgl.Object(scene, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
            'root:clear_flag(lvgl.FLAG.SCROLLABLE)','root:clear_flag(lvgl.FLAG.CLICKABLE)','local hands = {}',
            *pointer_lines(project,e,base,variant,value_scale=scale),
            'require("studio_scene_data").pointer(root,hands,config)','end']


def validate_injection(project,files):
    from .lua_runtime import scene_layers
    from .motion import lua_element
    import hashlib
    records=[]
    for i in range(max(1,len(project.variants))):
        p=project.variant_project(i)
        for e in scene_layers(p):
            if lua_element(e) or not supported(e):continue
            name=f'lua/studio_v{i}_scene.lua'
            settings=config(e)
            if not labels_for(e):
                settings['scale']=max(1,min(1000,65535//max(1,e.value_start+e.value_range))) if settings['smooth'] else 1
            code=files.get(name,b'').decode('utf8').replace('\r\n','\n')
            marker='local config = '+lua_value(settings)+'\n'
            if code.count(marker)!=1:raise ValueError('Binding dinamico della scena diverso dal progetto: '+e.name)
            records.append({'variant':i,'entry':name,'kind':'calendar' if labels_for(e) else 'pointer',**settings})
    if not records:return None
    expected=(resource_root()/'s5studio/lua/studio_scene_data.lua').read_bytes()
    if files.get('lua/studio_scene_data.lua')!=expected:raise ValueError('Runtime dei dati dinamici della scena mancante o alterato.')
    return {'injected':True,'runtime':'studio_scene_data.lua','moduleSha256':hashlib.sha256(expected).hexdigest(),
            'updates':'dataman-Q8-notifications','sampleValuesBaked':False,'layerOrderPreserved':True,
            'civilTimeDecoding':'floor-Q8-whole-counters','civilSecondsAnimation':{
                'repeatCount':1,'carrier':'dedicated-transparent-child','restart':'stop-then-start-on-second-change',
                'durationMs':1000,'pollingTimer':False,'stopsInAod':True},
            'chronoIndependent':True,'hardwareVerified':False,'bindings':records}
