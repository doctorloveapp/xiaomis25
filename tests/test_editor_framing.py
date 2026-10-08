from io import BytesIO
from pathlib import Path
import hashlib,json,os,struct,xml.etree.ElementTree as ET,zipfile
import pytest
from PIL import Image,ImageChops
from s5studio.model import Project,Element,template
from s5studio.render import canvas_image,render,png_bytes,layout_errors
from s5studio.native import generate_fprj,build
from s5studio.watchface_library import read_tables
ROOT=Path(__file__).resolve().parents[1]

def image_project(**changes):
    im=Image.new('RGBA',(620,500))
    im.putdata([(x%256,y%256,(x+y)%256,120+(x+y)%136) for y in range(500) for x in range(620)])
    raw=png_bytes(im);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
    p=Project(background='#000000');p.assets[key]=raw
    e=Element(kind='image',asset=key,x=-140,y=-80,width=720,height=600,**changes);p.elements=[e]
    return p,e,im

@pytest.mark.parametrize('fit',['cover','contain','stretch'])
def test_crop_matches_full_image_without_rescaling_viewport(tmp_path,fit):
    from PIL import ImageOps
    p,e,original=image_project(fit=fit,opacity=196)
    assert not p.validate() and not layout_errors(p)
    full=Image.new('RGBA',(e.width,e.height))
    fitted=ImageOps.fit(original,full.size,method=Image.Resampling.LANCZOS) if fit=='cover' else ImageOps.contain(original,full.size,method=Image.Resampling.LANCZOS) if fit=='contain' else original.resize(full.size,Image.Resampling.LANCZOS)
    fitted.putalpha(fitted.getchannel('A').point(lambda v:v*196//255))
    full.alpha_composite(fitted,((e.width-fitted.width)//2,(e.height-fitted.height)//2))
    expected=full.crop((140,80,620,560));crop,x,y=canvas_image(p,e)
    assert (x,y)==(0,0) and crop.size==(480,480)
    # A source-window resize can round premultiplied RGBA by two levels;
    # its spatial mapping must match a full resize followed by clipping.
    assert max(hi for lo,hi in ImageChops.difference(crop,expected).getextrema())<=2
    source=generate_fprj(p,tmp_path)
    w=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')[1]
    assert (int(w.get('X')),int(w.get('Y')),int(w.get('Width')),int(w.get('Height')))==(0,0,480,480)
    with Image.open(tmp_path/'images'/w.get('Bitmap')) as im:assert im.tobytes()==crop.tobytes()
    p.save(tmp_path/'framing.s5faceproj');q=Project.load(tmp_path/'framing.s5faceproj')
    assert q.elements[0].x==-140 and q.elements[0].width==720
    assert q.assets==p.assets and render(q).tobytes()==render(p).tobytes()

def test_partial_and_fully_offscreen_images(tmp_path):
    p,e,_=image_project();e.x=300;e.y=-500
    crop,x,y=canvas_image(p,e)
    assert (x,y,crop.size)==(300,0,(180,100))
    source=generate_fprj(p,tmp_path/'partial');w=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')[1]
    assert (w.get('X'),w.get('Y'),w.get('Width'),w.get('Height'))==('300','0','180','100')
    e.x=700;assert canvas_image(p,e) is None and not p.validate()
    source=generate_fprj(p,tmp_path/'outside')
    assert len(ET.parse(source.project_path).getroot().find('Screen').findall('Widget'))==1

def test_maximum_image_design_geometry_uses_small_window():
    p,e,_=image_project();e.x=e.y=-1800;e.width=e.height=4096
    assert not p.validate() and canvas_image(p,e)[0].size==(480,480)
    e.width=4097;assert p.validate()
    e.width=4096;e.x=-4097;assert p.validate()

@pytest.mark.integration
def test_real_compile_crop_and_keep_original_project(tmp_path):
    p,e,_=image_project(fit='stretch');p.name='S5 Ritaglio';p.elements+=[next(e for e in template('Digitale').elements if e.kind=='clock')]
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    t=read_tables((output/'resource.bin').read_bytes())
    for uid,_,payload in t[2]+t[3]:
        w,h=struct.unpack_from('<HH',payload,4);assert w<=480 and h<=480
    with zipfile.ZipFile(next(output.glob('*_TEMPLATE.zip'))) as z:
        m=ET.fromstring(z.read('resources/manifest.xml'))
        assert all(0<=int(n.get('x'))<480 and 0<=int(n.get('y'))<480 for n in m.iter('Layout'))
    q=Project.load(next(output.glob('*.s5faceproj')))
    assert q.elements[0].width==720 and q.elements[0].x==-140 and q.assets[e.asset]==p.assets[e.asset]

@pytest.fixture
def bridge():
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);owner=QObject()
    b=StudioBridge(owner,smoke=True)
    yield b
    b.timer.stop()

def command(b,action,**kw):
    result=json.loads(b.command(json.dumps({'action':action,**kw})))
    assert 'error' not in result,result.get('error')
    return result

def test_keyboard_nudges_accumulate_and_undo_with_variant(bridge):
    b=bridge;e=b.project.elements[0];original=e.x
    for _ in range(5):command(b,'nudge',id=e.id,dx=1,dy=0)
    assert b.element({'id':e.id}).x==original+5
    command(b,'undo');assert b.element({'id':e.id}).x==original+4
    command(b,'add-variant');command(b,'edit',id=e.id,variantOnly=True,changes={'x':100})
    command(b,'nudge',id=e.id,variantOnly=True,dx=-10,dy=1)
    assert b.project.variant_project(1).elements[0].x==90 and b.project.elements[0].x==original+4
    assert b.element({'id':e.id}).x==90
    assert b.project.variant_project(1).elements[0].y==e.y+1

def test_nudge_images_beyond_canvas_and_locked_slot(bridge):
    b=bridge;p,e,_=image_project();b.project=p
    command(b,'nudge',id=e.id,dx=-10,dy=-1)
    assert (b.project.elements[0].x,b.project.elements[0].y)==(-150,-81)
    command(b,'add-slot');s=b.project.complications[0];x=s['x']
    command(b,'nudge',id=s['id'],dx=10,dy=1)
    assert s['x']==x+10
    command(b,'edit-slot',id=s['id'],changes={'locked':True});command(b,'nudge',id=s['id'],dx=10,dy=0)
    assert b.layer(s['id'])['x']==x+10


def test_image_geometry_in_variant_is_checked_and_clipped():
    p,e,_=image_project();p.variants[0]['overrides']={e.id:{'width':1000,'height':1000,'x':-200,'y':-250}}
    assert not p.validate()
    resolved=p.variant_project(0);assert canvas_image(resolved,resolved.elements[0])[0].size==(480,480)
    p.variants[0]['overrides'][e.id]['width']=4097
    assert p.validate()


def test_nudge_is_local_to_the_style_and_aod_remains_common_and_locked(bridge):
    b=bridge;e=b.project.elements[0];x=e.x
    command(b,'add-variant');command(b,'edit',id=e.id,variantOnly=True,changes={'x':100})
    command(b,'nudge',id=e.id,dx=-10,dy=0)
    assert b.element({'id':e.id}).x==90 and b.project.elements[0].x==x
    aod=next(e for e in b.project.elements if e.aod);command(b,'aod',value=True)
    y=aod.y;command(b,'nudge',id=aod.id,variantOnly=True,dx=0,dy=1)
    assert b.element({'id':aod.id}).y==y+1
    command(b,'edit',id=aod.id,changes={'locked':True});before=b.project.metadata();history=len(b.undo_stack)
    command(b,'nudge',id=aod.id,dx=10,dy=0)
    assert b.project.metadata()==before and len(b.undo_stack)==history
