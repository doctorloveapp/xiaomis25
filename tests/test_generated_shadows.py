from copy import deepcopy
from pathlib import Path
import json
import os

from PIL import Image,ImageDraw
import pytest

from s5studio.hand_sets import HandSetCatalog,empty_draft,SHADOW_OPTIONS
from s5studio.hand_presets import preset_changes
from s5studio.lua_runtime import pro_views
from s5studio.model import Project,Element
from s5studio.native import generate_fprj
from s5studio.render import hand_image,png_bytes,render

ROOT=Path(__file__).resolve().parents[1]


def mother(catalog,tmp_path,name='needle',size=(24,160)):
    path=tmp_path/(name+'.png');image=Image.new('RGBA',size)
    ImageDraw.Draw(image).rectangle((8,8,15,size[1]-9),fill=(220,170,100,240));image.save(path)
    return catalog.stage(path)


def draft(catalog,tmp_path,small=False):
    result=empty_draft();result.update(name='Auto shadows',small=small,generateShadows=True)
    result['hands']={role:mother(catalog,tmp_path,role) for role in (('second',) if small else ('hour','minute','second'))}
    return result


def test_alpha_silhouette_padding_pivot_and_original_bytes(tmp_path):
    catalog=HandSetCatalog(tmp_path/'catalog');initial=draft(catalog,tmp_path,True)
    item=initial['hands']['second'];item['pivot']=[12,143]
    original=catalog.bitmap_path(item).read_bytes();result=catalog.refresh_generated(initial)
    shadow=result['hands']['second']['shadow']
    assert 'shadow' not in initial['hands']['second'] # Pure draft update.
    assert shadow['generated'] and shadow['size']==[34,170] and shadow['pivot']==[17,148]
    assert shadow['offset']==[2,3] and shadow['generatedFrom']['pivot']==[12,143]
    with Image.open(catalog.bitmap_path(shadow)) as image:
        assert image.getpixel((17,80))[:3]==(0,0,0) and 104<=image.getpixel((17,80))[3]<=108
        assert image.getpixel((5,5))==(0,0,0,0)
        assert image.getpixel((12,80))[3]>0 # Blur extends into transparent margin.
        assert max(image.getchannel('A').getdata())<=108
    assert catalog.bitmap_path(item).read_bytes()==original
    sharp=deepcopy(initial);sharp['shadowOptions']['blur']=0
    sharp=catalog.refresh_generated(sharp)['hands']['second']['shadow']
    assert sharp['size']==item['size'] and sharp['pivot']==item['pivot']


def test_manual_shadows_preserved_toggle_only_removes_generated(tmp_path):
    catalog=HandSetCatalog(tmp_path/'catalog');initial=draft(catalog,tmp_path)
    manual=mother(catalog,tmp_path,'manual');manual['pivot']=[10,140];manual['offset']=[-2,4]
    initial['hands']['hour']['shadow']=deepcopy(manual)
    result=catalog.refresh_generated(initial)
    assert result['hands']['hour']['shadow']==manual
    assert all(result['hands'][h]['shadow']['generated'] for h in ('minute','second'))
    result['generateShadows']=False;off=catalog.refresh_generated(result)
    assert off['hands']['hour']['shadow']==manual
    assert all('shadow' not in off['hands'][h] for h in ('minute','second'))
    off['generateShadows']=True;on=catalog.refresh_generated(off)
    assert on['hands']['hour']['shadow']==manual and on['hands']['second']['shadow']==result['hands']['second']['shadow']


def test_settings_source_and_pivot_updates_rebuild_only_automatic_shadow(tmp_path):
    catalog=HandSetCatalog(tmp_path/'catalog');result=catalog.refresh_generated(draft(catalog,tmp_path,True))
    item=result['hands']['second'];old=deepcopy(item['shadow'])
    item['pivot']=[10,120];result=catalog.refresh_generated(result)
    assert result['hands']['second']['shadow']['pivot']==[15,125]
    assert result['hands']['second']['shadow']['sourceSha256']==old['sourceSha256']
    result['shadowOptions'].update(opacity=70,blur=0,offset=[4,-3]);result=catalog.refresh_generated(result)
    new=result['hands']['second']['shadow']
    assert new['pivot']==[10,120] and new['offset']==[4,-3] and new['sourceSha256']!=old['sourceSha256']
    replacement=mother(catalog,tmp_path,'replacement',(32,170));replacement['shadow']=deepcopy(new)
    result['hands']['second']=replacement;result=catalog.refresh_generated(result)
    assert result['hands']['second']['shadow']['size']==[32,170]
    assert result['hands']['second']['shadow']['generatedFrom']['sourceSha256']==replacement['sourceSha256']
    saved=catalog.save(result);reloaded=HandSetCatalog(catalog.root).draft(saved['id'])
    assert reloaded==saved and catalog.presets()[0]['shadow']==saved['hands']['second']['shadow']


@pytest.mark.parametrize('size',[(480,480),(479,24),(24,480)])
def test_shadow_canvas_never_exceeds_watch_limits(tmp_path,size):
    catalog=HandSetCatalog(tmp_path/'catalog');result=empty_draft()
    result.update(name='Limit',small=True,generateShadows=True)
    result['hands']['second']=mother(catalog,tmp_path,size=size)
    saved=catalog.save(result);shadow=saved['hands']['second']['shadow']
    assert all(1<=n<=480 for n in shadow['size'])
    catalog.validate_item(shadow)


@pytest.mark.parametrize('options',[{'opacity':0},{'blur':float('nan')},{'offset':[21,0]},{'offset':None}])
def test_invalid_shadow_options_do_not_modify_catalog(tmp_path,options):
    catalog=HandSetCatalog(tmp_path/'catalog');result=draft(catalog,tmp_path,True)
    result['shadowOptions'].update(options)
    with pytest.raises(ValueError):catalog.save(result)
    assert not catalog.path.exists()


@pytest.mark.parametrize('kind,pro',[('analog',False),('analog',True),('pointer',False)])
def test_generated_shadows_use_existing_native_and_lua_paths(tmp_path,kind,pro):
    catalog=HandSetCatalog(tmp_path/'catalog');saved=catalog.save(draft(catalog,tmp_path,kind=='pointer'))
    presets=catalog.presets();chosen=next(p for p in presets if p['hand']==('second' if kind=='pointer' else 'hour'))
    p=Project(background='#d0d0d0');e=Element(kind=kind,x=60,y=60,width=360,height=360,second_hand=kind=='analog',chrono_pro=pro,show_ticks=False)
    p.elements=[e]
    for k,v in preset_changes(p,e,ROOT,chosen,'second' if kind=='pointer' else 'hour',presets,custom_root=catalog.root).items():setattr(e,k,v)
    before=png_bytes(render(p));e.show_shadows=False;assert png_bytes(render(p))!=before;e.show_shadows=True
    generated=generate_fprj(p,tmp_path/'export')
    if pro:
        for view in pro_views(e):
            path=generated.project_path.parent/'app/lua/gfx'/('v0_'+view.id+'_shadow.png')
            with Image.open(path) as image:assert png_bytes(image.convert('RGBA'))==png_bytes(hand_image(view,'second',p,shadow=True)[0])
    else:
        roles=('second',) if kind=='pointer' else ('hour','minute','second')
        paths=list((generated.project_path.parent/'images').glob('*shadow*.png'))
        assert len(paths)==len(roles)
        for role in roles:
            path=next(path for path in paths if role in path.stem or kind=='pointer')
            with Image.open(path) as image:assert png_bytes(image.convert('RGBA'))==png_bytes(hand_image(e,role,p,shadow=True)[0])
    p.save(tmp_path/'face.s5faceproj');catalog.delete(saved['id'])
    assert png_bytes(render(Project.load(tmp_path/'face.s5faceproj')))==before


def test_legacy_sets_open_with_generation_disabled(tmp_path):
    catalog=HandSetCatalog(tmp_path/'catalog');saved=catalog.save(draft(catalog,tmp_path,True))
    for key in ('generateShadows','shadowOptions'):saved.pop(key)
    saved['hands']['second'].pop('shadow')
    catalog._write([saved])
    legacy=catalog.draft(saved['id'])
    assert not legacy['generateShadows'] and legacy['shadowOptions']==SHADOW_OPTIONS
    assert catalog.presets()[0]['shadow'] is None


def test_bridge_generates_on_import_and_preserves_manual_shadow(tmp_path,monkeypatch):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication,QFileDialog
    from PySide6.QtCore import QObject
    import s5studio.web_ui as ui
    app=QApplication.instance() or QApplication([]);owner=QObject()
    monkeypatch.setattr(ui,'user_data_root',lambda:tmp_path/'user')
    b=ui.StudioBridge(owner,smoke=True)
    def command(action,**args):
        reply=json.loads(b.command(json.dumps({'action':action,**args})));assert 'error' not in reply,reply
        return reply['state']['handSetDraft']
    original=b.project.metadata()
    command('hand-set-meta',changes={'name':'Small generated','small':True,'generateShadows':True})
    path=tmp_path/'import.png';Image.new('RGBA',(24,160),'white').save(path)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a:(str(path),'PNG'))
    added=command('hand-set-image',role='second')
    assert added['hands']['second']['shadow']['generated']
    adjusted=command('hand-set-part',role='second',changes={'pivot':[12,130]})
    assert adjusted['hands']['second']['shadow']['pivot']==[17,135]
    manual=command('hand-set-image',role='second',shadow=True)['hands']['second']['shadow']
    assert 'generated' not in manual
    off=command('hand-set-meta',changes={'generateShadows':False});assert off['hands']['second']['shadow']==manual
    assert b.project.metadata()==original and not b.dirty
    command('hand-set-save');assert not next(s for s in b.hand_set_catalog.sets() if s['name']=='Small generated')['generateShadows']
    b.timer.stop();b.motion_timer.stop()
