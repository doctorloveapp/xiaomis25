from dataclasses import replace
from datetime import date,timedelta
from pathlib import Path
import hashlib,json,zipfile
import pytest
from s5studio.disk_catalog import DiskCatalog
from s5studio.moon_disk import SOURCE,REFERENCE_DATE,position,calibration_errors,lunar_element,defaults,validate_injection,write_scene as write_moon_scene
from s5studio.model import Element,Project
from s5studio.lua_runtime import scene_layers,write_scene,scene_bindings,interaction_report
from s5studio.native import generate_fprj,build
from s5studio.render import render,png_bytes
from test_motion_interaction import lua_runtime
from test_chrono_pro import pro_project,start,view

ROOT=Path(__file__).resolve().parents[1]


def add_moon(p,*,aod=False,offset=0):
    c=DiskCatalog(ROOT/'resources/disks')
    e=Element(kind='disk',aod=aod,name='Daily moon',x=150,y=235,width=180,height=180,
              **c.changes(p,'disk-longines-moonphase-59'))
    e.moon_day_offset=offset;p.elements.append(e)
    return e


def lunar_project():
    p=Project(elements=[],variants=[],complications=[],aod_enabled=False)
    add_moon(p)
    return p


def runtime(tmp_path,p=None,*,aod=False):
    lua,base=lua_runtime()
    lua.execute('''
      DATA={};TIMERS={};ANIMS=0;TODAY=nil
      os.date=function()return TODAY end
      package.preload.dataman=function() return {subscribe=function(name,obj,cb)
        DATA[name]=DATA[name] or {};table.insert(DATA[name],function(value)cb(obj,value)end)
      end} end
      function emit(name,value)for _,cb in ipairs(DATA[name] or {})do cb(value)end end
      local object=getmetatable(make(nil,{})).__index
      local oldset=object.set
      function object:set(t)self.writes=(self.writes or 0)+1;oldset(self,t)end
      local oldtimer=LV.Timer
      LV.Timer=function(attrs)local t=oldtimer(attrs);table.insert(TIMERS,t);return t end
    ''')
    module=lua.execute((ROOT/'s5studio/lua/studio_moon_disk.lua').read_text(encoding='utf8'))
    lua.globals().MOON=module;lua.execute('package.loaded.studio_moon_disk=MOON')
    p=p or lunar_project()
    if aod:
        e=next(e for e in p.elements if lunar_element(e) and e.aod)
        name=write_moon_scene(p,[e],tmp_path,0,key='v0_moon_'+e.id+'_aod')
    else:
        if any(e.chrono_pro for e in p.elements):
            pro=lua.execute((ROOT/'s5studio/lua/studio_core_pro.lua').read_text(encoding='utf8'))
            lua.globals().PRO=pro;lua.execute('package.loaded.studio_core_pro=PRO')
        name=write_scene(p,scene_layers(p),tmp_path,0)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    return lua,module,module.views[1],p,name


def calendar(lua,value,order=('year','month','day')):
    if isinstance(value,str):value=date.fromisoformat(value)
    for field in order:lua.globals().emit('date'+field.title(),getattr(value,field)*256)


def settle(v):
    if v.timer is not None and not v.timer.paused:
        v.timer.cb();v.timer.cb()


@pytest.mark.parametrize('reference',['2026-09-26','2028-02-29','2000-01-01','2100-02-28'])
@pytest.mark.parametrize('offset',[-58,-1,0,1,58])
def test_python_lua_calendar_and_all_59_positions_agree(tmp_path,reference,offset):
    p=lunar_project();e=p.elements[0];e.moon_reference_date=reference;e.moon_day_offset=offset
    lua,module,v,_,_=runtime(tmp_path,p)
    first=date.fromisoformat(reference)
    for n in range(-1,61):
        current=first+timedelta(days=n);calendar(lua,current);settle(v)
        assert v.last==position(reference,offset,current)==(n+offset)%59
        assert module.ordinal(current.year,current.month,current.day)==current.toordinal()
        assert v.timer.paused
    assert module.ordinal(1900,2,29) is None and module.ordinal(2100,2,29) is None
    assert module.ordinal(2000,2,29)==date(2000,2,29).toordinal()


@pytest.mark.parametrize('order',[('year','month','day'),('day','month','year'),('month','year','day')])
def test_calendar_rollovers_coalesce_and_repeated_notifications_never_write(tmp_path,order):
    lua,module,v,_,_=runtime(tmp_path)
    for stamp in ['2026-12-31','2027-01-01','2028-02-28','2028-02-29','2028-03-01','2100-02-28','2100-03-01']:
        before=v.hands[1].writes;calendar(lua,stamp,order)
        assert v.hands[1].writes==before  # no intermediate month/year poses
        settle(v);assert v.last==position(current=stamp)
        count=v.hands[1].writes
        for _ in range(200):calendar(lua,stamp,order)
        assert v.timer.paused and v.hands[1].writes==count
    assert module.ordinal(2026,13,1) is None


def test_calendar_timer_settles_only_after_revision_is_stable(tmp_path):
    lua,_,v,_,_=runtime(tmp_path)
    calendar(lua,'2026-12-31');settle(v);before=v.hands[1].writes
    lua.globals().emit('dateDay',256);v.timer.cb()
    assert v.hands[1].writes==before
    lua.globals().emit('dateYear',2027*256);v.timer.cb()
    assert v.hands[1].writes==before
    lua.globals().emit('dateMonth',256);v.timer.cb();v.timer.cb()
    assert v.last==position(current='2027-01-01') and v.hands[1].writes==before+1


def test_sleep_resume_and_deleted_view_preserve_daily_counter(tmp_path):
    lua,_,v,_,_=runtime(tmp_path);calendar(lua,REFERENCE_DATE);settle(v)
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    assert not v.visible and v.root.flags[1] and v.timer.paused
    before=v.hands[1].writes;calendar(lua,'2027-01-01')
    assert v.hands[1].writes==before and v.timer.paused
    lua.globals().ScreenStateChangedCB('AOD','ON',0);settle(v)
    assert v.visible and not v.root.flags[1] and v.last==position(current='2027-01-01')
    lua.globals().pageOnPause();calendar(lua,'2027-03-01');before=v.hands[1].writes
    lua.globals().pageOnResume();settle(v)
    assert v.last==position(current='2027-03-01') and v.hands[1].writes==before+1
    root=v.root;root.events[5]()
    assert v.deleted and v.timer.paused
    calendar(lua,'2027-03-02');v.timer.cb();assert not len(v.hands)


def test_aod_moon_is_frozen_and_never_creates_a_timer(tmp_path):
    p=lunar_project();p.elements[0].aod=True;p.aod_enabled=True
    lua,_,v,_,_=runtime(tmp_path,p,aod=True)
    calendar(lua,REFERENCE_DATE)
    assert v.last==0 and not len(lua.globals().TIMERS)
    before=v.hands[1].writes;calendar(lua,'2026-10-12')
    assert v.hands[1].writes==before and v.last==0
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    assert v.last==16 and not len(lua.globals().TIMERS)


def test_atomic_system_date_fallback_and_native_absence(tmp_path):
    lua,_,v,_,_=runtime(tmp_path)
    lua.execute('TODAY={year=2026,month=10,day=12}')
    lua.globals().pageOnResume()
    assert v.last==16 and v.timer is None
    lua.execute('TODAY={year=2026,month=10,day=13}')
    lua.globals().emit('dateDay',13*256)
    assert v.last==17 and v.timer is None


@pytest.mark.parametrize('aod',[False,True])
def test_native_calendar_wins_over_system_date_in_another_timezone(tmp_path,aod):
    p=lunar_project();p.elements[0].aod=aod;p.aod_enabled=aod
    lua,_,v,_,_=runtime(tmp_path,p,aod=aod)
    lua.execute('TODAY={year=2026,month=10,day=12}')
    calendar(lua,'2026-10-13');settle(v)
    assert v.last==17
    lua.globals().pageOnResume();settle(v)
    assert v.last==17


def test_preview_defaults_catalog_and_project_roundtrip(tmp_path):
    assert defaults(SOURCE)=={'value_start':0,'value_range':59,'angle_start':0,'angle_range':360,'moon_reference_date':REFERENCE_DATE,'moon_day_offset':0}
    assert defaults('dateMoon')['angle_range']==180
    p=lunar_project();e=p.elements[0];e.moon_day_offset=-2;e.angle_range=-360;e.angle_start=45
    assert not p.validate()
    before=png_bytes(render(p,{'__moonDate':'2026-10-12'}))
    path=tmp_path/'moon.s5faceproj';p.save(path);loaded=Project.load(path)
    assert png_bytes(render(loaded,{'__moonDate':'2026-10-12'}))==before
    assert before!=png_bytes(render(p,{'__moonDate':'2026-10-13'}))
    assert len(scene_bindings(p))==0 and scene_layers(p)==[e]
    for bad in ['2026-02-29','2026-9-26','2026-09-31','1899-12-31']:
        assert calibration_errors(bad,0)
    assert calibration_errors(REFERENCE_DATE,True) and calibration_errors(REFERENCE_DATE,59)
    for changes in [{'value_range':8},{'angle_range':180},{'disk_mode':'values'},{'moon_reference_date':'no-date'}]:
        bad=p.copy();bad.elements[0]=replace(e,**changes);assert bad.validate()


def test_moon_is_independent_of_all_chrono_callbacks_taps_and_timers(tmp_path):
    p=pro_project();main=next(e for e in p.elements if e.kind=='analog');main.only_chrono=True
    deci=next(e for e in p.elements if e.source=='studioChronoDecisecond');deci.smooth_seconds=True
    e=add_moon(p);p.elements.remove(e);p.elements.insert(0,e)
    lua,_,v,_,_=runtime(tmp_path,p);calendar(lua,REFERENCE_DATE);settle(v)
    for key,n in [('Hour',14),('Minute',8),('Second',47)]:lua.globals().emit('time'+key,n*256)
    core=lua.globals().PRO
    assert len(core.views)==6 and not any(item.id==e.id for _,item in core.views.items())
    start(lua,core);before=v.hands[1].writes
    for elapsed in range(40,2001,40):
        lua.globals().TICK=core.started+elapsed;core.clockAnimation.exec_cb(core.root,elapsed)
    assert v.hands[1].writes==before and v.timer.paused
    assert view(core,'studioChronoDecisecond').last==0 and view(core,'studioIntegratedSecond').last==2
    core.tap(core);lua.globals().TICK+=500;core.tap(core);core.progress(core,1000)
    assert core.state=='rest' and v.last==0 and v.hands[1].writes==before
    calendar(lua,'2026-09-27');settle(v)
    assert v.last==1 and core.state=='rest'


@pytest.mark.parametrize('alteration',['module','reference','angle','range'])
def test_validator_rejects_altered_lunar_module_or_binding(tmp_path,alteration):
    p=lunar_project();e=p.elements[0]
    entry=write_scene(p,scene_layers(p),tmp_path,0)
    files={f.relative_to(tmp_path/'app').as_posix():f.read_bytes() for f in (tmp_path/'app').rglob('*') if f.is_file()}
    assert validate_injection(p,files)['discs'][0]['valueRange']==59
    if alteration=='module':files['lua/studio_moon_disk.lua']+=b'\n-- altered'
    else:
        before,after={'reference':(b'reference={2026,9,26}',b'reference={2026,9,27}'),
                      'angle':(b'angleRange=3600',b'angleRange=-3600'),
                      'range':(b'valueRange=59',b'valueRange=24')}[alteration]
        assert before in files[entry];files[entry]=files[entry].replace(before,after)
    with pytest.raises(ValueError):validate_injection(p,files)


def test_editor_pro_preview_never_overrides_the_daily_moon(tmp_path):
    from s5studio.chrono_pro import ProPreview
    p=pro_project();e=add_moon(p);preview=ProPreview()
    for now,tap in [(0,False),(0,True),(720,False),(800,True),(1200,False),
                    (1300,True),(2020,False),(2100,True),(2820,False)]:
        if tap:preview.tap(p,now,30)
        values=preview.values(p,now,30)
        assert e.id not in values
        for date_value in ('2026-10-01','2026-10-15','2026-10-31'):
            from s5studio.render import element_image
            plain={'__moonDate':date_value}
            assert png_bytes(element_image(p,e,{**plain,'__proValues':values}))==png_bytes(element_image(p,e,plain))


@pytest.mark.integration
@pytest.mark.parametrize('aod_only',[False,True])
def test_real_compiler_moon_styles_aod_and_injection_report(tmp_path,aod_only):
    p=Project(elements=[Element(kind='clock',name='Ora')],variants=[],complications=[],aod_enabled=True) if aod_only else pro_project()
    if not aod_only:
        e=add_moon(p);p.elements.remove(e);p.elements.insert(0,e)
    add_moon(p,aod=True,offset=3);p.aod_enabled=True
    p.elements.append(Element(kind='clock',name='Ora AOD',aod=True,x=100,y=20,width=280,height=70))
    p.elements.append(Element(kind='pointer',name='Datario',source='dateDay',value_start=1,value_range=31))
    if not aod_only:
        p.ensure_independent_variants();p.add_variant(0)
        moon=next(e for e in p.editable_variant(1).elements if lunar_element(e))
        moon.moon_day_offset=-3;moon.angle_range=-360
    assert not p.validate()
    out=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    report=json.loads((out/'build-report.json').read_text(encoding='utf8'))
    lunar=report['interactive']['moonDisc']
    assert lunar['injected'] and not lunar['backgroundPolling'] and not lunar['animationTimers']
    assert len(lunar['discs'])==(1 if aod_only else 3)
    assert lunar['chronoIndependent'] and lunar['aodFrozenBetweenActivations']
    assert report['interactive']['manifestInteractive']=='true'
    with zipfile.ZipFile(next(out.glob('*.zip'))) as archive:
        import xml.etree.ElementTree as ET
        manifest=ET.fromstring(archive.read('resources/manifest.xml'))
        date_pointer=manifest.find('.//DataItemPointer[@source="dateDay"]')
        assert date_pointer is not None and date_pointer.get('valueStart')=='1' and date_pointer.get('valueRange')=='31'
        assert archive.read('app/lua/studio_moon_disk.lua')==(ROOT/'s5studio/lua/studio_moon_disk.lua').read_bytes()
        assert b'backgroundPolling' in (out/'build-report.json').read_bytes()
        if aod_only:assert not any('studio_core' in n for n in archive.namelist())
