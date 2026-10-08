"""Independent styles: editing, migration, persisted assets and real compiler."""
import hashlib,json,os,struct,zipfile
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import Image
from s5studio.model import Project,Element,VariantDesign,template
from s5studio.render import render,png_bytes
from s5studio.native import build,inspect_binary
from s5studio.watchface_library import read_tables
from s5studio.semantic_package import validate_package

ROOT=Path(__file__).resolve().parents[1]


def asset(project,color):
    out=BytesIO();Image.new('RGBA',(480,480),color).save(out,'PNG');data=out.getvalue()
    key='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';project.assets[key]=data
    return key


def command(bridge,action,**args):
    result=json.loads(bridge.command(json.dumps({'action':action,**args})))
    assert 'error' not in result,result.get('error')
    return result


@pytest.fixture
def bridge():
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);owner=QObject();b=StudioBridge(owner,smoke=True)
    yield b
    b.timer.stop();b.motion_timer.stop()


def test_legacy_migration_preserves_all_appearances_then_severs_inheritance():
    p=template('Analogico');e=p.elements[0]
    p.variants.append({'id':'blue','name':'Blu','accent':'#2345ff','background':'#132435',
                       'overrides':{e.id:{'x':30,'second_color':'#bb1234','show_shadows':False}}})
    p.complications=[{'id':'sensor','name':'Sensore','x':80,'y':200,'width':100,'height':50,
                     'frame':'none','showLabel':False,'showUnit':False,'options':['none','steps'],'default':'steps'}]
    expected=[png_bytes(render(p.variant_project(i))) for i in range(2)]
    p.ensure_independent_variants()
    assert p.schema_version==3 and all(v['independent'] for v in p.variants)
    assert expected==[png_bytes(render(p.variant_project(i))) for i in range(2)]
    p.elements[0].color='#ff0000';p.elements[0].x=90;p.complications[0]['x']=140
    second=p.variant_project(1)
    assert second.elements[0].color=='#2345ff' and second.elements[0].x==30
    assert second.complications[0]['x']==80
    p.ensure_independent_variants();assert second.metadata()==p.variant_project(1).metadata()


def test_schema_three_roundtrip_retains_variant_only_assets_and_validates_them(tmp_path):
    p=template('Analogico');i=p.add_variant()
    view=p.editable_variant(i);key=asset(p,'#99ccff')
    view.elements.insert(0,Element(kind='image',asset=key,x=0,y=0,width=480,height=480))
    view.sync_layer_order();p.commit_variant(i,view)
    path=tmp_path/'independent.s5faceproj';p.save(path)
    q=Project.load(path)
    assert q.metadata()==p.metadata() and q.assets[key]==p.assets[key]
    assert key not in {e.asset for e in q.elements}
    del q.assets[key];assert any('risorsa mancante' in e for e in q.validate())


@pytest.mark.parametrize('active',[0,1])
def test_add_delete_reorder_colour_sources_and_groups_affect_only_active_style(bridge,active):
    b=bridge;command(b,'add-variant');command(b,'select-variant',index=active)
    other=1-active;before=b.project.variant_project(other).metadata()
    analog=next(e for e in b.design.elements if e.kind=='analog' and not e.aod)
    command(b,'edit',id=analog.id,changes={'hour_color':'#eebb11','smooth_seconds':True,'chrono_pro':True})
    added=command(b,'add',kind='pointer')['selectedLayer']
    command(b,'edit',id=added,changes={'source':'studioChronoMinute','value_range':60})
    text=command(b,'add',kind='text')['selectedLayer']
    command(b,'edit',id=text,changes={'width':40,'height':30,'x':30,'y':90,'text':'PRO'})
    command(b,'move-group',ids=[added,text],dx=10,dy=10)
    command(b,'align-group',ids=[added,text],alignment='center-x')
    command(b,'reorder-layer',id=text,targetId=added,placement='below')
    assert b.design.layer_order.index(text)<b.design.layer_order.index(added)
    command(b,'add-slot');slot=b.design.complications[-1]
    command(b,'edit-slot',id=slot['id'],changes={'color':'#ff6677','options':['none','steps'],'default':'steps'})
    command(b,'delete',id=text);assert all(e.id!=text for e in b.design.elements)
    command(b,'undo');assert any(e.id==text for e in b.design.elements)
    command(b,'redo');assert all(e.id!=text for e in b.design.elements)
    assert b.project.variant_project(other).metadata()==before
    result=b.state();assert all(e['id']!=text for e in result['layers'])
    assert any(e['id']==slot['id'] for e in result['layers']) and result['independentVariants']


def test_replacing_background_is_visible_and_does_not_touch_original(bridge,monkeypatch):
    b=bridge;key=asset(b.project,'#ff0000')
    original=Element(kind='image',asset=key,name='NASA rosso',x=0,y=0,width=480,height=480)
    b.project.elements.insert(0,original);b.project.sync_layer_order()
    original_preview=png_bytes(render(b.project.variant_project(0)))
    command(b,'add-variant');newkey=asset(b.project,'#0033ee')
    def import_image():
        e=Element(kind='image',asset=newkey);b.design.elements.append(e);return e
    monkeypatch.setattr(b,'import_image',import_image)
    command(b,'variant-image')
    assert b.design.elements[0].asset==newkey and len([e for e in b.design.elements if e.kind=='image'])==1
    assert b.project.elements[0].asset==key and original_preview==png_bytes(render(b.project.variant_project(0)))
    assert render(b.project.variant_project(1)).getpixel((240,420))[:3]==(0,51,238)
    command(b,'edit',id=original.id,changes={'visible':False})
    assert b.project.elements[0].visible
    command(b,'delete',id=original.id);assert b.project.elements[0].asset==key
    command(b,'select-variant',index=0);assert b.element({'id':original.id}).asset==key


def test_aod_is_shared_without_sharing_normal_layers(bridge):
    b=bridge;command(b,'add-variant');normal=png_bytes(render(b.project.variant_project(0)))
    command(b,'aod',value=True);e=next(e for e in b.design.elements if e.aod and e.kind=='analog')
    command(b,'edit',id=e.id,changes={'hour_color':'#ffaa22','x':60})
    assert png_bytes(render(b.project.variant_project(0),aod=True))==png_bytes(render(b.project.variant_project(1),aod=True))
    assert png_bytes(render(b.project.variant_project(0)))==normal
    command(b,'aod',value=False);command(b,'edit',id=b.design.elements[0].id,changes={'hour_color':'#aa3355'})
    assert b.project.elements[0].hour_color!='#aa3355'


@pytest.mark.parametrize('from_aod',[False,True])
def test_background_menu_removes_owned_cloned_image_without_an_import_marker(bridge,from_aod):
    b=bridge;key=asset(b.project,'#ee3300')
    image=Element(kind='image',asset=key,name='NASA',x=0,y=0,width=480,height=480)
    b.project.elements.insert(0,image);b.project.sync_layer_order()
    command(b,'add-variant');assert not b.project.variants[1].get('backgroundLayerId')
    if from_aod:command(b,'aod',value=True);assert b.aod
    command(b,'edit-variant',changes={'imageAsset':''})
    assert not b.aod
    assert all(e.id!=image.id for e in b.design.elements)
    assert b.project.elements[0].asset==key and b.project.elements[0].visible
    command(b,'undo');assert b.design.elements[0].asset==key


def test_deleting_original_promotes_the_surviving_design_and_undo_restores(bridge):
    b=bridge;command(b,'add-variant');e=b.design.elements[0]
    command(b,'edit',id=e.id,changes={'hour_color':'#ffee00'})
    expected=png_bytes(render(b.project.variant_project(1)));name=b.project.variants[1]['name']
    command(b,'select-variant',index=0);command(b,'delete-variant')
    assert len(b.project.variants)==1 and b.project.variants[0]['name']==name
    assert png_bytes(render(b.project.variant_project(0)))==expected and not b.project.validate()
    command(b,'undo');assert len(b.project.variants)==2 and b.project.variants[0]['name']=='Originale'
    command(b,'redo');assert len(b.project.variants)==1 and png_bytes(render(b.project.variant_project(0)))==expected


def test_fifth_style_names_remain_unique_after_deletion_and_invalid_design_is_rejected(bridge):
    b=bridge
    for _ in range(4):command(b,'add-variant')
    assert len(b.project.variants)==5
    command(b,'select-variant',index=2);command(b,'delete-variant');command(b,'add-variant')
    assert len({v['name'] for v in b.project.variants})==5
    result=json.loads(b.command(json.dumps({'action':'add-variant'})));assert result.get('error')
    v=b.project.variants[1];v['design'].elements[0].width=481
    assert any(v['name'] in error for error in b.project.validate())


@pytest.mark.integration
def test_real_compiler_independent_images_bindings_slot_counts_and_aod(tmp_path):
    p=template('Analogico');p.elements=[e for e in p.elements if e.aod or e.kind=='analog']
    p.add_variant();p.add_variant(1)
    for index,color in enumerate(('#dd2200','#0044ee','#009944')):
        view=p.editable_variant(index);view.elements.insert(0,Element(kind='image',name='Sfondo',asset=asset(p,color),x=0,y=0,width=480,height=480))
        if index==1:
            analog=next(e for e in view.elements if e.kind=='analog');analog.chrono_pro=True
            view.elements.insert(1,Element(kind='pointer',name='Minuti Pro',source='studioChronoMinute',x=70,y=100,width=80,height=80))
        if index==2:view.elements.append(Element(kind='number',source='heartRate',x=170,y=320,width=140,height=40,size=24))
        for number in range(index):
            view.complications.append({'id':f'sensor{number}','name':f'Sensore {number}','x':40+number*230,'y':360,'width':110,'height':44,'size':24,
                                       'frame':'none','showLabel':False,'showUnit':False,'options':['none','steps'],'default':'steps','visible':True})
        view.sync_layer_order();p.commit_variant(index,view)
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(output/'resource.bin').read_bytes();info=inspect_binary(data)
    assert info['screenCount']==6 and info['nativeSlots']==3
    assert [len(read_tables(data,i)[8]) for i in (0,2,4)]==[0,1,2]
    assert [bool(read_tables(data,i)[5]) for i in (0,2,4)]==[False,True,False]
    assert all(not read_tables(data,i)[5] for i in (1,3,5))
    assert any(b[:2].hex()=='0822' for _,_,b in read_tables(data,4)[7])
    archive=next(output.glob('*_TEMPLATE.zip'))
    assert validate_package(ROOT/'quadrante_funzionante.zip',archive)['status']=='passed'
    with zipfile.ZipFile(archive) as z:
        report=json.loads(z.read('build-report.json'));assert report['applicationVersion']=='1.3'
        assert report['interactive']['chronoPro']['transitionDirection']=='clockwise-only'
        config=json.loads(z.read('editor.config.json'));assert not config['isSlotFollowing']
        previews=[Image.open(BytesIO(z.read('resources/'+t['preview']))).convert('RGB').getpixel((240,420)) for t in config['themes'] if t['type']=='normal']
        assert previews==[(221,34,0),(0,68,238),(0,153,68)]
        slots=[s['attrs']['SlotGroupName'] for t in config['themes'] for s in t['children'] if s['type']=='Slot']
        assert len(set(slots))==3
    q=Project.load(next(output.glob('*.s5faceproj')));assert q.metadata()==p.metadata()


def test_style_thumbnails_include_all_visible_layers_and_are_independent_of_live_preview(bridge):
    import base64
    from s5studio.render import SCENARIOS
    b=bridge;b.project=template('Analogico');b.project.ensure_independent_variants()
    b.project.elements[0].chrono_pro=True
    b.project.add_variant()
    for index,color in enumerate(('#bb2200','#0044cc')):
        scene=b.project.editable_variant(index)
        scene.elements.insert(0,Element(kind='image',name='Sfondo',asset=asset(b.project,color),x=0,y=0,width=480,height=480))
        scene.elements.append(Element(kind='pointer',source='studioChronoMinute',x=70,y=100,width=80,height=80))
        scene.elements.append(Element(kind='number',source='heartRate',x=170,y=360,width=140,height=40,size=24))
        scene.complications.append({'id':'sensor','name':'Passi','x':40,'y':330,'width':110,'height':44,'size':24,
                                    'frame':'none','showLabel':False,'showUnit':False,'options':['steps'],'default':'steps','visible':True})
        scene.layer_order=[];scene.sync_layer_order();b.project.commit_variant(index,scene)
    b.values['__proValues']={'unrelated':0};b.values['__chronoMs']=54321
    b.aod=True;state=b.state()
    for index,url in enumerate(state['thumbnails']):
        image=base64.b64decode(url.split(',',1)[1]);scene=b.project.variant_project(index)
        assert image==png_bytes(render(scene,SCENARIOS['Normale']))
        background=scene.copy();background.elements=[e for e in background.elements if e.kind=='image'];background.complications=[]
        assert image!=png_bytes(render(background,SCENARIOS['Normale']))
        for kind in ('analog','pointer','number','complication'):
            without=scene.copy()
            if kind=='complication':without.complications=[]
            else:without.elements=[e for e in without.elements if e.kind!=kind]
            assert image!=png_bytes(render(without,SCENARIOS['Normale'])),kind
