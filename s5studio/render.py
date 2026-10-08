from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import math
import os

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps
from .model import Element, Project

SCENARIOS = {
    "Normale": dict(hour=10, minute=8, second=30, day=6, month=10, batteryPercent=82, heartRate=72, steps=8540, calories=420),
    "Mezzanotte": dict(hour=0, minute=0, second=0, day=1, month=1, batteryPercent=0, heartRate=60, steps=0, calories=0),
    "Valori alti": dict(hour=23, minute=59, second=59, day=31, month=12, batteryPercent=100, heartRate=180, steps=99999, calories=9999),
    "Dati assenti": dict(hour=12, minute=34, second=0, day=6, month=10, batteryPercent=None, heartRate=None, steps=None, calories=None),
}


@lru_cache(maxsize=128)
def system_font(size: int, bold: bool):
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in (["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]):
        if (fonts / name).exists():
            return ImageFont.truetype(str(fonts / name), size)
    return ImageFont.truetype("DejaVuSans.ttf", size)


def font_for(p: Project, e: Element):
    return ImageFont.truetype(BytesIO(p.assets[e.font_asset]), e.size) if e.font_asset else system_font(e.size, e.bold)


def rgba(e: Element):
    return (*ImageColor.getrgb(e.color), e.opacity)


def tint_image(image,color):
    """Apply the chosen hue, preserving alpha and the bitmap's shading."""
    alpha=image.getchannel('A')
    shade=ImageOps.grayscale(image)
    # Transparent padding must not affect the brightest visible pixel.
    top=max((v for v,a in zip(shade.getdata(),alpha.getdata()) if a),default=255) or 255
    channels=[shade.point(lambda v,c=c:round(min(255,v*255/top)*c/255)) for c in ImageColor.getrgb(color)]
    return Image.merge('RGBA',(*channels,alpha))


def digit_metrics(p: Project, e: Element):
    font = font_for(p, e)
    boxes = [font.getbbox(c) for c in "0123456789-."]
    width = max(b[2] - min(b[0], 0) for b in boxes) + 2
    top = min(b[1] for b in boxes)
    height = max(b[3] for b in boxes) - top + 2
    return width, height, top


def digit_image(p: Project, e: Element, char: str):
    width, height, top = digit_metrics(p, e)
    im = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(im)
    font = font_for(p, e)
    box = font.getbbox(char)
    draw.text(((width - (box[2]-box[0]))//2 - box[0], 1 - top), char, font=font, fill=rgba(e))
    return im


def number_parts(p: Project, e: Element):
    """Native numeric groups; layout is shared by preview and FPRJ exporter."""
    cw, ch, _ = digit_metrics(p, e)
    separator = None
    if e.kind in {"clock", "date"}:
        separator = ":" if e.kind == "clock" else "/"
        sw = max(8, int(font_for(p, e).getlength(separator)) + 4)
        total = 4*cw + sw
        offset = 0 if e.align == "left" else (e.width-total if e.align == "right" else (e.width-total)//2)
        y = (e.height-ch)//2
        return [("hour" if e.kind == "clock" else "day", 2, offset, y),
                ("minute" if e.kind == "clock" else "month", 2, offset + 2*cw+sw, y)], (separator, offset+2*cw, y, sw, ch)
    total = e.digits*cw
    offset = 0 if e.align == "left" else (e.width-total if e.align == "right" else (e.width-total)//2)
    return [(e.source, e.digits, offset, (e.height-ch)//2)], None


def static_image(p: Project, e: Element):
    im = Image.new("RGBA", (e.width, e.height))
    draw = ImageDraw.Draw(im)
    if e.kind == "image":
        with Image.open(BytesIO(p.assets[e.asset])) as source:
            source = source.convert("RGBA")
            if e.tint:source=tint_image(source,e.color)
            if e.fit == "cover":
                fitted = ImageOps.fit(source, im.size, method=Image.Resampling.LANCZOS)
            elif e.fit == "contain":
                fitted = ImageOps.contain(source, im.size, method=Image.Resampling.LANCZOS)
            else:
                fitted = source.resize(im.size, Image.Resampling.LANCZOS)
            if e.opacity != 255:
                fitted.putalpha(fitted.getchannel("A").point(lambda n: n*e.opacity//255))
            im.alpha_composite(fitted, ((e.width-fitted.width)//2, (e.height-fitted.height)//2))
    elif e.kind == "text":
        font = font_for(p, e)
        box = draw.textbbox((0,0), e.text, font=font)
        w,h = box[2]-box[0],box[3]-box[1]
        x = 0 if e.align == "left" else e.width-w if e.align == "right" else (e.width-w)//2
        draw.text((x-box[0], (e.height-h)//2-box[1]), e.text, font=font, fill=rgba(e))
    elif e.kind == "rect":
        draw.rounded_rectangle((0,0,e.width-1,e.height-1), radius=min(12, e.height//3), fill=rgba(e))
    elif e.kind == "circle":
        draw.ellipse((1,1,e.width-2,e.height-2), fill=rgba(e))
    return im


def canvas_image(p: Project, e: Element):
    """Rasterize only the intersection of a design image with the watch canvas.

    Logical image sizes/offsets may exceed 480. The shared preview/export window
    never allocates or sends an oversized bitmap to EasyFace/the watch.
    """
    left,top=max(0,e.x),max(0,e.y)
    right,bottom=min(480,e.x+e.width),min(480,e.y+e.height)
    if right<=left or bottom<=top:return None
    if e.width<=480 and e.height<=480:
        full=static_image(p,e)
        return full.crop((left-e.x,top-e.y,right-e.x,bottom-e.y)),left,top
    im=Image.new('RGBA',(right-left,bottom-top))
    with Image.open(BytesIO(p.assets[e.asset])) as original:
        source=original.convert('RGBA')
    if e.tint:source=tint_image(source,e.color)
    w,h=e.width,e.height
    source_box=(0.,0.,float(source.width),float(source.height))
    if e.fit=='cover':
        scale=max(w/source.width,h/source.height)
        sw,sh=w/scale,h/scale
        source_box=((source.width-sw)/2,(source.height-sh)/2,(source.width+sw)/2,(source.height+sh)/2)
    elif e.fit=='contain':
        if source.width/source.height>w/h:h=max(1,round(source.height/source.width*w))
        else:w=max(1,round(source.width/source.height*h))
    offset_x,offset_y=(e.width-w)//2,(e.height-h)//2
    x0,y0=max(left-e.x,offset_x),max(top-e.y,offset_y)
    x1,y1=min(right-e.x,offset_x+w),min(bottom-e.y,offset_y+h)
    if x1>x0 and y1>y0:
        sx0,sy0,sx1,sy1=source_box
        box=(sx0+(x0-offset_x)*(sx1-sx0)/w,sy0+(y0-offset_y)*(sy1-sy0)/h,
             sx0+(x1-offset_x)*(sx1-sx0)/w,sy0+(y1-offset_y)*(sy1-sy0)/h)
        fitted=source.resize((x1-x0,y1-y0),Image.Resampling.LANCZOS,box=box)
        if e.opacity!=255:fitted.putalpha(fitted.getchannel('A').point(lambda n:n*e.opacity//255))
        im.alpha_composite(fitted,(x0-(left-e.x),y0-(top-e.y)))
    return im,left,top


def analog_face(e: Element):
    im = Image.new("RGBA", (e.width,e.height))
    draw = ImageDraw.Draw(im)
    cx,cy=e.width//2,e.height//2
    radius = min(e.width,e.height)//2 - 5
    if not e.show_ticks:return im
    for n in range(60):
        a=math.radians(n*6-90)
        length=12 if n%5 == 0 else 4
        draw.line((cx+math.cos(a)*(radius-length),cy+math.sin(a)*(radius-length),cx+math.cos(a)*radius,cy+math.sin(a)*radius), fill=rgba(e),width=3 if n%5 == 0 else 1)
    return im


def _raw_hand(e,which,p,shadow=False):
    suffix='_shadow' if shadow else ''
    asset=getattr(e,which+suffix+'_asset')
    if not asset or p is None:return None
    with Image.open(BytesIO(p.assets[asset])) as source:im=source.convert('RGBA')
    x=getattr(e,which+suffix+'_anchor_x');y=getattr(e,which+suffix+'_anchor_y')
    return im,(im.width//2 if x<0 else x,max(0,im.height-14) if y<0 else y)


def _window_hand(im,anchor,crop):
    # Keep an external native pivot by adding transparent padding. Small hands
    # discard the source canvas padding, so length refers to the visible needle.
    bounds=im.getchannel('A').getbbox() if crop else (0,0,*im.size)
    bounds=bounds or (0,0,*im.size)
    left,top=min(bounds[0],anchor[0]),min(bounds[1],anchor[1])
    right,bottom=max(bounds[2],anchor[0]+1),max(bounds[3],anchor[1]+1)
    return im.crop((left,top,right,bottom)),(anchor[0]-left,anchor[1]-top)


def raw_hand_pivot(e,which,p):
    main=_raw_hand(e,which,p)
    if main is None:return None
    im,original=main;anchor=original
    if e.kind=='pointer' and e.pointer_end_pivot:
        mask=im.getchannel('A').point(lambda a:255 if a>=24 else 0)
        bounds=mask.getbbox() or im.getchannel('A').getbbox()
        if bounds:
            row=mask.crop((bounds[0],bounds[3]-1,bounds[2],bounds[3])).getbbox()
            anchor=(bounds[0]+(row[0]+row[2]-1)//2 if row else (bounds[0]+bounds[2]-1)//2,bounds[3]-1)
    return im,anchor


def hand_preview(e,which,p):
    """A source-coordinate editing window, never a scaled export bitmap."""
    pair=raw_hand_pivot(e,which,p)
    if pair is None:return None
    im,anchor=pair
    bounds=im.getchannel('A').getbbox() or (0,0,*im.size)
    left,top=min(bounds[0],anchor[0])-8,min(bounds[1],anchor[1])-8
    right,bottom=max(bounds[2],anchor[0]+1)+8,max(bounds[3],anchor[1]+1)+8
    im=im.crop((left,top,right,bottom))
    color=getattr(e,which+'_color')
    if color:im=tint_image(im,color)
    import base64
    return {'src':'data:image/png;base64,'+base64.b64encode(png_bytes(im)).decode(),
            'width':im.width,'height':im.height,'originX':left,'originY':top,
            'pivotX':anchor[0]-left,'pivotY':anchor[1]-top,'asset':getattr(e,which+'_asset')}


def hand_edit_changes(e,changes,p):
    changes=dict(changes)
    for hand in ('hour','minute','second'):
        if hand+'_length' in changes:changes[hand+'_length_adjusted']=True
        if hand+'_width' in changes:changes[hand+'_width_adjusted']=True
        if any(hand+'_anchor_'+a in changes for a in ('x','y')):
            if e.kind=='pointer':changes['pointer_end_pivot']=False
            main=_raw_hand(e,hand,p)
            if main and min(getattr(e,hand+'_pivot_reference_'+a) for a in ('x','y'))<0:
                for i,a in enumerate(('x','y')):changes[hand+'_pivot_reference_'+a]=main[1][i]
    return changes


def _hand_geometry(e,which,p):
    raw=_raw_hand(e,which,p)
    if raw is None:return None
    im,original=raw
    anchor=raw_hand_pivot(e,which,p)[1]
    reference=tuple(getattr(e,which+'_pivot_reference_'+axis) for axis in ('x','y'))
    if min(reference)<0:reference=original
    delta=(anchor[0]-reference[0],anchor[1]-reference[1])
    crop=e.kind=='pointer' or getattr(e,which+'_length_adjusted') or getattr(e,which+'_width_adjusted')
    main=_window_hand(im,anchor,crop)
    shadow=_raw_hand(e,which,p,True)
    if shadow:
        sim,sa=shadow
        shadow=_window_hand(sim,(sa[0]+delta[0],sa[1]+delta[1]),crop)
    sx=sy=1.
    if e.kind=='pointer':
        bounds=main[0].getchannel('A').getbbox() or (0,0,*main[0].size)
        length=max(1,main[1][1]-bounds[1])
        sx=sy=min(e.width,e.height)*e.second_length/100/length
    elif getattr(e,which+'_length_adjusted'):
        bounds=main[0].getchannel('A').getbbox() or (0,0,*main[0].size)
        length=max(1,main[1][1]-bounds[1])
        sy=min(e.width,e.height)*getattr(e,which+'_length')/100/length
    if getattr(e,which+'_width_adjusted'):
        bounds=main[0].getchannel('A').point(lambda a:255 if a>=24 else 0).getbbox()
        # Width is the widest visible part of the graphic; transparent canvas
        # padding never counts as needle thickness.
        sx=getattr(e,which+'_width')/max(1,bounds[2]-bounds[0] if bounds else main[0].width)
    pairs=[main]+([shadow] if shadow else [])
    # Bounds are enforced on actual emitted bitmaps, independently per axis.
    sx=min(sx,480/max(pair[0].width for pair in pairs))
    sy=min(sy,480/max(pair[0].height for pair in pairs))
    return main,shadow,(sx,sy)


def hand_shadow_offset(e,which,p):
    geometry=_hand_geometry(e,which,p)
    scales=geometry[2] if geometry else (1.,1.)
    return tuple(round(getattr(e,which+'_shadow_offset_'+axis)*scales[i]) for i,axis in enumerate(('x','y')))


def hand_image(e: Element, which: str, p: Project | None=None, *, shadow=False):
    if e.kind=='compass':
        if shadow:return None
        with Image.open(BytesIO(p.assets[e.asset])) as source:im=source.convert('RGBA')
        scale=min(e.width/im.width,e.height/im.height)
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
        if e.tint:im=tint_image(im,e.color)
        if e.opacity!=255:im.putalpha(im.getchannel('A').point(lambda a:a*e.opacity//255))
        return im,(im.width//2,im.height//2)
    geometry=_hand_geometry(e,which,p)
    if geometry:
        pair=geometry[1 if shadow else 0]
        if pair is None:return None
        im,anchor=pair;scales=geometry[2]
        color=getattr(e,which+'_color')
        if color and not shadow:im=tint_image(im,color)
        if e.opacity!=255:im.putalpha(im.getchannel('A').point(lambda v:v*e.opacity//255))
        if scales!=(1.,1.):
            im=im.resize(tuple(max(1,round(v*scales[i])) for i,v in enumerate(im.size)),Image.Resampling.LANCZOS)
            anchor=tuple(max(0,min(im.size[i]-1,round(v*scales[i]))) for i,v in enumerate(anchor))
        return im,anchor
    if shadow:return None
    length = int(min(e.width,e.height) * getattr(e,which+'_length')/100)
    width = getattr(e,which+'_width')
    endpoint=e.kind=='pointer' and e.pointer_end_pivot
    im = Image.new("RGBA", (width+4,length+1 if endpoint else length+14))
    color=getattr(e,which+'_color') or e.color
    ImageDraw.Draw(im).rounded_rectangle((2,1,width+1,length if endpoint else length+12),radius=width//2,fill=(*ImageColor.getrgb(color),e.opacity))
    return im, (im.width//2,length)


def element_image(p: Project, e: Element, values: dict, *, viewport=None,origin=(0,0)):
    if e.kind=='image_values':
        from dataclasses import replace
        value=values.get(e.source)
        key=str(int(value)) if value is not None else '99'
        asset=e.value_assets.get(key,e.value_assets.get('99',next(iter(e.value_assets.values()))))
        return static_image(p,replace(e,kind='image',asset=asset,fit='contain'))
    if e.kind in {"text", "image", "rect", "circle"}:
        return static_image(p,e)
    if e.kind in ('analog','pointer','compass'):
        im=Image.new('RGBA',viewport or (e.width,e.height))
        if e.kind=='analog':im.alpha_composite(analog_face(e),origin)
        cx,cy=origin[0]+e.width//2,origin[1]+e.height//2
        # Preview uses native hand raster assets, rotated around the same anchor.
        hands=[("hour",((values.get('hour') or 0)%12)*30+(values.get('minute') or 0)*0.5), ("minute",(values.get('minute') or 0)*6)]
        if e.second_hand and not e.aod:
            second=values.get('__proValues',{}).get(e.id+'_second') if e.chrono_pro else None
            if second is None:second=((values.get('second') or 0)+(values.get('__secondFraction',0) if e.smooth_seconds else int(values.get('__secondFraction',0))))%60
            hands.append(('second',second*6))
        if e.kind in ('pointer','compass'):
            from .motion import ALL_LUA_SOURCES, lua_value
            value=lua_value(e.source,values.get('__chronoMs',0) if e.source!='studioDecisecond' else values.get('__clockMs',0),e.smooth_seconds) if e.source in ALL_LUA_SOURCES else values.get(e.source)
            if e.source=='studioDecisecond':value=e.value_start+value/10*e.value_range
            if e.id in values.get('__proValues',{}):value=values['__proValues'][e.id]
            if e.smooth_seconds and e.source in ('second','timeSecond') and value is not None:value=(value+values.get('__secondFraction',0))%60
            fraction=0 if value is None else max(0,min(1,(float(value)-e.value_start)/e.value_range))
            hands=[('second',e.angle_start+fraction*e.angle_range)]
        for shadow in ([True,False] if e.show_shadows else [False]):
            for which, angle in hands:
                pair=hand_image(e,which,p,shadow=shadow)
                if pair is None:continue
                hand,anchor=pair;dx,dy=hand_shadow_offset(e,which,p) if shadow else (0,0)
                centre=(cx+dx,cy+dy)
                layer=Image.new('RGBA',im.size)
                layer.alpha_composite(hand,(centre[0]-anchor[0],centre[1]-anchor[1]))
                im.alpha_composite(layer.rotate(-angle,resample=Image.Resampling.BICUBIC,center=centre))
        if e.kind=='analog':ImageDraw.Draw(im).ellipse((cx-6,cy-6,cx+6,cy+6),fill=rgba(e))
        return im
    im = Image.new("RGBA", (e.width,e.height))
    cw,ch,_=digit_metrics(p,e)
    groups, sep = number_parts(p,e)
    for source, count, x, y in groups:
        value = values.get(source)
        if value is None:
            text = "-"*count
        else:
            if e.kind=='number' and e.decimals:
                text=f'{float(value):.{e.decimals}f}'
                if len(text)>count:text='-'*count
            else:text = str(max(-(10**(count-1)-1),min(int(value),10**count-1)))
            text = text.zfill(count) if e.leading_zero or e.kind in {"clock","date"} else text.ljust(count)
        for index,char in enumerate(text):
            if char != " ":
                im.alpha_composite(digit_image(p,e,char),(x+index*cw,y))
    if sep:
        char,x,y,w,h=sep
        font=font_for(p,e)
        box=font.getbbox(char)
        ImageDraw.Draw(im).text((x+(w-(box[2]-box[0]))//2-box[0],y+1-digit_metrics(p,e)[2]), char, font=font, fill=rgba(e))
    return im


def render(p: Project, values: dict | None = None, aod=False, circular=True):
    values = values or SCENARIOS["Normale"]
    from .complications import sample_values
    values=sample_values(values)
    im = Image.new("RGBA",(480,480),"#000000" if aod else p.background)
    from .complications import option_image
    from .motion import excluded_from_aod
    for layer in p.ordered_layers(aod):
        if isinstance(layer,Element):
            if layer.visible and not (aod and excluded_from_aod(layer)):
                if layer.kind=='image':
                    clipped=canvas_image(p,layer)
                    if clipped:bitmap,x,y=clipped;im.alpha_composite(bitmap,(x,y))
                elif layer.kind in ('analog','pointer','compass'):
                    # Native hands use the level centre as their pivot, but
                    # their bitmap is clipped by the watch canvas, not the
                    # editor's selection box. Rotate on that same full canvas.
                    im.alpha_composite(element_image(p,layer,values,viewport=im.size,origin=(layer.x,layer.y)))
                else:im.alpha_composite(element_image(p,layer,values),(layer.x,layer.y))
        elif layer['visible']:
            choice=values.get('__choices',{}).get(layer['id'],layer['default'])
            im.alpha_composite(option_image(layer,choice if choice in layer['options'] else layer['default'],values),(layer['x'],layer['y']))
    if circular:
        mask=Image.new('L',(480,480))
        ImageDraw.Draw(mask).ellipse((0,0,479,479),fill=255)
        im.putalpha(mask)
    return im


def png_bytes(im: Image.Image) -> bytes:
    out=BytesIO()
    im.save(out,'PNG')
    return out.getvalue()


def layout_errors(p: Project) -> list[str]:
    errors = []
    for e in p.elements:
        if not e.visible:
            continue
        if e.kind in {"number","clock","date"}:
            cw,ch,_=digit_metrics(p,e)
            groups,sep=number_parts(p,e)
            if any(x<0 or y<0 or x+n*cw>e.width or y+ch>e.height for _,n,x,y in groups):
                errors.append(f"{e.name}: aumenta larghezza/altezza o riduci la dimensione del font.")
        elif e.kind == 'text':
            box=font_for(p,e).getbbox(e.text)
            if box[2]-box[0]>e.width or box[3]-box[1]>e.height:
                errors.append(f"{e.name}: il testo non entra nello spazio assegnato.")
        if e.kind!='image' and (e.x+e.width>480 or e.y+e.height>480):
            errors.append(f"{e.name}: il componente supera i bordi del canvas.")
    return errors
