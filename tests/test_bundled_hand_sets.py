from copy import deepcopy
import hashlib
import json
from pathlib import Path

from PIL import Image
import pytest

from s5studio.hand_sets import HandSetCatalog,empty_draft
from s5studio.hand_presets import preset_changes
from s5studio.model import Project,Element
from s5studio.release_hand_sets import sync_hand_sets
from s5studio.watchface_library import library

ROOT=Path(__file__).resolve().parents[1]


def personal(folder,name='New small set'):
    catalog=HandSetCatalog(folder);png=folder.parent/(name+'.png');png.parent.mkdir(parents=True,exist_ok=True)
    Image.new('RGBA',(12,72),'orange').save(png)
    draft=empty_draft();draft.update(name=name,small=True,generateShadows=True)
    draft['hands']['second']=catalog.stage(png)
    return catalog,catalog.save(draft)


def runtime(root,local):
    return HandSetCatalog(local,bundled_root=root/'resources/hand-sets',library_hands=library()['hands'],resources=ROOT)


def test_new_pc_bundled_sets_apply_edit_and_restore_without_originals(tmp_path):
    user=tmp_path/'fresh-pc';catalog=runtime(ROOT,user)
    assert not user.exists()
    names={s['name'] for s in catalog.sets()}
    assert {'Seiko 5 ombra','Swatch Orange ombra','Swatch orange piccole','Hamilton Lancette'}<=names
    assert len(catalog.presets())==595+sum(len(s['hands']) for s in json.loads((ROOT/'resources/hand-sets/catalog.json').read_text(encoding='utf8'))['sets']) and not user.exists()
    record=next(s for s in catalog.sets() if s['name']=='Seiko 5 ombra')
    bundled=(ROOT/'resources/hand-sets/catalog.json').read_bytes()
    draft=catalog.draft(record['id']);draft['name']='Edited Seiko';draft['hands']['hour']['pivot'][0]-=1
    catalog.save(draft)
    fresh=runtime(ROOT,user);preset=next(p for p in fresh.presets() if p['setId']==record['id'] and p['hand']=='hour')
    project=Project();element=Element(kind='analog');project.elements=[element]
    changes=preset_changes(project,element,ROOT,preset,'hour',fresh.presets(),custom_catalog=fresh)
    assert changes['hour_anchor_x']==draft['hands']['hour']['pivot'][0]
    assert all(changes[r+'_asset'] in project.assets for r in ('hour','minute','second'))
    assert changes['minute_shadow_asset'] in project.assets
    assert len([s for s in fresh.sets() if s['id']==record['id']])==1
    fresh.restore(record['id']);assert fresh.draft(record['id'])['name']=='Seiko 5 ombra'
    assert (ROOT/'resources/hand-sets/catalog.json').read_bytes()==bundled


def test_all_original_graphics_are_editable_and_initial_presets_are_unchanged(tmp_path):
    catalog=HandSetCatalog(tmp_path/'user',library_hands=library()['hands'],resources=ROOT)
    original={p['id']:p for p in library()['hands']};presets=catalog.presets()
    assert {p['id'] for p in presets}==set(original) and len(presets)==595
    for preset in presets:
        assert {k:v for k,v in preset.items() if k!='setId'}=={k:v for k,v in original[preset['id']].items() if k!='setId'}
    seen=set()
    for record in catalog.sets():
        draft=catalog.draft(record['id']);seen.update(draft['origin']['members'].values())
        for item in draft['hands'].values():
            catalog.validate_item(item)
            if item.get('shadow'):catalog.validate_item(item['shadow'])
    assert seen==set(original)
    assert not catalog.path.exists() # Opening drafts never saves catalog changes.


@pytest.mark.parametrize('small,aod',[(False,False),(False,True),(True,False),(True,True)])
def test_original_sets_edit_reopen_apply_and_restore_keep_preset_ids(tmp_path,small,aod):
    catalog=HandSetCatalog(tmp_path/'user',library_hands=library()['hands'],resources=ROOT)
    record=next(s for s in catalog.sets() if s['small']==small and
                all(catalog.original_presets[k]['aod']==aod for k in s['origin']['members'].values()))
    originals={p['id']:deepcopy(p) for p in catalog.presets() if p['setId']==record['id']}
    draft=catalog.draft(record['id']);draft['name']='Edited original';role=next(iter(draft['hands']))
    draft['hands'][role]['pivot'][0]=0
    catalog.save(draft)
    saved=HandSetCatalog(catalog.root,library_hands=library()['hands'],resources=ROOT)
    presets=[p for p in saved.presets() if p['setId']==record['id']]
    assert {p['id'] for p in presets}==set(originals)
    chosen=next(p for p in presets if p['id']==record['origin']['members'][role])
    project=Project();element=Element(kind='pointer' if small else 'analog',aod=aod);project.elements=[element]
    changes=preset_changes(project,element,ROOT,chosen,'second' if small else role,saved.presets(),custom_catalog=saved)
    assert changes[('second' if small else role)+'_anchor_x']==0
    if aod and not small:assert not changes.get('second_hand',False)
    before=deepcopy(project.assets);saved.restore(record['id'])
    assert {p['id']:p for p in saved.presets() if p['setId']==record['id']}==originals
    assert project.assets==before


def test_external_pivots_are_padded_without_moving_original_pixels(tmp_path):
    catalog=HandSetCatalog(tmp_path/'user',library_hands=library()['hands'],resources=ROOT)
    records=[s for s in catalog.builtin_sets if any(p.get('externalPivot') for p in s['hands'].values())]
    assert records
    for record in records:
        draft=catalog.draft(record['id'])
        for role,original in record['hands'].items():
            item=draft['hands'][role];assert item['pivot']==original['pivot']
            with Image.open(ROOT/original['assetPath']) as before,Image.open(catalog.bitmap_path(item)) as after:
                assert after.crop((0,0,*before.size)).tobytes()==before.convert('RGBA').tobytes()
            catalog.validate_item(item)


def test_release_sync_discovers_new_sets_updates_and_validates_before_writing(tmp_path):
    source,first=personal(tmp_path/'app-user/hand-sets')
    second_source,second=personal(tmp_path/'dev-user/hand-sets','Other set')
    root=tmp_path/'release';root.mkdir();paths=[second_source.root,source.root]
    before=source.path.read_bytes();report=sync_hand_sets(root,paths)
    assert report['bundledSets']==2 and len(report['updates'])==2
    assert source.path.read_bytes()==before
    assert sync_hand_sets(root,paths)['updates']==[]
    edited=source.draft(first['id']);edited['name']='Updated local';edited['hands']['second']['pivot']=[3,60];source.save(edited)
    report=sync_hand_sets(root,paths);assert report['updates']==[{'id':first['id'],'name':'Updated local','action':'updated'}]
    fresh=HandSetCatalog(tmp_path/'new-pc',bundled_root=root/'resources/hand-sets')
    assert fresh.draft(first['id'])['hands']['second']['pivot']==[3,60]
    output=root/'resources/hand-sets/catalog.json';good=output.read_bytes()
    source.bitmap_path(edited['hands']['second']).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='alterata'):sync_hand_sets(root,paths)
    assert output.read_bytes()==good


def test_bundled_deletion_persists_and_projects_keep_their_assets(tmp_path):
    catalog=runtime(ROOT,tmp_path/'user');preset=next(p for p in catalog.presets() if p.get('custom') and p['small'])
    project=Project();element=Element(kind='pointer');project.elements=[element]
    changes=preset_changes(project,element,ROOT,preset,'second',catalog.presets(),custom_catalog=catalog)
    for key,value in changes.items():setattr(element,key,value)
    project.save(tmp_path/'saved.s5faceproj');catalog.delete(preset['setId'])
    reopened=runtime(ROOT,catalog.root)
    assert not any(p['setId']==preset['setId'] for p in reopened.presets())
    assert Project.load(tmp_path/'saved.s5faceproj').assets==project.assets
    reopened.restore(preset['setId']);assert any(p['setId']==preset['setId'] for p in reopened.presets())
