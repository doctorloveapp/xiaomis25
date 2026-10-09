"""Focused 1.5 checks: transformed graphics, native bindings and editor actions."""
import hashlib,json,math,os,re,struct,zipfile
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import Image,ImageDraw
from s5studio.model import Project,Element,template
from s5studio.render import canvas_static,canvas_image,render,png_bytes
from s5studio.transforms import bounds
from s5studio.native import generate_fprj,build,inspect_binary
from s5studio.semantic_package import validate_package
from s5studio.watchface_library import library,read_tables
from s5studio.catalog_labels import display_preset

ROOT=Path(__file__).resolve().parents[1]


def asset(project,image):
    raw=png_bytes(image);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
    project.assets[key]=raw;return key


def test_clockwise_rotation_and_clipping_preserve_source():
    p=Project();im=Image.new('RGBA',(40,20),'red');ImageDraw.Draw(im).rectangle((20,0,39,19),fill='blue')
    e=Element(kind='image',asset=asset(p,im),x=100,y=100,width=40,height=20,fit='stretch',rotation=90)
    before=dict(p.assets);p.elements=[e];result=render(p,circular=False)
    assert result.getpixel((120,95))[:3]==(255,0,0)
    assert result.getpixel((120,125))[:3]==(0,0,255)
    assert canvas_static(p,e)[0].size==(24,44) and p.assets==before
    e.x=470;e.rotation=35
    bitmap,x,y=canvas_static(p,e);assert 0<=x<480 and x+bitmap.width<=480 and y+bitmap.height<=480


@pytest.mark.parametrize('arc',[90,-90])
def test_arc_direction_and_first_preview_match_export(tmp_path,arc):
    p=Project();e=Element(kind='rect',x=160,y=160,width=160,height=20,color='#ff0000',arc=arc);p.elements=[e]
    bitmap,x,y=canvas_static(p,e)
    if arc>0:assert y+bitmap.height>e.y+e.height
    else:assert y<e.y
    source=generate_fprj(p,tmp_path);widget=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')[1]
    with Image.open(source.project_path.parent/'images'/widget.get('Bitmap')) as exported:
        assert exported.tobytes()==bitmap.tobytes()
    assert int(widget.get('X'))==x and int(widget.get('Y'))==y
    expected=Image.new('RGBA',(480,480),p.background);expected.alpha_composite(bitmap,(x,y))
    assert render(p,circular=False).tobytes()==expected.tobytes()


@pytest.mark.parametrize('fit',['cover','contain','stretch'])
def test_large_transformed_image_keeps_only_watch_window(fit):
    p=Project();e=Element(kind='image',asset=asset(p,Image.new('RGBA',(80,40),'white')),x=-1800,y=-1800,width=4096,height=4096,fit=fit,rotation=32,arc=20)
    p.elements=[e];assert not p.validate()
    bitmap,x,y=canvas_image(p,e);assert bitmap.size==(480,480) and (x,y)==(0,0)
    assert bitmap.getchannel('A').getbbox() is not None


def test_transform_persistence_and_style_independence(tmp_path):
    p=Project(elements=[Element(kind='text',text='S5 STUDIO',rotation=24,arc=90,x=100,y=80,width=220,height=40,size=22)])
    p.add_variant();view=p.editable_variant(1);view.elements[0].rotation=-30;p.commit_variant(1,view)
    p.save(tmp_path/'rotated.s5faceproj');q=Project.load(tmp_path/'rotated.s5faceproj')
    assert q.variant_project(0).elements[0].rotation==24 and q.variant_project(1).elements[0].rotation==-30
    assert q.variant_project(1).elements[0].arc==90
    assert render(q.variant_project(1)).tobytes()==render(p.variant_project(1)).tobytes()
    plain=Element.from_dict({'kind':'rect','width':100,'height':30})
    assert plain.rotation==plain.arc==0 and canvas_static(q,plain)[0].size==(100,30)


@pytest.mark.parametrize('kind,rotation,arc',[('analog',20,0),('pointer',0,10),('number',20,0),('text',float('nan'),0),('text',0,271),('rect',0,180)])
def test_invalid_or_inapplicable_transform_is_rejected(kind,rotation,arc):
    p=Project(elements=[Element(kind=kind,rotation=rotation,arc=arc,width=50,height=100)])
    assert p.validate()


def test_catalog_chinese_names_are_english_without_changing_assets():
    catalog=library()['hands'];translated=[display_preset(p) for p in catalog]
    assert len(translated)==595
    for original,display in zip(catalog,translated):
        assert not re.search('[\u3400-\u9fff]',' '.join(str(display.get(k,'')) for k in ('name','theme','author','variant')))
        assert all(display[k]==original[k] for k in ('id','assetPath','sourceSha256','pivot','shadow','setMembers'))
    assert display_preset({'name':'户外探险家','theme':'样式2','author':'小米'})['name']=='Outdoor Explorer'
    assert display_preset({'name':'户外探险家','theme':'样式2','author':'小米'})['theme']=='Style 2'
    assert any('originalName' in p for p in translated)


@pytest.fixture
def bridge():
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);owner=QObject();b=StudioBridge(owner,smoke=True)
    yield b
    b.timer.stop();b.motion_timer.stop()


def command(b,action,**args):
    reply=json.loads(b.command(json.dumps({'action':action,**args})));assert 'error' not in reply,reply
    return reply


def test_shape_change_undo_and_transform_commands(bridge):
    b=bridge;command(b,'add',kind='rect');e=b.design.elements[-1];identity=e.id
    command(b,'set-shape',id=identity,kind='circle');circle=b.element({'id':identity})
    assert circle.kind=='circle' and circle.width==circle.height
    command(b,'undo');assert b.element({'id':identity}).kind=='rect'
    command(b,'redo');assert b.element({'id':identity}).kind=='circle'
    command(b,'edit',id=identity,changes={'rotation':25,'arc':40})
    assert b.element({'id':identity}).rotation==25
    command(b,'add-variant');command(b,'edit',id=identity,changes={'rotation':-25})
    assert next(e for e in b.project.variant_project(0).elements if e.id==identity).rotation==25
    assert next(e for e in b.project.variant_project(1).elements if e.id==identity).rotation==-25


@pytest.mark.integration
def test_real_compile_transformed_images_text_shapes_weather_lua_and_aod(tmp_path):
    p=template('Analogico');p.name='S5 Trasformazioni';p.elements=[e for e in p.elements if e.kind=='analog']
    main=p.elements[0];main.chrono_pro=True
    image=Element(kind='image',name='Immagine ruotata',x=90,y=30,width=110,height=50,rotation=25,arc=60,
                  asset=asset(p,Image.new('RGBA',(30,20),'#2944bb')))
    text=Element(kind='text',name='Testo arcuato',text='S5 STUDIO',x=130,y=290,width=220,height=40,size=22,rotation=-15,arc=-100)
    chrono=Element(kind='pointer',source='studioChronoMinute',x=100,y=180,width=80,height=80)
    shape=Element(kind='rect',x=320,y=310,width=100,height=20,rotation=40,arc=60)
    circle=Element(kind='circle',x=330,y=60,width=40,height=40,rotation=20)
    frames={'0':asset(p,Image.new('RGBA',(20,20),'red')),'1':asset(p,Image.new('RGBA',(20,20),'blue')),'99':asset(p,Image.new('RGBA',(20,20),'gray'))}
    weather=Element(kind='image_values',name='Meteo',source='weatherCurrentWeather',value_assets=frames,x=230,y=350,width=60,height=40,rotation=20,arc=40)
    live=Element(kind='number',source='heartRate',x=140,y=390,width=140,height=40,size=24)
    aod_text=Element(kind='text',text='AOD',aod=True,x=170,y=60,width=140,height=40,size=24,rotation=10,arc=50)
    p.elements=[image,main,text,chrono,shape,circle,weather,live,*p.elements[1:],aod_text];p.add_variant()
    before=dict(p.assets);output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    archive=next(output.glob('*_TEMPLATE.zip'));data=(output/'resource.bin').read_bytes()
    assert inspect_binary(data)['screenCount']==4 and p.assets==before
    assert validate_package(ROOT/'quadrante_funzionante.zip',archive)['status']=='passed'
    with zipfile.ZipFile(archive) as z:
        report=json.loads(z.read('build-report.json'));assert report['applicationVersion']=='1.7.2'
        for i in (0,1):
            variant=p.variant_project(i);e=next(e for e in variant.elements if e.id==text.id)
            bitmap,x,y=canvas_static(variant,e)
            with Image.open(BytesIO(z.read(f'app/lua/gfx/v{i}_{text.id}_static.png'))) as im:
                assert im.tobytes()==bitmap.tobytes()
            code=z.read(f'app/lua/studio_v{i}_scene.lua').decode('utf8')
            assert f'x={x},y={y},src=SCRIPT_PATH' in code
        for i in (0,2):
            codes={b[:2].hex() for _,_,b in read_tables(data,i)[7]}
            from s5studio.model import SOURCES
            assert SOURCES['heartRate'][1].lower() in codes and SOURCES['weatherCurrentWeather'][1].lower() in codes
        for i in (1,3):assert not read_tables(data,i)[5]
        for index in range(4):
            for _,_,payload in read_tables(data,index)[2]+read_tables(data,index)[3]:
                width,height=struct.unpack_from('<HH',payload,4);assert width<=480 and height<=480
    saved=Project.load(next(output.glob('*.s5faceproj')))
    assert saved.assets==p.assets and saved.elements[0].rotation==25
