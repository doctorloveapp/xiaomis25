"""Layer shadows rasterized once at export, using the same geometry as preview."""
import math
from PIL import Image,ImageFilter
from .colors import color_rgba,valid_color

SHADOW_KINDS=frozenset(('text','number','rect','circle'))
PROPERTIES={'fill_enabled','border_color','border_width','shadow_enabled','shadow_color',
            'shadow_opacity','shadow_offset_x','shadow_offset_y','shadow_blur','shadow_spread'}


def enabled(e):
    return e.kind in SHADOW_KINDS and e.shadow_enabled


def errors(e):
    result=[]
    if type(e.fill_enabled) is not bool or type(e.shadow_enabled) is not bool:
        result.append(f'{e.name}: riempimento e ombra devono essere flag.')
    if not valid_color(e.border_color) or not valid_color(e.shadow_color):
        result.append(f'{e.name}: colore cornice/ombra non valido.')
    for key,low,high in [('border_width',0,100),('shadow_opacity',0,255),
                         ('shadow_offset_x',-480,480),('shadow_offset_y',-480,480),
                         ('shadow_blur',0,40),('shadow_spread',-32,32)]:
        value=getattr(e,key)
        if type(value) is not int or not low<=value<=high:
            result.append(f'{e.name}: {key} deve essere un intero tra {low} e {high}.')
    if e.shadow_enabled and e.kind not in SHADOW_KINDS:
        result.append(f'{e.name}: ombra disponibile per forme, testo e dati live.')
    return result


def clip(pair):
    if pair is None:return None
    bitmap,x,y=pair
    left,top=max(0,x),max(0,y);right,bottom=min(480,x+bitmap.width),min(480,y+bitmap.height)
    if right<=left or bottom<=top:return None
    return bitmap.crop((left-x,top-y,right-x,bottom-y)),left,top


def layers(pair,e):
    """Separate shadow/foreground so all live glyphs stay above all shadows."""
    if pair is None:return None,None
    if not enabled(e):return None,pair
    problem=errors(e)
    if problem:raise ValueError('\n'.join(problem))
    bitmap,x,y=pair;box=bitmap.getchannel('A').getbbox()
    if box is None:return None,None
    bitmap=bitmap.crop(box);x+=box[0];y+=box[1]
    color=color_rgba(e.shadow_color,e.shadow_opacity)
    if not color[3]:return None,clip((bitmap,x,y))
    pad=math.ceil(e.shadow_blur*3)+abs(e.shadow_spread)+2
    mask=Image.new('L',(bitmap.width+pad*2,bitmap.height+pad*2))
    mask.paste(bitmap.getchannel('A'),(pad,pad))
    if e.shadow_spread:
        mask=mask.filter((ImageFilter.MaxFilter if e.shadow_spread>0 else ImageFilter.MinFilter)(abs(e.shadow_spread)*2+1))
    if e.shadow_blur:mask=mask.filter(ImageFilter.GaussianBlur(e.shadow_blur))
    shadow=Image.new('RGBA',mask.size,color[:3]+(0,))
    shadow.putalpha(mask.point(lambda a:a*color[3]//255))
    return clip((shadow,x-pad+e.shadow_offset_x,y-pad+e.shadow_offset_y)),clip((bitmap,x,y))


def merge(shadow,foreground):
    pairs=[p for p in (shadow,foreground) if p is not None]
    if not pairs:return None
    if len(pairs)==1:return pairs[0]
    left=min(x for _,x,y in pairs);top=min(y for _,x,y in pairs)
    right=max(x+im.width for im,x,y in pairs);bottom=max(y+im.height for im,x,y in pairs)
    result=Image.new('RGBA',(right-left,bottom-top))
    for bitmap,x,y in pairs:result.alpha_composite(bitmap,(x-left,y-top))
    return result,left,top
