from pathlib import Path
import json,struct,zipfile,xml.etree.ElementTree as ET
import pytest
from s5studio.model import Project,Element,template,normalized_slot
from s5studio.motion import LUA_SOURCES
from s5studio.native import build,generate_fprj,inspect_binary
from s5studio.watchface_library import read_tables
from s5studio.lua_runtime import write_pointer,unpack_app
from s5studio.semantic_package import validate_package
from s5studio.selection import move,align
ROOT=Path(__file__).resolve().parents[1]


def test_group_move_preserves_offsets_at_edge_and_in_all_variants():
    p=Project(elements=[Element(x=20,y=40,width=40,height=40),Element(x=420,y=80,width=40,height=40)])
    p.variants.append({'id':'blue','name':'Blu','accent':'#ffffff','overrides':{p.elements[1].id:{'x':430}}})
    p.complications=[normalized_slot({'id':'slot','name':'Passi','x':50,'y':100,'width':60,'height':40,'options':['steps'],'default':'steps'})]
    ids=[e.id for e in p.elements]+['slot']
    assert move(p,ids,100,10)==(10,10)
    assert [e.x for e in p.elements]==[30,430] and p.complications[0]['x']==60
    assert p.variants[1]['overrides'][p.elements[1].id]['x']==440
    assert move(p,ids,-100,0)==(-30,0)
    assert [e.x for e in p.elements]==[0,400]


def test_group_align_and_variant_only_do_not_change_other_styles():
    p=Project(elements=[Element(x=50,y=80,width=40,height=40),Element(x=150,y=180,width=40,height=40)])
    p.variants.append({'id':'blue','name':'Blu','accent':'#ffffff','overrides':{}})
    ids=[e.id for e in p.elements]
    align(p,ids,'center-x',variant=1,variant_only=True)
    assert [e.x for e in p.elements]==[50,150]
    assert [e.x for e in p.variant_project(1).elements]==[170,270]
    assert p.variant_project(1).elements[1].y-p.variant_project(1).elements[0].y==100
    p.elements[1].locked=True
    before=p.metadata()
    with pytest.raises(ValueError,match='Sblocca'):move(p,ids,1,1)
    assert before==p.metadata()
    with pytest.raises(ValueError):move(p,[ids[0],ids[0]],1,1)


def test_aod_removes_all_second_and_lua_small_hands_even_in_variants(tmp_path):
    p=template('Analogico')
    for source in ('second','timeSecond','timeSecondLow','timeSecondHigh',*LUA_SOURCES):
        p.elements.append(Element(kind='pointer',source=source,aod=True,x=10,y=10,width=80,height=80))
    p.elements[-1].visible=False
    p.variants[0]['overrides']={p.elements[-1].id:{'visible':True}}
    source=generate_fprj(p,tmp_path)
    aod=ET.parse(tmp_path/'AOD/quadrante.fprj').getroot()
    assert not any(w.get('Name','').startswith(('pointer_','app_')) for w in aod.iter('Widget'))
    assert not any(w.get('SecondHand_Image') for w in aod.iter('Widget'))
    assert not (tmp_path/'AOD/app').exists()


def lua_runtime():
    from lupa import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
        TICK=0
        local object={}
        function object:set(t) for k,v in pairs(t) do self[k]=v end end
        function object:add_flag(f) self.flags[f]=true end
        function object:clear_flag(f) self.flags[f]=false end
        function object:onevent(code,cb) self.events[code]=cb end
        function object:pause() self.paused=true end
        function object:resume() self.paused=false end
        function object:Anim(attrs)
            local a=make(nil,attrs);a.target=self;self.animation=a;return a
        end
        function make(parent,attrs)
            local o={flags={},events={}};setmetatable(o,{__index=object});o:set(attrs)
            if parent then parent.children=parent.children or {};table.insert(parent.children,o) end
            return o
        end
        LV={Object=make,FLAG={HIDDEN=1,CLICKABLE=2,SCROLLABLE=3},EVENT={CLICKED=4,DELETE=5,PRESSED=6},
            Timer=function(attrs) return make(nil,attrs) end,tick_get=function()return TICK end}
        package.preload.lvgl=function()return LV end
        debug.getregistry().widgets={__index={Pointer=make}}
        SCRIPT_PATH='/fake/app/lua/'
    ''')
    core=lua.execute((ROOT/'s5studio/lua/studio_core.lua').read_text(encoding='utf8'))
    lua.globals().CORE=core;lua.execute('package.loaded.studio_core=CORE')
    return lua,core


def test_actual_lua_start_stop_reset_shared_hands_deciseconds_and_screen_lifecycle(tmp_path):
    lua,core=lua_runtime();p=Project()
    for index,source in enumerate(LUA_SOURCES):
        e=Element(kind='pointer',source=source,smooth_seconds=source=='studioChronoSecond',value_range=LUA_SOURCES[source][1],x=80+index*80,y=100,width=80,height=80)
        p.elements.append(e);name=write_pointer(p,e,tmp_path,0)
        lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert len(core.views)==4
    lua.globals().TICK=1000;core.tap(core);assert core.state=='running'
    lua.globals().TICK=3723456;core.update(core,3723456)
    deci=core.views[1].animation;deci.exec_cb(deci.target,456)
    assert core.views[1].hands[1].value==4
    assert core.views[2].hands[1].value==1
    assert core.views[3].hands[1].value==2
    assert core.views[4].hands[1].value==pytest.approx(2.456)
    core.tap(core);assert core.state=='stopped'
    frozen=core.views[4].hands[1].value
    lua.globals().TICK=9999999;core.update(core,9999999)
    assert core.views[4].hands[1].value==frozen
    core.tap(core);assert core.state=='reset'
    assert all(core.views[i].hands[1].value==0 for i in (2,3,4))
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    assert not deci.run
    assert core.timer.paused and all(core.views[i].root.flags[1] for i in range(1,5))
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert deci.run
    assert not core.timer.paused and all(not core.views[i].root.flags[1] for i in range(1,5))
    lua.globals().pageOnPause();assert core.timer.paused
    lua.globals().pageOnResume();assert not core.timer.paused
    # The same core instance is returned to every script in a VM.
    assert lua.eval('require("studio_core")==CORE')


def test_lua_unavailable_clock_does_not_start_and_never_counts_callback_invocations():
    lua,core=lua_runtime();lua.execute('LV.tick_get=nil;io.open=function()return nil end;os.time=nil')
    core.tap(core);assert core.state=='reset'
    core.update(core,None);assert core.elapsed==0


def test_lua_monotonic_time_includes_sleep_and_procfs_fallback():
    lua,core=lua_runtime();lua.execute('CORE:add {root=make(nil,{}),hands={},source="studioChronoSecond",range=60}')
    lua.globals().TICK=1000;core.tap(core)
    lua.globals().pageOnPause();lua.globals().TICK=11000
    assert core.timer.paused
    lua.globals().pageOnResume();assert core.value(core,11000)==10000
    # A clock source is selected once; never change origins mid-chronograph.
    lua.execute('LV.tick_get=nil;io.open=function()return {read=function()return "   123.45" end,close=function()end} end')
    assert core.clock()==11000 and core.clockMode=='lvgl-monotonic'
    lua,core=lua_runtime()
    lua.execute('LV.tick_get=nil;io.open=function()return {read=function()return "   123.45" end,close=function()end} end')
    assert core.clock()==123450


@pytest.mark.parametrize('smooth',[False,True])
def test_decisecond_animation_without_any_exported_clock_drives_main_and_shadow(tmp_path,smooth):
    lua,core=lua_runtime()
    lua.execute('LV.tick_get=nil;io=nil;os=nil')
    p=Project();e=Element(kind='pointer',source='studioDecisecond',value_start=5,value_range=60,smooth_seconds=smooth)
    p.elements=[e];name=write_pointer(p,e,tmp_path,0)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    view=core.views[1];anim=view.animation
    assert core.timer is None and anim.run and anim.duration==1000 and anim.repeat_count==-1
    assert anim.path=='linear' and anim.start_value==0 and anim.end_value==1000
    # LVGL supplies elapsed phase, rather than counting callback invocations.
    for phase in (0,250,999,1000,1200):
        anim.exec_cb(anim.target,phase)
        tenth=(phase%1000)/100
        if not smooth:tenth=int(tenth)
        expected=5+tenth/10*60
        assert all(view.hands[i].value==pytest.approx(expected) for i in range(1,len(view.hands)+1))
    before=view.hands[1].value
    core.screen(core,False);assert not anim.run and view.root.flags[1]
    anim.exec_cb(anim.target,700);assert view.hands[1].value==before
    core.screen(core,True);assert anim.run and not view.root.flags[1]
    view.root.events[5]();assert not anim.run and len(core.views)==0


def test_chrono_full_face_tap_works_with_wall_clock_fallback_and_freezes_after_stop(tmp_path):
    lua,core=lua_runtime()
    lua.execute('LV.tick_get=nil;io.open=function()error("not permitted")end;WALL=100;os.time=function()return WALL end')
    p=Project()
    for source in ('studioChronoHour','studioChronoMinute','studioChronoSecond'):
        e=Element(kind='pointer',source=source,value_range=LUA_SOURCES[source][1],x=266,y=175,width=130,height=130)
        p.elements.append(e);name=write_pointer(p,e,tmp_path,0)
        lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
        text=(tmp_path/'app'/name).read_text(encoding='utf8')
        assert 'local tap = lvgl.Object(root, {x=0,y=0,w=480,h=480' in text
    # The generated touch handler invokes the shared core, not a mock tap.
    lua.execute('local root=CORE.views[3].root;TAP=root.children[#root.children]')
    lua.execute('TAP.events[LV.EVENT.PRESSED]()')
    assert core.state=='running' and core.clockMode=='wall-second'
    lua.globals().WALL=3763;core.update(core,core.clock())
    assert [core.views[i].hands[1].value for i in (1,2,3)]==[1,1,3]
    lua.execute('TAP.events[LV.EVENT.PRESSED]()');assert core.state=='stopped'
    lua.globals().WALL=9999;core.update(core,core.clock())
    assert core.views[3].hands[1].value==3
    lua.execute('TAP.events[LV.EVENT.PRESSED]()');assert core.state=='reset'
    assert core.views[3].hands[1].value==0


def test_touch_during_page_pause_is_retained_once_but_aod_touches_are_ignored(tmp_path):
    lua,core=lua_runtime();p=Project();e=Element(kind='pointer',source='studioChronoSecond',value_range=60)
    name=write_pointer(p,e,tmp_path,0);lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    lua.execute('local root=CORE.views[1].root;TAP=root.children[#root.children]')
    lua.globals().pageOnPause()
    assert not core.active and not core.views[1].root.flags[1]
    lua.execute('TAP.events[LV.EVENT.PRESSED]()')
    assert core.pendingTap and core.state=='reset'
    lua.globals().TICK=1000;lua.globals().pageOnResume()
    assert core.state=='running' and not core.pendingTap
    core.update(core,4000);assert core.views[1].hands[1].value==3
    lua.globals().pageOnResume();assert core.state=='running'
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    lua.execute('TAP.events[LV.EVENT.PRESSED]()')
    assert not core.pendingTap and core.views[1].root.flags[1]
    lua.globals().pageOnResume();assert not core.active
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert core.state=='running' and core.active


@pytest.mark.parametrize('failure',[False,True])
def test_qthread_completion_clears_busy_once_without_rendering_gallery(tmp_path,monkeypatch,failure):
    import time
    from PySide6.QtWidgets import QApplication,QMainWindow
    from s5studio import web_ui
    app=QApplication.instance() or QApplication([]);win=QMainWindow();bridge=web_ui.StudioBridge(win,smoke=True)
    def compile(*args):
        if failure:raise ValueError('Errore fixture')
        return tmp_path
    monkeypatch.setattr(web_ui,'build',compile)
    def render_state():raise AssertionError('La notifica di fine non deve renderizzare le anteprime')
    monkeypatch.setattr(bridge,'state',render_state)
    events=[];bridge.event.connect(lambda raw:events.append(json.loads(raw)))
    worker=web_ui.BuildTask(bridge.project,bridge.compiler,tmp_path)
    bridge.worker=worker;worker.finished.connect(bridge.build_finished);worker.start()
    deadline=time.monotonic()+5
    while bridge.worker is not None and time.monotonic()<deadline:app.processEvents()
    assert bridge.worker is None and len(events)==1
    event=events[0];assert event['buildStatus']['busy'] is False and 'state' not in event
    assert event['buildDone'] is not failure
    assert event['error']==('Errore fixture' if failure else '')
    assert event['buildStatus']['output']==('' if failure else str(tmp_path))
    win.close();app.processEvents()


def test_bridge_group_move_is_one_undo_and_rejects_locked_or_missing_layers():
    from PySide6.QtWidgets import QApplication,QMainWindow
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);win=QMainWindow();bridge=StudioBridge(win,smoke=True)
    bridge.project=Project(elements=[Element(x=60,y=80,width=40,height=40),Element(x=200,y=150,width=40,height=40)])
    ids=[e.id for e in bridge.project.elements]
    result=json.loads(bridge.command(json.dumps({'action':'move-group','ids':ids,'dx':10,'dy':20})))
    assert not result.get('error') and len(bridge.undo_stack)==1
    assert [(e.x,e.y) for e in bridge.project.elements]==[(70,100),(210,170)]
    bridge.command(json.dumps({'action':'undo'}));assert [(e.x,e.y) for e in bridge.project.elements]==[(60,80),(200,150)]
    bridge.project.elements[1].locked=True;before=bridge.project.metadata()
    result=json.loads(bridge.command(json.dumps({'action':'move-group','ids':ids,'dx':10,'dy':20})))
    assert result.get('error') and bridge.project.metadata()==before
    result=json.loads(bridge.command(json.dumps({'action':'move-group','ids':['missing'],'dx':10,'dy':20})))
    assert result.get('error') and bridge.project.metadata()==before


@pytest.mark.integration
def test_real_compiler_sweep_lua_all_variants_aod_and_report_tampering(tmp_path):
    p=template('Analogico');p.elements[0].smooth_seconds=True
    p.variants.append({'id':'blue','name':'Blu','accent':'#ffffff','background':'','imageAsset':'','overrides':{}})
    for source in LUA_SOURCES:
        p.elements.append(Element(kind='pointer',source=source,value_range=LUA_SOURCES[source][1],x=100,y=100,width=80,height=80))
    p.elements.append(Element(kind='pointer',source='timeSecond',smooth_seconds=True,x=280,y=100,width=80,height=80))
    p.elements.append(Element(kind='pointer',source='timeSecond',smooth_seconds=True,aod=True,x=100,y=100,width=80,height=80))
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    archive=next(output.glob('*_TEMPLATE.zip'));data=(output/'resource.bin').read_bytes();info=inspect_binary(data)
    with zipfile.ZipFile(archive) as z:
        report=json.loads(z.read('build-report.json'));assert report['interactive']['injected']
        assert report['interactive']['appLayoutCount']==8
        assert ET.fromstring(z.read('resources/manifest.xml')).get('interactive')=='true'
        for screen in info['screens']:
            tables=read_tables(data,screen['index'])
            seconds=[b for _,_,b in tables[7] if b[:2]==bytes.fromhex('1811') and b[3]>>4==3]
            if screen['aod']:assert not seconds and not tables[5]
            else:
                assert len(seconds)==2 and all(struct.unpack_from('<H',b,6)[0]==40 for b in seconds)
                for _,_,b in tables[5]:
                    name,content=unpack_app(b);assert z.read('app/'+name)==content
    assert validate_package(ROOT/'quadrante_funzionante.zip',archive)['status']=='passed'
    tampered=tmp_path/'tampered.zip'
    with zipfile.ZipFile(archive) as src,zipfile.ZipFile(tampered,'w') as dst:
        for item in src.infolist():
            b=src.read(item)
            if item.filename=='build-report.json':
                r=json.loads(b);r['interactive']['injected']=False;b=json.dumps(r).encode()
            dst.writestr(item,b)
    with zipfile.ZipFile(tampered) as z:
        from s5studio.semantic_package import validate_semantics
        with pytest.raises(ValueError,match='Rapporto'):validate_semantics(z)
