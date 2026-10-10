"""Opt-in civil hour/minute hands: seconds-driven, with no animation timer."""
from pathlib import Path
from .paths import resource_root


def civil_entry(e,hand,variant):
    return f'lua/studio_v{variant}_civil_{e.id}_{hand}.lua'


def civil_roles(e):
    if e.kind!='analog' or e.aod or not e.visible or e.chrono_pro and e.second_hand:return []
    return [hand for hand,enabled in [('hour',e.smooth_hours),('minute',e.smooth_minutes)] if enabled]


def write_civil_hand(project,e,hand,directory,variant):
    from .lua_runtime import pro_views,pointer_lines
    base=Path(directory)/'app/lua';(base/'gfx').mkdir(parents=True,exist_ok=True)
    for module in ('studio_civil_hand','studio_civil_clock'):
        (base/(module+'.lua')).write_bytes((resource_root()/('s5studio/lua/'+module+'.lua')).read_bytes())
    view=pro_views(e)[('hour','minute','second').index(hand)]
    lines=['local lvgl = require("lvgl")','local civil = require("studio_civil_hand")',
           'local widgets = debug.getregistry()["widgets"].__index',
           'local root = lvgl.Object(nil, {x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})',
           'root:clear_flag(lvgl.FLAG.SCROLLABLE)','root:clear_flag(lvgl.FLAG.CLICKABLE)',
           'local hands = {}']
    # Keep the original analog bitmap dimensions, pivots and shadow offsets.
    lines+=pointer_lines(project,view,base,variant,value_scale=3600 if hand=='hour' else 60,graphic=e,hand=hand)
    lines += [f'civil.bind(root, hands, "{hand}")']
    name=civil_entry(e,hand,variant)
    (Path(directory)/'app'/name).write_text('\n'.join(lines)+'\n',encoding='utf8')
    return name
