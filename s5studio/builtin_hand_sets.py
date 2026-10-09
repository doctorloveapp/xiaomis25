"""Expose every original catalog graphic as an editable set, preserving IDs."""
from copy import deepcopy
import hashlib
from pathlib import Path

from PIL import Image

from .catalog_labels import display_preset


def group_library(presets):
    groups={}
    for preset in presets:
        # Sensor indicators may reference a main clock set. They remain independent.
        key=(preset['small'],preset['aod'],tuple(sorted(preset.get('setMembers',{}).values())) if preset['hand']!='indicator' else ())
        if not key[2]:key=(*key,preset['id'])
        groups.setdefault(key,[]).append(preset)
    result=[]
    for items in groups.values():
        first=display_preset(items[0]);members={('second' if p['hand']=='indicator' else p['hand']):p['id'] for p in items}
        if len(members)!=len(items):raise ValueError('Ruoli duplicati nel catalogo originale.')
        digest=hashlib.sha256('|'.join(sorted(p['id'] for p in items)).encode()).hexdigest()[:16]
        name=' · '.join(str(v) for v in (first['name'],first['theme'],first['variant'],
                            'Small' if first['small'] else 'Main','AOD' if first['aod'] else '') if v)
        name=name[:70]+' · '+digest[:6]
        result.append({'id':'builtin-'+digest,'name':name,'small':first['small'],
                       'hands':{role:deepcopy(next(p for p in items if p['id']==identity)) for role,identity in members.items()},
                       'origin':{'kind':'library','members':members}})
    return result


def import_original(catalog,record):
    """Copy only a set being edited; retain transparent space and external pivots."""
    record=deepcopy(record)
    def copy(item):
        path=(catalog.resources/item['assetPath']).resolve()
        if not path.is_relative_to((catalog.resources/'data/hand-presets').resolve()):raise ValueError('Percorso del catalogo originale non valido.')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sourceSha256']:raise ValueError('PNG originale alterata.')
        with Image.open(path) as source:image=source.convert('RGBA')
        x,y=item['pivot'];left=max(0,-x);top=max(0,-y)
        size=(max(image.width+left,x+left+1),max(image.height+top,y+top+1))
        if max(size)>480:raise ValueError('Pivot originale fuori dal campo supportato.')
        if size!=image.size:
            padded=Image.new('RGBA',size);padded.paste(image,(left,top));image=padded
        return catalog._store_image(image,Path(item.get('path',path.name)).name,[x+left,y+top],item.get('offset',[0,0]))
    for role,item in record['hands'].items():
        mother=copy(item)
        if item.get('shadow'):mother['shadow']=copy(item['shadow'])
        record['hands'][role]=mother
    return record
