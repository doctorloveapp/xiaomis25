from io import BytesIO
from pathlib import Path
import hashlib,struct,xml.etree.ElementTree as ET,zipfile
import pytest
from PIL import Image,ImageDraw,ImageChops
from s5studio.model import Project,Element,template,normalized_slot
from s5studio.render import static_image,element_image,hand_image,render,png_bytes
from s5studio.complications import option_project,option_image
from s5studio.native import build,generate_fprj
from s5studio.watchface_library import read_tables
ROOT=Path(__file__).resolve().parents[1]

def raw_slot(key='slot',**changes):
    return normalized_slot({'id':key,'name':key,'x':100,'y':100,'width':100,'height':40,'size':28,
                            'options':['none','steps'],'default':'steps','frame':'none',
                            'showLabel':False,'showUnit':False,'weatherMode':'value',**changes})

def test_layer_order_changes_composite_and_survives_save(tmp_path):
    p=Project(background='#000000');cover=Element(kind='rect',x=100,y=100,width=100,height=40,color='#ff0000')
    p.elements=[cover];p.complications=[raw_slot()];p.layer_order=['slot',cover.id]
    behind=render(p,circular=False)
    assert behind.getpixel((130,120))[:3]==(255,0,0)
    p.layer_order=[cover.id,'slot'];front=render(p,circular=False)
    assert ImageChops.difference(front,behind).convert('RGB').getbbox() is not None
    p.save(tmp_path/'ordered.s5faceproj');loaded=Project.load(tmp_path/'ordered.s5faceproj')
    assert loaded.layer_order==p.layer_order and render(loaded).tobytes()==render(p).tobytes()

def test_old_slot_appearance_and_new_value_only():
    legacy=normalized_slot(dict(id='old',name='old',x=10,y=10,options=['steps'],default='steps'))
    assert legacy['frame']=='rounded' and legacy['showLabel'] and legacy['showUnit']
    p=option_project(raw_slot(),'steps')
    assert len(p.elements)==1 and p.elements[0].kind=='number'
    assert option_image(raw_slot(),'steps',{'steps':1234}).getpixel((0,0))[3]==0
    assert option_image(raw_slot(),'none',{}).getbbox() is None

@pytest.mark.parametrize('percentage',[0,1,25,50,99,100])
def test_opacity_matches_preview_and_exported_asset(tmp_path,percentage):
    p=Project();raw=png_bytes(Image.new('RGBA',(20,10),(200,100,50,255)))
    key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw
    alpha=round(percentage*255/100);e=Element(kind='image',asset=key,width=100,height=50,opacity=alpha);p.elements=[e]
    assert static_image(p,e).getpixel((20,20))[3]==alpha
    source=generate_fprj(p,tmp_path)
    widget=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')[1]
    with Image.open(source.project_path.parent/'images'/widget.get('Bitmap')) as im:
        assert im.getpixel((20,20))[3]==alpha

def test_per_hand_colours_and_tint_preserve_source_and_alpha():
    p=Project();e=Element(kind='analog',hour_color='#ff0000',minute_color='#00ff00',second_color='#0000ff')
    for hand,colour in [('hour',(255,0,0)),('minute',(0,255,0)),('second',(0,0,255))]:
        im,_=hand_image(e,hand,p);assert im.getpixel((2,10))[:3]==colour
    im=Image.new('RGBA',(8,20),(180,180,180,77));raw=png_bytes(im)
    key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw;e.hour_asset=key
    tinted,_=hand_image(e,'hour',p)
    assert tinted.getpixel((0,0))==(255,0,0,77) and p.assets[key]==raw
    e.hour_color='';assert hand_image(e,'hour',p)[0].tobytes()==im.tobytes()

def test_pointer_preview_scaled_asset_and_rotation():
    p=Project();e=Element(kind='pointer',source='batteryPercent',width=100,height=100,
                         value_range=100,angle_start=-90,angle_range=180,second_width=3,color='#ffffff')
    left=element_image(p,e,{'batteryPercent':0});right=element_image(p,e,{'batteryPercent':100})
    assert left.getbbox()[0]<50 and right.getbbox()[2]>50 and left.tobytes()!=right.tobytes()
    image=Image.new('RGBA',(20,220));ImageDraw.Draw(image).line((10,1,10,210),fill='white',width=4)
    raw=png_bytes(image);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw
    e.second_asset=key;e.second_anchor_x=10;e.second_anchor_y=200;e.second_length=40;e.pointer_end_pivot=False
    hand,anchor=hand_image(e,'second',p)
    assert anchor[1]==40 and hand.height<100 and p.assets[key]==raw

@pytest.mark.integration
def test_native_reordered_raw_slots_pointer_ranges_and_aod(tmp_path):
    p=template('Analogico');p.elements=[e for e in p.elements if e.kind=='analog'];p.variants=p.variants[:1]
    hand=Element(kind='pointer',name='Batteria piccola',source='batteryPercent',x=100,y=250,width=100,height=100,
                 value_range=100,angle_start=-152,angle_range=304,color='#ef9876',second_width=3)
    aod=Element(kind='pointer',name='Batteria AOD',source='batteryPercent',aod=True,x=100,y=250,width=100,height=100,value_range=100)
    cover=Element(kind='rect',name='Copertura',x=100,y=100,width=100,height=40,color='#ffffff',opacity=128)
    p.elements.extend([hand,aod,cover]);p.complications=[raw_slot('first'),raw_slot('second',x=270)]
    # Reversed slot layout order must also pass semantic ZIP validation.
    p.layer_order=[p.elements[0].id,'second',cover.id,'first',hand.id,p.elements[1].id,aod.id]
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(output/'resource.bin').read_bytes();tables=read_tables(data)
    targets=[struct.unpack_from('<I',b)[0] for _,_,b in tables[0]]
    slots=[uid for uid,_,_ in tables[8]]
    assert targets.index(slots[1])<targets.index(slots[0])
    assert targets.index(slots[0])-targets.index(slots[1])==2
    for uid,_,payload in tables[9]:
        count=struct.unpack_from('<H',payload,40)[0];child=struct.unpack_from('<I',payload,48)[0]
        # Numeric choices contain one dynamic child; None one transparent image.
        assert count==1 and any(child==u for index in (2,7) for u,_,_ in tables[index])
    pointer=next(b for _,_,b in tables[7] if b[:2]==bytes.fromhex('0841'))
    assert struct.unpack_from('<II',pointer,12)==(0,100<<8)
    assert struct.unpack_from('<hh',pointer,24)==(-1520,3040)
    apointer=next(b for _,_,b in read_tables(data,1)[7] if b[:2]==bytes.fromhex('0841'))
    assert struct.unpack_from('<II',apointer,12)==(0,100<<8)
    with zipfile.ZipFile(next(output.glob('*_TEMPLATE.zip'))) as z:
        m=ET.fromstring(z.read('resources/manifest.xml'))
        assert any(w.get('valueRange')=='100' and w.get('source')=='systemStatusBattery' for w in m.iter('DataItemPointer'))
