from copy import deepcopy
from pathlib import Path
import json
import os
import xml.etree.ElementTree as ET

from PIL import Image,ImageDraw
import pytest

from s5studio.hand_sets import HandSetCatalog,empty_draft
from s5studio.hand_presets import preset_changes
from s5studio.model import Project,Element
from s5studio.native import generate_fprj
from s5studio.render import hand_image,render
from s5studio.watchface_library import library

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def catalog(tmp_path):
    return HandSetCatalog(tmp_path/'personal')


def png(tmp_path,name='needle.png',color='white'):
    path=tmp_path/name;image=Image.new('RGBA',(24,160))
    ImageDraw.Draw(image).polygon([(12,3),(17,145),(12,154),(7,145)],fill=color)
    image.save(path)
    return path


def complete(catalog,tmp_path):
    return {'id':'','name':'My custom set','small':False,'hands':{
        role:catalog.stage(png(tmp_path,role+'.png',color))
        for role,color in [('hour','red'),('minute','green'),('second','blue')]}}


def apply(catalog,p,e,preset,hand,presets=None):
    changes=preset_changes(p,e,ROOT,preset,hand,presets or catalog.presets(),custom_root=catalog.root)
    for k,v in changes.items():setattr(e,k,v)


def test_named_set_reload_autopair_shadows_override_and_self_contained_project(catalog,tmp_path):
    draft=complete(catalog,tmp_path)
    shadow=catalog.stage(png(tmp_path,'shadow.png','#00000080'));shadow['pivot']=[11,150];shadow['offset']=[2,3]
    draft['hands']['hour']['pivot']=[12,147];draft['hands']['hour']['shadow']=shadow
    saved=catalog.save(draft);reloaded=HandSetCatalog(catalog.root);presets=reloaded.presets()
    hour=next(p for p in presets if p['hand']=='hour')
    assert len(presets)==3 and {p['name'] for p in presets}=={'My custom set'}
    assert all(p['setMembers']==hour['setMembers'] for p in presets)
    for role in draft['hands']:(tmp_path/(role+'.png')).unlink()
    p=Project();e=Element(kind='analog',show_ticks=False);p.elements=[e];apply(reloaded,p,e,hour,'hour')
    assert [getattr(e,r+'_preset') for r in ('hour','minute','second')]==[hour['setMembers'][r] for r in ('hour','minute','second')]
    assert (e.hour_anchor_x,e.hour_anchor_y)==(12,147)
    assert (e.hour_shadow_anchor_x,e.hour_shadow_anchor_y,e.hour_shadow_offset_x,e.hour_shadow_offset_y)==(11,150,2,3)
    before=render(p).tobytes();e.second_hand=False # Native AOD never re-enables seconds.
    aod=Element(kind='analog',aod=True);apply(reloaded,p,aod,hour,'hour');assert not aod.second_hand
    p.save(tmp_path/'self-contained.s5faceproj');catalog.delete(saved['id'])
    assert not catalog.presets() and not Project.load(tmp_path/'self-contained.s5faceproj').validate()
    e.second_hand=True;assert render(p).tobytes()==before
    override=next(h for h in library()['hands'] if h['hand']=='minute')
    previous=e.hour_asset,e.second_asset
    apply(catalog,p,e,override,'minute',library()['hands'])
    assert (e.hour_asset,e.second_asset)==previous and e.minute_preset==override['id']
    assert all(getattr(e,r+'_asset') in p.assets for r in ('hour','minute','second'))


def test_update_preserves_ids_duplicate_names_and_invalid_save_are_atomic(catalog,tmp_path):
    first=catalog.save(complete(catalog,tmp_path));ids=[p['id'] for p in catalog.presets()]
    edit=catalog.draft(first['id']);edit['name']='Renamed set';edit['hands']['minute']['pivot']=[12,150]
    catalog.save(edit)
    assert [p['id'] for p in catalog.presets()]==ids and len(catalog.sets())==1
    before=catalog.path.read_bytes();duplicate=complete(catalog,tmp_path);duplicate['name']='renamed SET'
    with pytest.raises(ValueError,match='già'):catalog.save(duplicate)
    incomplete=empty_draft();incomplete['name']='Incomplete';incomplete['hands']['hour']=edit['hands']['hour']
    with pytest.raises(ValueError,match='ore, minuti e secondi'):catalog.save(incomplete)
    invalid=deepcopy(edit);invalid['hands']['hour']['pivot']=[24,0]
    with pytest.raises(ValueError,match='pivot'):catalog.save(invalid)
    assert catalog.path.read_bytes()==before


@pytest.mark.parametrize('size,color,fmt', [((481,10),'white','PNG'),((10,481),'white','PNG'),((8,8),(0,0,0,0),'PNG'),((24,160),'white','JPEG')])
def test_invalid_assets_rejected_without_catalog_change(catalog,tmp_path,size,color,fmt):
    source=tmp_path/'bad.png';image=Image.new('RGBA',size,color)
    (image.convert('RGB') if fmt=='JPEG' else image).save(source,format=fmt)
    with pytest.raises(ValueError):catalog.stage(source)
    assert not catalog.path.exists()


def test_modified_png_and_path_traversal_are_rejected(catalog,tmp_path):
    item=catalog.stage(png(tmp_path));corrupt=deepcopy(item);corrupt['assetPath']='../outside.png'
    with pytest.raises(ValueError,match='Percorso'):catalog.bitmap_path(corrupt)
    (catalog.root/item['assetPath']).write_bytes(b'altered')
    with pytest.raises(ValueError,match='alterata'):catalog.bitmap_path(item)


def test_small_set_keeps_manual_pivot_in_preview_and_native_export(catalog,tmp_path):
    draft=empty_draft();draft.update(name='Small crono',small=True)
    item=catalog.stage(png(tmp_path));item['pivot']=[12,125];draft['hands']['second']=item
    record=catalog.save(draft);preset=catalog.presets()[0]
    p=Project();e=Element(kind='pointer',source='studioChronoMinute',width=120,height=120)
    p.elements=[e];apply(catalog,p,e,preset,'second')
    assert not e.pointer_end_pivot and e.second_anchor_y==125
    bitmap,pivot=hand_image(e,'second',p);assert pivot[1]<bitmap.height-1
    source=generate_fprj(p,tmp_path/'native-small')
    assert source.project_path.is_file() and not p.validate()
    catalog.delete(record['id']);assert hand_image(e,'second',p)[1]==pivot


def test_main_set_images_and_pivots_are_exported_by_native_path(catalog,tmp_path):
    draft=complete(catalog,tmp_path);draft['hands']['minute']['pivot']=[12,130]
    catalog.save(draft);p=Project();e=Element(kind='analog',show_ticks=False);p.elements=[e]
    apply(catalog,p,e,next(x for x in catalog.presets() if x['hand']=='hour'),'hour')
    generated=generate_fprj(p,tmp_path/'native-main');widgets=ET.parse(generated.project_path).getroot().find('Screen')
    analog=next(w for w in widgets if w.get('Shape')=='27' and w.get('MinuteImage_rotate_yc') is not None)
    assert int(analog.get('MinuteImage_rotate_yc'))==hand_image(e,'minute',p)[1][1]
    assert e.minute_asset in p.assets and not p.validate()


def test_bridge_import_cancel_pivot_persistence_and_edit_isolated_from_project(catalog,tmp_path,monkeypatch):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication,QFileDialog
    from PySide6.QtCore import QObject
    import s5studio.web_ui as ui
    app=QApplication.instance() or QApplication([]);owner=QObject()
    monkeypatch.setattr(ui,'user_data_root',lambda:tmp_path/'user')
    bridge=ui.StudioBridge(owner,smoke=True)
    def command(action,**args):
        reply=json.loads(bridge.command(json.dumps({'action':action,**args})))
        assert 'error' not in reply,reply
        return reply
    initial=bridge.project.metadata();command('hand-set-meta',changes={'name':'Bridge set'})
    for role in ('hour','minute','second'):
        path=png(tmp_path,role+'-bridge.png')
        monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,p=path:(str(p),'PNG'))
        command('hand-set-image',role=role)
    before=deepcopy(bridge.hand_set_draft)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a:('','PNG'))
    command('hand-set-image',role='second');assert bridge.hand_set_draft==before
    command('hand-set-part',role='hour',changes={'pivot':[12,140]})
    bad=json.loads(bridge.command(json.dumps({'action':'hand-set-part','role':'hour','changes':{'pivot':[24,0]}})))
    assert 'error' in bad and bridge.hand_set_draft['hands']['hour']['pivot']==[12,140]
    result=command('hand-set-save');record=next(s for s in result['state']['handSets'] if s['name']=='Bridge set')
    assert bridge.project.metadata()==initial and not bridge.dirty and not bridge.undo_stack
    other=ui.StudioBridge(owner,smoke=True)
    assert any(s['name']=='Bridge set' for s in other.state()['handSets'])
    chosen=next(p for p in bridge.hand_presets if p.get('custom') and p['hand']=='hour' and p['setId']==record['id'])
    analog=next(e for e in bridge.design.elements if e.kind=='analog')
    command('hand-preset',id=analog.id,hand='hour',preset=chosen['id'])
    after=deepcopy(bridge.project.assets);metadata=bridge.project.metadata()
    command('hand-set-load',id=record['id']);command('hand-set-meta',changes={'name':'Updated name'});command('hand-set-save')
    assert bridge.project.assets==after and bridge.project.metadata()==metadata
    command('hand-set-delete',id=record['id']);assert bridge.project.assets==after and bridge.project.metadata()==metadata
    assert not any(s['id']==record['id'] for s in bridge.state()['handSets']) and bridge.state()['handSetDraft']==empty_draft()
    bridge.timer.stop();bridge.motion_timer.stop();other.timer.stop();other.motion_timer.stop()
