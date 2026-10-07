"""Example project for the unified layer editor and small independent hands."""
from pathlib import Path
from io import BytesIO
import hashlib,sys,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from s5studio.model import Project,Element,normalized_slot
from s5studio.render import render,png_bytes
p=Project.load(ROOT/'projects/S5_Analogico_Libero_0.5.s5faceproj')
p.name='S5 Studio Crono';p.face_id='706006001';p.background='#090f1b'
for e in p.elements:
    if e.kind=='analog' and not e.aod:
        e.x=e.y=24;e.width=e.height=432;e.hour_length=25;e.minute_length=39;e.second_length=43
        e.hour_color='#f5f2eb';e.minute_color='#82eac5';e.second_color='#ff798a'
    if e.name=='Firma':e.text='S5 STUDIO';e.y=78;e.size=16;e.color='#cad4e4'
    if e.kind=='date' and not e.aod:e.y=418;e.size=19
# This original bitmap is an image layer: its opacity can be edited in Studio.
back=Image.new('RGBA',(480,480));draw=ImageDraw.Draw(back)
for cx,cy in [(162,218),(318,218),(240,337)]:
    draw.ellipse((cx-54,cy-54,cx+54,cy+54),fill='#101b2a',outline='#33465c',width=2)
    for n in range(12):
        a=math.radians(n*30-90);draw.line((cx+math.cos(a)*45,cy+math.sin(a)*45,cx+math.cos(a)*49,cy+math.sin(a)*49),fill='#728198',width=1)
raw=png_bytes(back);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw
background=Element(kind='image',name='Sottoquadranti (immagine)',asset=key,x=0,y=0,width=480,height=480,fit='contain',opacity=210)
p.elements.insert(0,background)
for name,x,y,source,range_value,col in [('Secondi piccoli',108,164,'second',60,'#ff798a'),('Minuti piccoli',264,164,'minute',60,'#82eac5'),('Batteria piccola',186,283,'batteryPercent',100,'#f4c780')]:
    p.elements.append(Element(kind='pointer',name=name,x=x,y=y,width=108,height=108,source=source,value_range=range_value,color=col,second_length=40,second_width=3))
for slot,(x,y,w,default) in zip(p.complications,[(70,122,140,'healthStepCount'),(270,122,140,'healthHeartRate'),(38,276,118,'weatherCurrentTemperature'),(324,276,118,'systemSensorCompass'),(180,383,120,'systemStatusBattery')]):
    slot.update(x=x,y=y,width=w,height=32,size=22,frame='none',showLabel=False,showUnit=False,weatherMode='value',default=default)
# Image and small hands behind the main hands; values above all hands.
p.layer_order=[background.id]+[e.id for e in p.elements if e.kind=='pointer' and not e.aod]+[e.id for e in p.elements if e.id!=background.id and e.kind!='pointer' and not e.aod]+[s['id'] for s in p.complications]+[e.id for e in p.elements if e.aod]
path=ROOT/'projects/S5_Studio_Crono_0.6.s5faceproj';p.save(path,png_bytes(render(p.variant_project(0))))
for i in range(5):(ROOT/'docs/screenshots'/f'S5-Studio-Crono-0.6-stile-{i+1}.png').write_bytes(png_bytes(render(p.variant_project(i))))
print(path)
