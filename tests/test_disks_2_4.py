from dataclasses import replace
from pathlib import Path
import json,struct,subprocess
import xml.etree.ElementTree as ET
import pytest
from PIL import Image,ImageDraw
from s5studio.disk_catalog import DiskCatalog,empty_disk,native_frames,selected_frame
from s5studio.model import Project,Element,SOURCES
from s5studio.render import hand_image,hand_shadow_offset,element_image,render,png_bytes,SCENARIOS
from s5studio.calendar_labels import labels_for,sample_label,MONTHS_SHORT,MOON_PHASES
from s5studio.native import generate_fprj

ROOT=Path(__file__).resolve().parents[1]


def test_all_recovered_discs_and_original_sources_validate(tmp_path):
    c=DiskCatalog(tmp_path/'catalog',bundled_root=ROOT/'resources/disks')
    all_records=c.sets();records=[r for r in all_records if r.get('origin',{}).get('kind')!='user-import'];assert len(records)==89
    assert {r['category'] for r in records}=={'celestial','compass','mechanical','dial'}
    for record in all_records:
        c.validate_record(record)
        assert all(item['pivot']==[n//2 for n in item['size']] for item in record['hands'].values())
    celestial=[r for r in records if r['category']=='celestial']
    assert len(celestial)==13 and all(r['mode']=='values' for r in celestial)
    assert sum(len(r['hands']) for r in records)==515
    report=json.loads((ROOT/'docs/library-analysis/discs-2.4.json').read_text(encoding='utf8'))
    assert len(report['coverage'])==report['watchfacesScanned']==39


def test_custom_disk_center_edit_shadow_and_project_independence(tmp_path):
    path=tmp_path/'sun.png';im=Image.new('RGBA',(100,100));d=ImageDraw.Draw(im)
    d.ellipse((10,10,89,89),fill='#ffc600');d.rectangle((48,2,52,20),fill='red');im.save(path)
    c=DiskCatalog(tmp_path/'catalog');draft=empty_disk();item=c.stage(path)
    assert item['pivot']==[50,50]
    draft.update(name='Sun',hands={'disk':item},generateShadows=True)
    record=c.save(draft);assert record['hands']['disk']['shadow']['generated']
    p=Project(variants=[],complications=[],aod_enabled=False)
    e=Element(kind='disk',width=200,height=200,**c.changes(p,record['id']));p.elements=[e]
    assert not p.validate()
    bitmap,anchor=hand_image(e,'second',p)
    assert bitmap.size==(200,200) and anchor==(100,100)
    assert hand_shadow_offset(e,'second',p)==(4,6)
    shadow,sp=hand_image(e,'second',p,shadow=True)
    assert sp[0]-anchor[0]==10 and shadow.getbbox()
    saved=tmp_path/'disc.s5faceproj';p.save(saved);loaded=Project.load(saved)
    assert png_bytes(render(p))==png_bytes(render(loaded))
    before=png_bytes(render(loaded));draft=c.draft(record['id']);draft['hands']['disk']['pivot']=[30,50];c.save(draft)
    assert png_bytes(render(loaded))==before
    assert c.changes(Project(),record['id'])['second_anchor_x']==30


def test_bundled_override_restore_and_lunar_sequence_shadows(tmp_path):
    c=DiskCatalog(tmp_path/'catalog',bundled_root=ROOT/'resources/disks')
    record=next(r for r in c.sets() if r['category']=='celestial' and len(r['hands'])==30)
    draft=c.draft(record['id']);draft['generateShadows']=True;c.save(draft)
    assert next(r for r in c.summaries() if r['id']==record['id'])['modified']
    p=Project(variants=[],complications=[],aod_enabled=False)
    e=Element(kind='disk',width=120,height=120,**c.changes(p,record['id']));p.elements=[e]
    assert len(e.disk_shadow_assets)==30 and not p.validate()
    frames,xy=native_frames(p,e)
    assert len({im.size for im in frames.values()})==1
    assert len({png_bytes(im) for im in frames.values()})>8
    f=tmp_path/'lunar.s5faceproj';p.save(f);loaded=Project.load(f)
    assert loaded.elements[0].disk_shadow_assets==e.disk_shadow_assets
    assert len(loaded.assets)==len(p.assets)
    c.restore(record['id']);assert not next(r for r in c.summaries() if r['id']==record['id'])['modified']
    assert not c.draft(record['id'])['generateShadows']


def test_delete_bundled_disk_persists_and_keeps_project_and_originals(tmp_path):
    bundled=ROOT/'resources/disks'
    original=(bundled/'catalog.json').read_bytes()
    c=DiskCatalog(tmp_path/'catalog',bundled_root=bundled)
    total=len(c.sets())
    record=c.sets()[0];identity=record['id']
    p=Project(elements=[],variants=[],complications=[],aod_enabled=False)
    p.elements=[Element(kind='disk',width=100,height=100,**c.changes(p,identity))]
    before=png_bytes(render(p));assets=dict(p.assets)
    draft=c.draft(identity);draft['name']='Edited bundled disc';c.save(draft)
    c.delete(identity)
    reloaded=DiskCatalog(tmp_path/'catalog',bundled_root=bundled)
    assert len(reloaded.sets())==total-1 and not any(s['id']==identity for s in reloaded.summaries())
    assert reloaded.deleted_bundled()==[{'id':identity,'name':record['name']}]
    assert png_bytes(render(p))==before and p.assets==assets and not p.validate()
    saved=tmp_path/'preserved.s5faceproj';p.save(saved)
    assert png_bytes(render(Project.load(saved)))==before
    assert (bundled/'catalog.json').read_bytes()==original
    reloaded.restore(identity)
    assert len(reloaded.sets())==total and not reloaded.deleted_bundled()
    assert reloaded.draft(identity)['name']==record['name']
    with pytest.raises(ValueError):reloaded.delete('missing-disc')


def test_delete_personal_disk_persists_without_offering_bundled_restore(tmp_path):
    path=tmp_path/'disc.png';Image.new('RGBA',(40,40),'orange').save(path)
    c=DiskCatalog(tmp_path/'catalog',bundled_root=ROOT/'resources/disks')
    total=len(c.sets())
    record=c.save({**empty_disk(),'name':'Personal disc','hands':{'disk':c.stage(path)}})
    c.delete(record['id'])
    reloaded=DiskCatalog(tmp_path/'catalog',bundled_root=ROOT/'resources/disks')
    assert len(reloaded.sets())==total and not reloaded.deleted_bundled()
    assert not any(s['id']==record['id'] for s in reloaded.sets())


def test_month_abbreviations_lunar_labels_and_24_hour_native_alias(tmp_path):
    assert MONTHS_SHORT==('JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC')
    e=Element(kind='number',source='dateMonth',month_abbreviated=True,width=300)
    assert all(sample_label(e,{'dateMonth':i})==label for i,label in enumerate(MONTHS_SHORT,1))
    assert sample_label(replace(e,source='month'),{'dateMonth':1})=='JAN'
    assert sample_label(replace(e,month_abbreviated=False),{'dateMonth':1})=='January'
    moon=replace(e,source='dateMoon')
    assert tuple(labels_for(moon).values())==MOON_PHASES
    assert sample_label(moon,SCENARIOS['Normale'])=='Full Moon'
    from s5studio.complications import sample_values
    assert sample_values({'hour':18})['timeHour24']==18
    assert SOURCES['timeHour24'][1]==SOURCES['timeHour'][1]
    p=Project(elements=[e],variants=[],complications=[],aod_enabled=False)
    p.save(tmp_path/'month.s5faceproj');assert Project.load(tmp_path/'month.s5faceproj').elements[0].month_abbreviated


def test_native_source_uses_rotating_discs_sequences_shadows_and_calendar(tmp_path):
    c=DiskCatalog(tmp_path/'catalog',bundled_root=ROOT/'resources/disks')
    rose=next(r for r in c.sets() if r['category']=='compass' and r['mode']=='rotation')
    moon=next(r for r in c.sets() if r['category']=='celestial' and len(r['hands'])==30)
    p=Project(variants=[],complications=[],aod_enabled=False)
    p.elements=[Element(kind='disk',x=40,y=40,width=100,height=100,**c.changes(p,rose['id'])),
                Element(kind='disk',x=200,y=40,width=120,height=120,**c.changes(p,moon['id'])),
                Element(kind='number',source='dateMonth',month_abbreviated=True,x=100,y=300,width=200,height=50),
                Element(kind='number',source='dateMoon',x=70,y=360,width=340,height=50)]
    source=generate_fprj(p,tmp_path/'source');xml=ET.parse(source.project_path)
    pointers=xml.findall('.//Widget[@Shape="27"]');assert len(pointers)==1
    lists=xml.findall('.//Widget[@Shape="31"]');assert sorted(len(n.get('BitmapList').split('|')) for n in lists)==[8,12,30]
    assert {n.get('Index_Src') for n in lists}=={SOURCES['dateMonth'][1],SOURCES['dateMoon'][1],SOURCES['dateLunarDay'][1]}


@pytest.mark.parametrize('fallback',[False,True])
def test_only_chrono_main_seconds_rest_stop_reset_and_aod(tmp_path,fallback):
    from test_chrono_pro import pro_project,pro_runtime,view,start,finish
    p=pro_project();main=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    main.only_chrono=True
    p,lua,core=pro_runtime(tmp_path,fallback=fallback,project=p)
    seconds=view(core,'studioIntegratedSecond')
    assert seconds.onlyChrono and seconds.last==0
    assert core.restTimer.paused and not core.clockRunning
    from test_chrono_performance import frame_start
    frame_start(lua,core,fallback)
    if fallback:core.tapLocked=False
    if fallback:core.engineTick=core.started+3661456
    else:lua.globals().TICK=core.started+3661456
    core.update(core,core.started+3661456)
    assert seconds.last==1 and view(core,'studioChronoHour').last==1 and view(core,'studioChronoMinute').last==1
    core.tap(core);assert core.state=='stopped'
    if fallback:core.engineTick+=500;core.tapLocked=False
    else:lua.globals().TICK+=500
    core.tap(core);assert core.state=='resetting'
    core.progress(core,500);assert seconds.last>1
    core.progress(core,1000);assert core.state=='rest' and seconds.last==0
    lua.execute('DATA.timeSecond(58*256)');assert seconds.last==0
    core.screen(core,False);assert not core.active
    core.screen(core,True);assert seconds.last==0
    from s5studio.chrono_pro import ProPreview
    preview=ProPreview();assert preview.values(p,0,47)[main.id+'_second']==0
    preview.tap(p,0,47);preview.values(p,720,48);preview.tap(p,800,48)
    assert preview.values(p,2145,49)[main.id+'_second']==1
    preview.tap(p,2200,49);preview.tap(p,2500,49)
    assert preview.values(p,3220,50)[main.id+'_second']==0


def test_24_hour_small_hand_matches_quarter_day_positions(tmp_path):
    from s5studio.complications import sample_values
    p=Project(variants=[],complications=[],aod_enabled=False)
    e=Element(kind='pointer',source='timeHour24',value_range=24,angle_range=360,width=100,height=100)
    p.elements=[e]
    assert not p.validate()
    for h in (0,6,12,18,23):
        actual=element_image(p,e,sample_values({'hour':h}))
        expected=element_image(p,replace(e,source='timeHour'),sample_values({'hour':h}))
        assert png_bytes(actual)==png_bytes(expected)
