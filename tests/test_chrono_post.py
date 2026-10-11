"""Execute the exported 2.0 Lua scene, including six measuring hands."""
import os,subprocess,zipfile
import xml.etree.ElementTree as ET
import pytest
from s5studio.model import Element,Project
from s5studio.motion import POST_SOURCES,excluded_from_aod
from s5studio.chrono_pro import ProPreview
from s5studio.lua_runtime import scene_layers,write_scene,interaction_report
from s5studio.native import generate_fprj
from s5studio.live_data import complete_aod_apps
from test_chrono_pro import pro_project,pro_runtime,start,finish,view,ROOT


def post_project(*,readout='fraction',arc=False,ccw=False,deci=True):
    p=pro_project(deci)
    p.elements[:0]=[Element(kind='pointer',source=source,post_readout=readout,
        value_range=8 if arc else 10 if readout=='digit' else period,
        pointer_arc=arc,angle_start=30 if arc else 0,
        angle_range=(-250 if ccw else 110) if arc else 360,
        smooth_seconds=True,x=70+i*100,y=80,width=80,height=80)
        for i,(source,(_,period)) in enumerate(POST_SOURCES.items())]
    return p


@pytest.mark.parametrize('readout',['fraction','digit'])
@pytest.mark.parametrize('elapsed',[1000,1001,1009,1010,1099,1100,1488,1999,3661456])
def test_post_freezes_one_timestamp_and_moves_only_after_stop(tmp_path,readout,elapsed):
    p,lua,core=pro_runtime(tmp_path,project=post_project(readout=readout))
    assert len(core.views)==8  # two civil hands + six measuring hands
    posts=[view(core,s) for s in POST_SOURCES]
    start(lua,core)
    before=[v.hands[1].writes for v in posts]
    lua.globals().TICK=core.started+elapsed;core.update(core,core.clock(core))
    assert [v.last for v in posts]==[0,0]
    assert [v.hands[1].writes for v in posts]==before
    core.tap(core)
    assert core.state=='reading' and core.elapsed==elapsed and core.runTimer.paused
    assert len(core.transition.entries)==2 and core.transitionAnimation.duration==720
    frozen={v.id:v.last for _,v in core.views.items() if v.source not in POST_SOURCES}
    lua.globals().TICK+=2000;core.update(core,core.clock(core));core.progress(core,500)
    assert core.elapsed==elapsed
    assert {v.id:v.last for _,v in core.views.items() if v.source not in POST_SOURCES}==frozen
    core.tap(core);assert core.state=='reading'
    finish(lua,core);assert core.state=='stopped'
    expected=[elapsed%1000//10,elapsed%1000]
    if readout=='digit':expected=[v%10 for v in expected]
    assert [v.last for v in posts]==expected
    lua.globals().TICK+=9000;core.update(core,core.clock(core))
    assert [v.last for v in posts]==expected
    core.tap(core);assert core.state=='resetting' and len(core.transition.entries)==6
    finish(lua,core);assert core.state=='rest' and [v.last for v in posts]==[0,0]


@pytest.mark.parametrize('ccw',[False,True])
def test_arc_stop_and_reset_stay_on_calibrated_scale_and_match_preview(tmp_path,ccw):
    p,lua,core=pro_runtime(tmp_path,project=post_project(readout='digit',arc=True,ccw=ccw))
    preview=ProPreview();preview.tap(p,0,47);preview.values(p,720,47);preview.tap(p,720,47)
    start(lua,core);lua.globals().TICK=core.started+1488;core.tap(core);preview.tap(p,2208,47)
    for phase in (0,100,250,500,750,900,1000):
        core.progress(core,phase);values=preview.values(p,2208+720*phase/1000,47)
        for source in POST_SOURCES:
            v=view(core,source)
            assert 0<=v.last<=8
            assert v.last==pytest.approx(values[v.id],abs=.001)
            assert v.hands[1].range.angleStart==300
            assert v.hands[1].range.angleRange==(-2500 if ccw else 1100)
    assert all(view(core,s).last==8 for s in POST_SOURCES)
    lua.globals().TICK+=1000;core.tap(core);preview.tap(p,3208,47)
    for phase in (0,200,500,900,1000):
        core.progress(core,phase);values=preview.values(p,3208+720*phase/1000,47)
        for source in POST_SOURCES:
            v=view(core,source);assert 0<=v.last<=8
            assert v.last==pytest.approx(values[v.id],abs=.001)
    assert preview.state==core.state=='rest'


@pytest.mark.parametrize('temporary',[False,True])
def test_post_transition_aod_cancel_and_touch_pause(tmp_path,temporary):
    p,lua,core=pro_runtime(tmp_path,project=post_project())
    start(lua,core);lua.globals().TICK=core.started+1456;core.tap(core);core.progress(core,300)
    core.screen(core,False,temporary)
    assert not core.transitionAnimation.run and core.runTimer.paused
    if temporary:
        assert core.state=='reading' and core.transition is not None
    else:
        assert core.state=='stopped' and core.transition is None
        assert all(v.root.flags[1] for _,v in core.views.items())
    core.screen(core,True,temporary)
    if temporary:core.progress(core,1000)
    assert core.state=='stopped' and core.elapsed==1456
    assert view(core,'studioChronoCentisecond').last==45
    assert view(core,'studioChronoMillisecond').last==456


def test_post_does_not_add_fast_timer_and_fallback_does_not_invent_milliseconds(tmp_path):
    p,lua,core=pro_runtime(tmp_path,fallback=True,project=post_project(deci=False))
    assert core.runTimer.period==1000
    core.tap(core);core.clockAnimation.exec_cb(core.root,0);core.clockAnimation.exec_cb(core.root,720)
    core.progress(core,1000);core.tapUnlockAnimation.exec_cb(core.root,1000);core.tap(core)
    core.clockAnimation.exec_cb(core.root,0);core.clockAnimation.exec_cb(core.root,1480)
    core.tapUnlockAnimation.exec_cb(core.root,1000);core.tap(core)
    assert core.elapsed==1480 and core.state=='reading'
    core.progress(core,1000)
    assert view(core,'studioChronoCentisecond').last==48
    assert view(core,'studioChronoMillisecond').last==480


def test_post_tick_wrap_same_time_for_all_six_hands(tmp_path):
    p,lua,core=pro_runtime(tmp_path,project=post_project())
    lua.globals().TICK=4294966000;start(lua,core)
    lua.globals().TICK=(core.started+3661999)%4294967296;core.tap(core);core.progress(core,1000)
    assert core.elapsed==3661999
    for source,expected in [('studioChronoHour',1),('studioChronoMinute',1),('studioChronoDecisecond',9),
                            ('studioIntegratedSecond',1),('studioChronoCentisecond',99),('studioChronoMillisecond',999)]:
        assert view(core,source).last==expected


def test_post_persistence_validation_and_aod_exclusion(tmp_path):
    p=post_project(readout='digit',arc=True,ccw=True);assert not p.validate()
    p.save(tmp_path/'post.s5faceproj');loaded=Project.load(tmp_path/'post.s5faceproj')
    assert loaded.elements[0].pointer_arc and loaded.elements[0].post_readout=='digit'
    main=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    main.visible=False;assert not p.validate()
    main.chrono_pro=False;assert any('POST' in e for e in p.validate())
    main.chrono_pro=True
    for e in p.elements[:2]:e.aod=True;assert excluded_from_aod(e)
    src=generate_fprj(p,tmp_path/'aod-source')
    assert not (tmp_path/'aod-source/AOD/app').exists()
    for invalid in (0,360,-360):
        p.elements[0].angle_range=invalid;assert p.validate()


def test_post_real_compiler_contains_scripts_and_reports_calibration(tmp_path):
    p=post_project(readout='digit',arc=True,ccw=True)
    source=generate_fprj(p,tmp_path/'source')
    output=tmp_path/'out';output.mkdir()
    compiler=ROOT/'tools/easyface-4.23/Compiler.exe'
    result=subprocess.run([str(compiler),'-b',str(source.project_path),str(output),'post.face','167210065'],
        cwd=compiler.parent,capture_output=True,stdin=subprocess.DEVNULL,timeout=30,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0 and b'No Errors' in result.stdout+result.stderr
    data=complete_aod_apps((output/'post.face').read_bytes(),source.project_path)
    report=interaction_report(p,data,b'<Watchface interactive="true"/>')
    assert report['chronoPro']['postReadout']['injected']
    assert len(report['chronoPro']['postReadout']['pointers'])==2
    assert not report['chronoPro']['postReadout']['millisecondAccuracyGuaranteed']
    assert report['chronoPro']['postReadout']['extraRunningTimers']==0
    assert report['chronoPro']['postReadout']['pointers'][0]['angleEnd']==140
    assert report['chronoPro']['postReadout']['pointers'][0]['angleRange']==-250
    from s5studio.native_graph import compose
    from s5studio.watchface_library import read_tables
    with zipfile.ZipFile(ROOT/'quadrante_funzionante.zip') as z:reference=z.read('resource.bin')
    preview=read_tables(data,0)[2][0][2]
    final,metadata=compose(data,p,reference,source.project_path.parent,[preview],{},{},aod_preview=preview)
    final_report=interaction_report(p,final,metadata['resources/manifest.xml'])
    assert final_report['chronoPro']['postReadout']['injected']
    assert b'interactive="true"' in metadata['resources/manifest.xml']
    assert metadata['app/lua/studio_core_pro.lua']==(ROOT/'s5studio/lua/studio_core_pro.lua').read_bytes()
