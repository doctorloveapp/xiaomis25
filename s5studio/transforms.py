"""Compile-time graphic transforms, shared by preview, native assets and Lua scenes.

Positive rotation is clockwise; positive arc bends the ends below the centre.
The output is always clipped to the 480 px watch canvas. Sensors are never baked.
"""
from functools import lru_cache
from io import BytesIO
import math
from PIL import Image,ImageChops

KINDS=frozenset(('image','image_values','text','rect','circle'))


def active(e):
    return e.kind in KINDS and bool(e.rotation or e.arc)


def errors(e):
    result=[]
    for key,limit in (('rotation',360),('arc',270)):
        value=getattr(e,key)
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>limit:
            result.append(f'{e.name}: {key} deve essere un numero tra {-limit} e {limit} gradi.')
    if result:return result
    if (e.rotation or e.arc) and e.kind not in KINDS:
        result.append(f'{e.name}: rotazione e arco sono disponibili per testi, immagini e forme.')
    if e.arc and type(e.width) is int and type(e.height) is int and e.width>0:
        if abs(math.radians(e.arc))*e.height>=1.9*e.width:
            result.append(f'{e.name}: riduci l’arco oppure l’altezza per evitare che la grafica si ripieghi su sé stessa.')
    return result


def forward(x,y,w,h,rotation,arc):
    u,v=x-w/2,y-h/2
    k=math.radians(arc)/w
    if k:
        angle=k*u;r=1/k
        u,v=(r-v)*math.sin(angle),r-(r-v)*math.cos(angle)
    a=math.radians(rotation);c,s=math.cos(a),math.sin(a)
    return c*u-s*v,s*u+c*v


def bounds(e,clip=True):
    cx,cy=e.x+e.width/2,e.y+e.height/2
    points=[]
    for i in range(65):
        t=i/64
        for x,y in ((e.width*t,0),(e.width*t,e.height),(0,e.height*t),(e.width,e.height*t)):
            u,v=forward(x,y,e.width,e.height,e.rotation,e.arc);points.append((cx+u,cy+v))
    left=math.floor(min(x for x,y in points))-2;top=math.floor(min(y for x,y in points))-2
    right=math.ceil(max(x for x,y in points))+2;bottom=math.ceil(max(y for x,y in points))+2
    return (max(0,left),max(0,top),min(480,right),min(480,bottom)) if clip else (left,top,right,bottom)


@lru_cache(maxsize=32)
def mesh(x,y,w,h,rotation,arc,left,top,right,bottom):
    cx,cy=x+w/2,y+h/2;a=math.radians(rotation);c,s=math.cos(a),math.sin(a)
    k=math.radians(arc)/w
    def inverse(px,py):
        dx,dy=px-cx,py-cy;u,v=c*dx+s*dy,-s*dx+c*dy
        if k:
            r=1/k;sign=1 if r>0 else -1
            angle=math.atan2(sign*u,sign*(r-v))
            u,v=angle/k,r-sign*math.hypot(u,r-v)
        return u+w/2,v+h/2
    output=[]
    for py in range(top,bottom,8):
        for px in range(left,right,8):
            x1,y1=min(px+8,right),min(py+8,bottom)
            quad=tuple(value for point in ((px,py),(px,y1),(x1,y1),(x1,py)) for value in inverse(*point))
            output.append(((px-left,py-top,x1-left,y1-top),quad))
    return tuple(output)


def raster(p,e):
    """Return a transformed (bitmap, x, y), with no oversized fitted canvas."""
    from .render import static_image,tint_image
    problem=errors(e)
    if problem:raise ValueError('\n'.join(problem))
    left,top,right,bottom=bounds(e)
    if right<=left or bottom<=top:return None
    sx=sy=1.;ox=oy=0.
    if e.kind=='image':
        with Image.open(BytesIO(p.assets[e.asset])) as source:source=source.convert('RGBA')
        if e.tint:source=tint_image(source,e.color)
        if e.opacity!=255:source.putalpha(source.getchannel('A').point(lambda a:a*e.opacity//255))
        sx,sy=e.width/source.width,e.height/source.height
        if e.fit!='stretch':sx=sy=max(sx,sy) if e.fit=='cover' else min(sx,sy)
        ox,oy=(e.width-source.width*sx)/2,(e.height-source.height*sy)/2
    else:source=static_image(p,e)
    logical=mesh(e.x,e.y,e.width,e.height,e.rotation,e.arc,left,top,right,bottom)
    mapped=[];masks=[]
    for box,quad in logical:
        mapped.append((box,tuple((value-(ox if i%2==0 else oy))/(sx if i%2==0 else sy) for i,value in enumerate(quad))))
        masks.append((box,tuple(value*2/(e.width if i%2==0 else e.height) for i,value in enumerate(quad))))
    size=(right-left,bottom-top)
    bitmap=source.transform(size,Image.Transform.MESH,mapped,Image.Resampling.BICUBIC)
    mask=Image.new('L',(2,2),255).transform(size,Image.Transform.MESH,masks,Image.Resampling.NEAREST)
    bitmap.putalpha(ImageChops.multiply(bitmap.getchannel('A'),mask))
    return bitmap,left,top
