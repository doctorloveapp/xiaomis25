"""Live native-source layers must not be flattened or reordered by chrono export."""
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET
import pytest
from s5studio.model import Element,Project
from s5studio.calendar_labels import labels_for
from s5studio.scene_data import validate_injection,supported
from s5studio.lua_runtime import scene_layers,write_scene,scene_bindings
from s5studio.native import generate_fprj
from s5studio.render import png_bytes
from s5studio.render import element_image
from test_motion_interaction import lua_runtime
from test_chrono_pro import pro_project,start
from test_moon_disk import add_moon

ROOT=Path(__file__).resolve().parents[1]


def mixed_project(pro=True):
    p=pro_project() if pro else Project(elements=[Element(kind='pointer',source='studioChronoMinute'),Element(kind='pointer',source='studioChronoSecond')],variants=[],complications=[],aod_enabled=False)
    month=Element(kind='number',source='dateMonth',name='Month',month_abbreviated=True)
    day=Element(kind='number',source='dateWeek',name='Day')
    p.elements[1:1]=[month,day]
    p.assets['assets/fixture-hand.png']=png_bytes(Image.new('RGBA',(10,60),'white'))
    for source,period in [('timeHour24',24),('timeSecond',60),('dateDay',31)]:
        p.elements.insert(1,Element(kind='pointer',source=source,value_range=period,
                                   smooth_seconds=True,show_shadows=True,
                                   second_asset='assets/fixture-hand.png',second_shadow_asset='assets/fixture-hand.png'))
    moon=add_moon(p);p.elements.remove(moon);p.elements.insert(0,moon)
    return p


def runtime(tmp_path,p):
    lua,core=lua_runtime()
    lua.execute('''
      DATA={};TIMER_COUNT=0;os.date=function()return {year=2026,month=10,day=12}end
      package.preload.dataman=function()return {subscribe=function(source,obj,cb)
        DATA[source]=DATA[source] or {};table.insert(DATA[source],function(raw)cb(obj,raw)end)
      end}end
      function emit(source,value)for _,cb in ipairs(DATA[source] or {})do cb(value)end end
      local old=LV.Timer;LV.Timer=function(attrs)TIMER_COUNT=TIMER_COUNT+1;return old(attrs)end
      local object=getmetatable(make(nil,{})).__index;local oldset=object.set
      function object:set(t)self.writes=(self.writes or 0)+1;oldset(self,t)end
    ''')
    for module in ['studio_scene_data','studio_moon_disk','studio_core_pro']:
        lua.globals().MODULE=lua.execute((ROOT/f's5studio/lua/{module}.lua').read_text(encoding='utf8'))
        lua.execute(f'package.loaded.{module}=MODULE')
    name=write_scene(p,scene_layers(p),tmp_path,0)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    data=lua.eval('require("studio_scene_data")')
    pro=lua.eval('require("studio_core_pro")')
    return lua,data,pro,core,name


@pytest.mark.parametrize('pro',[False,True])
def test_scene_keeps_source_order_and_runtime_bindings(tmp_path,pro):
    p=mixed_project(pro);lua,data,controller,classic,name=runtime(tmp_path,p)
    code=(tmp_path/'app'/name).read_text(encoding='utf8')
    native=[e for e in scene_layers(p) if supported(e)]
    assert [v.config.id for _,v in data.views.items()]==[e.id for e in native]
    assert [code.index('"id"]="'+e.id+'"') for e in native]==sorted(code.index('"id"]="'+e.id+'"') for e in native)
    chrono_ids={v.id for _,v in (controller if pro else classic).views.items()}
    assert not chrono_ids.intersection(e.id for e in native)
    assert len(chrono_ids)==len(scene_bindings(p))
    files={f.relative_to(tmp_path/'app').as_posix():f.read_bytes() for f in (tmp_path/'app').rglob('*') if f.is_file()}
    assert len(validate_injection(p,files)['bindings'])==5
    files[name]=files[name].replace(b'"source"]="dateWeek"',b'"source"]="dateMonth"')
    with pytest.raises(ValueError,match='Binding dinamico'):validate_injection(p,files)


def test_native_pointer_values_and_calendar_images_stay_live_during_chrono(tmp_path):
    p=mixed_project();lua,data,core,_,_=runtime(tmp_path,p)
    views={v.config.source:v for _,v in data.views.items()}
    baseline=lua.globals().TIMER_COUNT
    for source,value in [('timeHour',14),('timeSecond',59),('dateDay',31),('dateWeek',1),('dateMonth',10),('timeMinute',20)]:
        lua.globals().emit(source,value*256)
    assert views['timeHour'].hands[1].value==14
    assert views['dateDay'].hands[1].value==31
    assert views['dateWeek'].image.src.endswith('_calendar_1.png')
    assert views['dateMonth'].image.src.endswith('_calendar_10.png')
    second=views['timeSecond'];second.animation.exec_cb(second.root,500)
    assert second.hands[1].value==59500 and second.hands[2].value==59500
    second.animation.exec_cb(second.root,1000)
    assert second.hands[1].value==0
    lua.globals().emit('timeSecond',0)
    assert second.hands[1].value==0
    before=second.hands[1].writes
    for _ in range(20):lua.globals().emit('timeSecond',0)
    assert second.hands[1].writes==before
    start(lua,core)
    lua.globals().emit('dateDay',1*256);lua.globals().emit('dateWeek',2*256);lua.globals().emit('dateMonth',11*256)
    assert views['dateDay'].hands[1].value==1 and views['dateWeek'].image.src.endswith('_calendar_2.png')
    assert views['dateMonth'].image.src.endswith('_calendar_11.png')
    # No polling timer was added for these scene data views.
    assert lua.globals().TIMER_COUNT==baseline
    lua.globals().emit('dateWeek',2147483647)
    assert views['dateWeek'].image.flags[1]
    lua.globals().emit('dateWeek',3*256)
    assert not views['dateWeek'].image.flags[1]


def test_scene_data_pause_aod_resume_and_delete(tmp_path):
    p=mixed_project();lua,data,core,_,_=runtime(tmp_path,p)
    second=next(v for _,v in data.views.items() if v.config.source=='timeSecond')
    lua.globals().emit('timeSecond',4*256)
    second.animation.exec_cb(second.root,400);before=second.hands[1].writes
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    lua.globals().emit('timeSecond',20*256);second.animation.exec_cb(second.root,700)
    assert second.hands[1].writes==before and not second.animation.run and second.root.flags[1]
    lua.globals().pageOnResume();assert not second.animation.run
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert second.animation.run and second.hands[1].value==20000 and not second.root.flags[1]
    lua.globals().pageOnPause();before=second.hands[1].writes
    lua.globals().emit('timeSecond',25*256);second.animation.exec_cb(second.root,800)
    assert not second.animation.run and second.hands[1].writes==before
    lua.globals().pageOnResume();assert second.hands[1].value==25000
    second.root.events[5]();lua.globals().emit('timeSecond',30*256)
    assert second.deleted and not second.animation.run and not len(second.hands)


def test_generate_native_source_with_live_calendar_between_moon_and_chrono(tmp_path):
    p=mixed_project();src=generate_fprj(p,tmp_path)
    widgets=ET.parse(src.project_path).findall('.//Widget')
    assert sum(w.get('Shape')=='34' for w in widgets)==1
    assert not any(w.get('Name','').startswith('pointer_') for w in widgets)
    assert 'studio_scene_data.lua' in [f.name for f in (tmp_path/'app/lua').glob('*.lua')]
    # Native images-with-values must not accidentally become rotating pointers.
    assert not supported(Element(kind='disk',disk_mode='values',source='dateMoon'))


def test_independent_styles_keep_their_calendar_source_settings_and_module(tmp_path):
    p=mixed_project();p.ensure_independent_variants();p.add_variant(0)
    month=next(e for e in p.editable_variant(1).elements if e.source=='dateMonth')
    month.month_abbreviated=False
    second=next(e for e in p.editable_variant(1).elements if e.source=='timeSecond')
    second.smooth_seconds=False
    generate_fprj(p,tmp_path)
    files={f.relative_to(tmp_path/'app').as_posix():f.read_bytes() for f in (tmp_path/'app').rglob('*') if f.is_file()}
    report=validate_injection(p,files)
    assert len(report['bindings'])==10
    assert [b['smooth'] for b in report['bindings'] if b['source']=='timeSecond']==[True,False]
    files['lua/studio_scene_data.lua']+=b'\n-- changed'
    with pytest.raises(ValueError,match='Runtime dei dati'):validate_injection(p,files)


def test_moon_only_scene_can_contain_a_live_calendar(tmp_path):
    p=mixed_project();p.elements=[e for e in p.elements if e.source=='studioMoon59' or labels_for(e)]
    add_moon(p)
    lua,data,core,_,_=runtime(tmp_path,p)
    assert not len(core.views) and len(data.views)==2
    lua.globals().emit('dateWeek',4*256)
    day=next(v for _,v in data.views.items() if v.config.source=='dateWeek')
    assert day.image.src.endswith('_calendar_4.png')


@pytest.mark.parametrize('source,limit',[('timeHour',24),('timeMinute',60),('timeSecond',60)])
def test_scene_civil_counter_fraction_never_rounds_to_next_tick(tmp_path,source,limit):
    p=mixed_project()
    # Add the ordinary minute hand too, within the same scene as the Pro hands.
    p.elements.insert(1,Element(kind='pointer',source='timeMinute',value_range=60))
    lua,data,_,_,_=runtime(tmp_path,p)
    v=next(v for _,v in data.views.items() if v.config.source==source)
    for whole in range(limit):
        for fractional_bits in (0,1,127,128,255):
            lua.globals().emit(source,whole*256+fractional_bits)
            assert v.value==whole
            assert v.hands[1].value==whole*v.config.scale
    last=v.hands[1].value
    for invalid in (-256,limit*256,2147483647,4294967295):
        lua.globals().emit(source,invalid)
        assert v.hands[1].value==last
        if v.animation:assert not v.animation.run


def test_normal_seconds_sweep_uses_s5_one_shot_and_restarts_each_real_tick(tmp_path):
    lua,data,_,_,_=runtime(tmp_path,mixed_project())
    v=next(v for _,v in data.views.items() if v.config.source=='timeSecond')
    animation=v.animation
    # Match the carrier and single-execution convention of the S5-tested Pro
    # transitions. The old mock allowed callbacks even for repeat_count=0.
    assert animation.repeat_count==1
    assert lua.eval('function(a,b)return a==b end')(animation.target.parent,v.root)
    assert (animation.target.w,animation.target.h)==(1,1)
    assert not animation.target.flags[2] and not animation.target.flags[3]
    lua.globals().A=animation
    lua.execute('''
      RESTARTS=0;STOPS=0;LAST_RUN=false
      local original=A.set
      function A:set(attrs)
        if attrs.run==false then STOPS=STOPS+1;LAST_RUN=false end
        if attrs.run==true and not LAST_RUN then RESTARTS=RESTARTS+1;LAST_RUN=true end
        original(self,attrs)
      end
      function frame(phase)
        if not A.run or A.repeat_count~=1 then return end
        A.exec_cb(A.target,phase)
        if phase>=A.end_value then A.run=false;LAST_RUN=false end
      end
    ''')
    for second in (57,58,59,0,1,2):
        # Notification may arrive while the preceding sweep is in flight.
        before=lua.globals().RESTARTS
        lua.globals().emit('timeSecond',second*256+192)
        assert lua.globals().RESTARTS==before+1 and animation.run
        for phase in range(0,1000,40):
            lua.globals().frame(phase)
            expected=round(((second+phase/1000)%60)*1000)
            assert all(h.value==expected for _,h in v.hands.items())
        # Duplicate notifications must not restart the animation.
        lua.globals().emit('timeSecond',second*256+255)
        assert lua.globals().RESTARTS==before+1
    lua.globals().frame(1000)
    assert not animation.run and v.hands[1].value==3000
    lua.globals().emit('timeSecond',3*256)
    assert animation.run and v.hands[1].value==3000
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    stopped=v.hands[1].writes;lua.globals().frame(400)
    assert v.hands[1].writes==stopped and not animation.run


@pytest.mark.parametrize('source,whole',[('timeHour24',14),('timeHour',23),('timeMinute',59),('timeSecond',59)])
def test_preview_small_civil_hands_use_whole_counters_like_export(source,whole):
    p=Project();e=Element(kind='pointer',source=source,value_range=24 if 'Hour' in source else 60,
                          width=180,height=180,smooth_seconds=source=='timeSecond')
    integer=png_bytes(element_image(p,e,{source:whole,'__secondFraction':0.4}))
    fractional=png_bytes(element_image(p,e,{source:whole+0.75,'__secondFraction':0.4}))
    assert integer==fractional
