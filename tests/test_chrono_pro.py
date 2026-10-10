import hashlib,json,zipfile,struct
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from s5studio.model import Element,Project,template
from s5studio.motion import pro_enabled
from s5studio.lua_runtime import scene_layers,write_scene,scene_bindings,unpack_app
from s5studio.native import generate_fprj,build,inspect_binary
from s5studio.watchface_library import read_tables
from s5studio.semantic_package import validate_package,validate_semantics
from test_motion_interaction import lua_runtime

ROOT=Path(__file__).resolve().parents[1]


def pro_project(deci=True):
    p=template('Analogico');p.elements[0].chrono_pro=True;p.elements[0].smooth_seconds=True
    sources=[('studioChronoHour',12),('studioChronoMinute',60)]
    if deci:sources.append(('studioChronoDecisecond',10))
    p.elements[:0]=[Element(kind='pointer',source=s,value_range=r,smooth_seconds=True,
                          x=90+i*100,y=180,width=80,height=80) for i,(s,r) in enumerate(sources)]
    return p


def pro_runtime(tmp_path,*,fallback=False,deci=True,hide_main=False):
    lua,_=lua_runtime()
    lua.execute('''
        DATA={}
        package.preload.dataman=function() return {subscribe=function(name,obj,cb)
            DATA[name]=function(value) cb(obj,value) end
        end} end
        local object=getmetatable(make(nil,{})).__index
        local oldset=object.set
        function object:set(t) self.writes=(self.writes or 0)+1;oldset(self,t) end
    ''')
    if fallback:lua.execute('LV.tick_get=nil;io.open=function()return nil end;WALL=1000;os.time=function()return WALL end')
    core=lua.execute((ROOT/'s5studio/lua/studio_core_pro.lua').read_text(encoding='utf8'))
    lua.globals().PRO=core;lua.execute('package.loaded.studio_core_pro=PRO')
    p=pro_project(deci)
    if hide_main:next(e for e in p.elements if e.kind=='analog' and not e.aod).visible=False
    name=write_scene(p,scene_layers(p),tmp_path,0)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    lua.execute('DATA.timeHour(14*256);DATA.timeMinute(8*256);DATA.timeSecond(47*256)')
    return p,lua,core


def view(core,source):
    return next(v for _,v in core.views.items() if v.source==source)


def finish(lua,core):
    lua.globals().TICK+=core.transitionMs+80
    core.progress(core,1000)


def start(lua,core):
    core.tap(core);assert core.state=='arming'
    finish(lua,core);assert core.state=='ready'
    core.tap(core);assert core.state=='running'


@pytest.mark.parametrize('deci',[False,True])
def test_pro_running_is_quantized_cached_and_all_rollovers_work(tmp_path,deci):
    p,lua,core=pro_runtime(tmp_path,deci=deci)
    assert core.state=='rest' and view(core,'studioIntegratedSecond').last==47
    start(lua,core);assert core.runTimer.period==(100 if deci else 1000)
    assert core.restTimer.paused
    base=core.started
    for elapsed in (99,100,456,1000,59999,60000,65000,3600000,3661456,43200000):
        lua.globals().TICK=base+elapsed;core.update(core,base+elapsed)
        assert view(core,'studioIntegratedSecond').last==(elapsed//1000)%60
        assert view(core,'studioChronoMinute').last==(elapsed//60000)%60
        assert view(core,'studioChronoHour').last==(elapsed//3600000)%12
        if deci:assert view(core,'studioChronoDecisecond').last==(elapsed%1000)//100
        current={v.id:v.hands[1].writes for _,v in core.views.items()}
        core.update(core,base+elapsed)
        assert {v.id:v.hands[1].writes for _,v in core.views.items()}==current
    core.tap(core);assert core.state=='stopped' and core.runTimer.paused
    frozen={v.id:v.last for _,v in core.views.items()}
    lua.globals().TICK+=10000;core.update(core,lua.globals().TICK)
    assert {v.id:v.last for _,v in core.views.items()}==frozen


@pytest.mark.parametrize('smooth',[False,True])
def test_pro_all_reset_hands_sweep_together_and_return_to_latest_civil_time(tmp_path,smooth):
    p,lua,core=pro_runtime(tmp_path)
    for _,v in core.views.items():v.smooth=smooth
    start(lua,core);lua.globals().TICK=core.started+3661456;core.tap(core)
    lua.globals().TICK+=500;core.tap(core);assert core.state=='resetting'
    assert len(core.transition.entries)==4 and core.transitionAnimation.duration==720
    starts={e.view.id:e.start for _,e in core.transition.entries.items()}
    lua.execute('DATA.timeSecond(52*256)')
    core.progress(core,500)
    for _,e in core.transition.entries.items():
        assert e.view.last!=starts[e.view.id]
        assert e.view.hands[1].value==pytest.approx(e.view.last*e.view.scale)
        assert e.view.hands[1].value==int(e.view.hands[1].value)
    assert view(core,'studioChronoDecisecond').last==pytest.approx(8.5)
    finish(lua,core)
    assert core.state=='rest'
    for s in ('studioChronoHour','studioChronoMinute','studioChronoDecisecond'):assert view(core,s).last==0
    assert int(view(core,'studioIntegratedSecond').last)==52


@pytest.mark.parametrize('state',['arming','ready','running','stopped','resetting'])
def test_pro_aod_immediately_cancels_animation_and_never_processes_hidden_taps(tmp_path,state):
    p,lua,core=pro_runtime(tmp_path)
    core.tap(core)
    if state!='arming':finish(lua,core)
    if state in ('running','stopped','resetting'):core.tap(core)
    if state in ('stopped','resetting'):
        lua.globals().TICK+=65456;core.tap(core)
    if state=='resetting':lua.globals().TICK+=400;core.tap(core)
    assert core.state==state
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    assert not core.active and not core.transitionAnimation.run
    assert core.root.flags[1]
    assert core.runTimer.paused and core.restTimer.paused
    assert all(v.root.flags[1] for _,v in core.views.items())
    before={v.id:v.last for _,v in core.views.items()};expected=core.state
    core.progress(core,1000);core.tap(core);core.update(core,9999999)
    assert core.state==expected and {v.id:v.last for _,v in core.views.items()}==before
    lua.globals().TICK+=10000
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert all(not v.root.flags[1] for _,v in core.views.items())
    assert core.transition is None


def test_pro_wall_fallback_uses_animation_phase_for_real_visible_decisecond_steps(tmp_path):
    p,lua,core=pro_runtime(tmp_path,fallback=True)
    assert core.clockMode=='lvgl-animation-phase'
    core.tap(core);core.clockAnimation.exec_cb(core.root,0);core.clockAnimation.exec_cb(core.root,720)
    core.progress(core,1000)
    core.tapUnlockAnimation.exec_cb(core.root,1000);core.tap(core);assert core.state=='running'
    core.clockAnimation.exec_cb(core.root,0);core.clockAnimation.exec_cb(core.root,456)
    core.update(core,core.clock(core))
    assert view(core,'studioChronoDecisecond').last==4
    core.clockAnimation.exec_cb(core.root,60000);core.clockAnimation.exec_cb(core.root,0)
    core.clockAnimation.exec_cb(core.root,1000);core.update(core,core.clock(core))
    assert view(core,'studioChronoMinute').last==1
    lua.globals().ScreenStateChangedCB('ON','AOD',0);lua.globals().WALL+=20
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert core.elapsed>=81000
    core.tapUnlockAnimation.exec_cb(core.root,1000);core.tap(core);assert core.state=='stopped'
    core.tapUnlockAnimation.exec_cb(core.root,1000);core.tap(core);assert core.state=='resetting'


def test_pro_tick_wrap_and_touch_pause_preserve_state(tmp_path):
    p,lua,core=pro_runtime(tmp_path)
    lua.globals().TICK=4294967000;start(lua,core)
    # start() uses an unbounded test integer; cross the actual uint32 boundary.
    lua.globals().TICK=(lua.globals().TICK+250)%4294967296;core.update(core,core.clock(core))
    assert core.elapsed>=100
    lua.globals().pageOnPause();core.tap(core);assert core.pendingTap
    lua.globals().TICK+=400;lua.globals().pageOnResume()
    assert core.state=='stopped' and not core.pendingTap


@pytest.mark.parametrize('angle_range',[360,180,-360,-180,720])
def test_all_transition_frames_are_physically_clockwise_even_on_partial_or_reversed_dials(tmp_path,angle_range):
    p,lua,core=pro_runtime(tmp_path)
    small=view(core,'studioChronoMinute');small.angleRange=angle_range;small.angleStart=30
    for _,hand in small.hands.items():hand.range.angleRange=angle_range*10;hand.range.angleStart=300
    def angles():
        result={}
        for _,v in core.views.items():
            if v.source in ('studioTimeHour','studioTimeMinute'):continue
            h=v.hands[1];r=h.range
            result[v.id]=(r.angleStart+(h.value-r.valueStart)*r.angleRange/r.valueRange)/10%360
        return result
    def sweep():
        previous=angles();travel={key:0 for key in previous}
        for phase in range(0,1001,50):
            core.progress(core,phase);current=angles()
            for key,a in current.items():
                delta=(a-previous[key])%360
                assert delta<180,(key,phase,delta)
                travel[key]+=delta
            previous=current
        return travel
    core.tap(core);travel=sweep()
    # Preparing 47 -> 60/0 advances clockwise by 78 degrees.
    assert travel[view(core,'studioIntegratedSecond').id]==pytest.approx(78,abs=.1)
    lua.globals().TICK+=400;core.tap(core);assert core.state=='running'
    lua.globals().TICK=core.started+3661456;core.tap(core)
    lua.globals().TICK+=400;core.tap(core);assert core.state=='resetting'
    travel=sweep();assert core.state=='rest'
    assert travel[view(core,'studioChronoHour').id]==pytest.approx(330,abs=.1)
    assert travel[view(core,'studioChronoDecisecond').id]==pytest.approx(216,abs=.1)
    assert small.hands[1].range.angleRange==angle_range*10
    assert small.hands[1].range.angleStart==300 and not small.transitionAngle


def test_mixed_classic_and_pro_scenes_have_only_the_current_controller_active(tmp_path):
    p,lua,core=pro_runtime(tmp_path)
    classic=p.copy();classic.variants=[]
    classic.elements=[e for e in classic.elements if e.kind=='pointer' and e.source!='studioChronoDecisecond']
    name=write_scene(classic,scene_layers(classic),tmp_path,1)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert not core.active and not core.currentScene and core.root.flags[1]
    assert lua.globals().CORE.active
    lua.globals().ScreenStateChangedCB('OFF','ON',0)
    assert not core.active and lua.globals().CORE.active
    name=write_scene(p,scene_layers(p),tmp_path,2);lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert core.active and core.currentScene and not lua.globals().CORE.active
    lua.globals().ScreenStateChangedCB('OFF','ON',0)
    assert core.active and not lua.globals().CORE.active
    core.root.events[5]()
    name=write_scene(classic,scene_layers(classic),tmp_path,3)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert lua.globals().CORE.active and len(lua.globals().CORE.views)==2


@pytest.mark.parametrize('transition',['arming','resetting'])
def test_touch_pause_does_not_skip_the_mandatory_sweep(tmp_path,transition):
    p,lua,core=pro_runtime(tmp_path)
    if transition=='resetting':
        start(lua,core);lua.globals().TICK+=65456;core.tap(core)
        lua.globals().TICK+=400
    core.tap(core);assert core.state==transition
    core.progress(core,250)
    pose={v.id:v.last for _,v in core.views.items()}
    lua.globals().pageOnPause()
    assert core.state==transition and core.transition is not None
    assert not core.transitionAnimation.run and not core.root.flags[1]
    core.tap(core);assert not core.pendingTap
    core.progress(core,1000)
    assert {v.id:v.last for _,v in core.views.items()}==pose
    lua.globals().TICK+=1000;lua.globals().pageOnResume()
    assert core.state==transition and core.transitionAnimation.run
    assert all(e.start==pose[e.view.id] for _,e in core.transition.entries.items())
    finish(lua,core)
    assert core.state==('ready' if transition=='arming' else 'rest')


def test_pro_save_load_defaults_and_single_scene_geometry(tmp_path):
    p=pro_project();assert not p.validate()
    p.save(tmp_path/'pro.s5faceproj');loaded=Project.load(tmp_path/'pro.s5faceproj')
    assert pro_enabled(loaded)
    source=generate_fprj(p,tmp_path/'source')
    widgets=list(ET.parse(source.project_path).iter('Widget'))
    assert sum(w.get('Shape')=='34' for w in widgets)==1
    assert not any(w.get('SecondHand_Image') for w in widgets)
    assert not (tmp_path/'source/AOD/app').exists()
    old=Element.from_dict({'kind':'analog','second_hand':True});assert not old.chrono_pro
    assert all('chrono_pro' not in e for e in template('Analogico').metadata()['elements'])
    p.elements[3].chrono_pro=False
    assert any('Decimi crono' in error for error in p.validate())


def test_pro_scene_change_and_delete_do_not_leave_old_callbacks_in_control(tmp_path):
    p,lua,core=pro_runtime(tmp_path,fallback=True)
    old=core.root;oldtimer=core.runTimer;oldanimation=core.transitionAnimation
    name=write_scene(p,scene_layers(p),tmp_path,1)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert core.root!=old and len(core.views)==6 and oldtimer.paused
    assert not oldanimation.run
    # Old scene deletion and stale callbacks must not destroy or move the new one.
    old.events[5]();oldtimer.cb();oldanimation.exec_cb(oldanimation.target,1000)
    assert core.configured and len(core.views)==6
    assert lua.eval('PRO.clockAnimation.target ~= PRO.transitionAnimation.target')
    assert lua.eval('PRO.tapUnlockAnimation.target ~= PRO.transitionAnimation.target')
    core.root.events[5]();assert not core.configured and len(core.views)==0
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    assert core.configured and core.active and len(core.views)==6


def assert_pro_canvas_matches_scene(project,main,directory):
    from PIL import Image
    from s5studio.render import element_image,hand_image,hand_shadow_offset
    from s5studio.lua_runtime import pro_views
    name=write_scene(project,scene_layers(project),directory,0)
    code=(directory/'app'/name).read_text(encoding='utf8')
    expected=Image.new('RGBA',(480,480))
    angles=(64,48,282)  # 14:08:47
    cx,cy=main.x+main.width//2,main.y+main.height//2
    for hand,view,angle in zip(('hour','minute','second'),pro_views(main),angles):
        for shadow in ([True,False] if main.show_shadows else [False]):
            path=f'gfx/v0_{main.id}_{hand}'+('_shadow' if shadow else '')+'.png'
            pair=hand_image(view,'second',project,shadow=shadow)
            if pair is None:continue
            bitmap,anchor=pair
            with Image.open(directory/'app/lua'/path) as image:
                assert image.size==bitmap.size
                assert image.convert('RGBA').tobytes()==bitmap.tobytes()
            dx,dy=hand_shadow_offset(view,'second',project) if shadow else (0,0)
            center=(cx+dx,cy+dy);x,y=center[0]-anchor[0],center[1]-anchor[1]
            assert f'x={x},y={y},pivot={{x={anchor[0]},y={anchor[1]}}},value=0,src=SCRIPT_PATH.."{path}"' in code
            layer=Image.new('RGBA',(480,480));layer.alpha_composite(bitmap,(x,y))
            expected.alpha_composite(layer.rotate(-angle,resample=Image.Resampling.BICUBIC,center=center))
    with Image.open(directory/f'app/lua/gfx/v0_{main.id}_center.png') as dot:
        expected.alpha_composite(dot.convert('RGBA'),(cx-7,cy-7))
    actual=element_image(project,main,{'hour':14,'minute':8,'second':47},viewport=(480,480),origin=(main.x,main.y))
    assert actual.tobytes()==expected.tobytes()


@pytest.mark.parametrize('length_adjusted,width_adjusted',[(False,False),(True,False),(False,True),(True,True)])
def test_pro_preview_matches_exported_hands_colour_and_shadow_offsets(tmp_path,length_adjusted,width_adjusted):
    from PIL import Image
    from io import BytesIO
    p=pro_project();main=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    main.show_ticks=False;main.show_shadows=True
    for index,hand in enumerate(('hour','minute','second')):
        raw=BytesIO();Image.new('RGBA',(12+index,50+index),(190,100,40,220)).save(raw,'PNG');data=raw.getvalue()
        asset='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';p.assets[asset]=data
        for suffix in ('','_shadow'):
            setattr(main,hand+suffix+'_asset',asset)
            setattr(main,hand+suffix+'_anchor_x',3+index);setattr(main,hand+suffix+'_anchor_y',45+index)
        setattr(main,hand+'_color','#3344ff');setattr(main,hand+'_length_adjusted',length_adjusted)
        setattr(main,hand+'_width_adjusted',width_adjusted);setattr(main,hand+'_shadow_offset_x',index+2)
    assert_pro_canvas_matches_scene(p,main,tmp_path)


def nasa_minute_graphic(project):
    """Reproduce the NASA canvas, pivot and untouched length=10 setting."""
    from PIL import Image,ImageDraw
    from io import BytesIO
    main=next(e for e in project.elements if e.kind=='analog' and not e.aod)
    for suffix,size,anchor,box in (('',(40,480),(20,240),(5,33,34,294)),
                                  ('_shadow',(52,480),(26,240),(0,27,51,300))):
        image=Image.new('RGBA',size);ImageDraw.Draw(image).rectangle(box,fill=(210,170,100,180))
        raw=BytesIO();image.save(raw,'PNG');data=raw.getvalue()
        asset='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';project.assets[asset]=data
        setattr(main,'minute'+suffix+'_asset',asset)
        for axis,value in zip(('x','y'),anchor):setattr(main,'minute'+suffix+'_anchor_'+axis,value)
    main.minute_length=10;main.minute_width=5
    main.minute_length_adjusted=False;main.minute_width_adjusted=False
    main.minute_color='#ffffff';main.minute_shadow_offset_y=7;main.show_shadows=True
    return main


def test_pro_nasa_preview_is_correct_on_first_render_without_touching_controls(tmp_path):
    from s5studio.lua_runtime import pro_views
    from s5studio.render import hand_image
    p=pro_project();main=nasa_minute_graphic(p);main.show_ticks=False
    minute=pro_views(main)[1]
    bitmap,anchor=hand_image(minute,'second',p)
    assert bitmap.size==(5,46) and anchor==(3,36)
    assert not main.minute_length_adjusted and main.minute_length==10
    assert_pro_canvas_matches_scene(p,main,tmp_path)
    # The preview follows subsequent edits too; it never changes project flags.
    main.minute_length=55;main.minute_length_adjusted=True
    assert_pro_canvas_matches_scene(p,main,tmp_path)
    assert main.minute_length==55 and main.minute_length_adjusted


@pytest.mark.integration
def test_pro_real_compiler_variants_aod_package_and_report(tmp_path,monkeypatch):
    p=pro_project();p.variants.append({'id':'blue','name':'Blu','accent':'#ffffff','background':'','imageAsset':'','overrides':{}})
    main=nasa_minute_graphic(p)
    from s5studio import native_graph
    encoded={};factory=native_graph.preview_factory
    def capture(project,work,compiler,progress):
        result=factory(project,work,compiler,progress);encoded['normal'],encoded['aod']=result
        return result
    monkeypatch.setattr(native_graph,'preview_factory',capture)
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    archive=next(output.glob('*_TEMPLATE.zip'));data=(output/'resource.bin').read_bytes()
    from s5studio.watchface_library import directory_bases
    for index,base in enumerate(directory_bases(data)):
        expected=encoded['aod'] if index%2 else encoded['normal'][index//2]
        if index%2:
            assert any(b==expected for _,_,b in read_tables(data,index)[2])
        else:
            pos=struct.unpack_from('<I',data,base+4)[0]
            assert data[pos:pos+len(expected)]==expected
    from PIL import Image
    # Runtime Lua hands and every visible layer are rasterized before encoding.
    with zipfile.ZipFile(archive) as z:
        config=json.loads(z.read('editor.config.json'))
        assert json.loads(z.read('s5studio-schema.json'))['phonePreview']['staticOnly']
        for theme in config['themes']:
            assert theme['preview'].startswith('_preview/') and 'previewAni' not in theme
            assert config['formats'][theme['preview']]=='indexed8'
            for child in theme['children']:
                if child['type']=='Image':
                    path=child['attrs']['resources']['pointer0']['studio'][0]
                    assert 'resources/'+path in z.namelist() and config['formats'][path]=='indexed8'
        from s5studio.render import hand_image
        from s5studio.lua_runtime import pro_views
        from io import BytesIO
        for i in range(len(p.variants)):
            variant=p.variant_project(i)
            minute=pro_views(next(e for e in variant.elements if e.id==main.id))[1]
            for shadow in (False,True):
                expected,_=hand_image(minute,'second',variant,shadow=shadow)
                path=f'app/lua/gfx/v{i}_{main.id}_minute'+('_shadow' if shadow else '')+'.png'
                with Image.open(BytesIO(z.read(path))) as image:
                    assert image.size==expected.size
                    assert image.convert('RGBA').tobytes()==expected.tobytes()
        for i,theme in enumerate(t for t in config['themes'] if t['type']=='normal'):
            from io import BytesIO
            from s5studio.render import render
            with Image.open(BytesIO(z.read('resources/'+theme['preview']))) as preview:
                assert preview.convert('RGB').tobytes()==render(p.variant_project(i),circular=False).convert('RGB').tobytes()
    with zipfile.ZipFile(archive) as z:
        report=json.loads(z.read('build-report.json'));pro=report['interactive']['chronoPro']
        assert pro['runningSmoothForcedOff'] and pro['transitionSmoothForcedOn'] and pro['aodCancelsTransitions']
        assert pro['transitionDurationMs']==720 and pro['transitionTargetFps']==25
        assert report['applicationVersion']=='1.8.1' and report['interactive']['appLayoutCount']==2
        assert all(len(s['pointerIds'])==6 for s in report['interactive']['luaArchitecture']['scenes'])
        for screen in inspect_binary(data)['screens']:
            tables=read_tables(data,screen['index'])
            if screen['aod']:assert not tables[5]
            else:
                for _,_,payload in tables[5]:
                    name,content=unpack_app(payload);assert z.read('app/'+name)==content
        assert ET.fromstring(z.read('resources/manifest.xml')).get('interactive')=='true'
    assert validate_package(ROOT/'quadrante_funzionante.zip',archive)['status']=='passed'
    tampered=tmp_path/'tampered.zip'
    with zipfile.ZipFile(archive) as src,zipfile.ZipFile(tampered,'w') as dst:
        for item in src.infolist():
            content=src.read(item)
            if item.filename=='build-report.json':
                r=json.loads(content);r['interactive']['chronoPro']['runningSmoothForcedOff']=False;content=json.dumps(r).encode()
            dst.writestr(item,content)
    with zipfile.ZipFile(tampered) as z:
        with pytest.raises(ValueError,match='Rapporto'):validate_semantics(z)
    bad_preview=tmp_path/'bad-preview.zip'
    with zipfile.ZipFile(archive) as src:
        config=json.loads(src.read('editor.config.json'))
        config['formats'][config['themes'][0]['preview']]='wrong-format'
        edited=json.dumps(config,ensure_ascii=False,indent=2).encode('utf8')
        schema=json.loads(src.read('s5studio-schema.json'))
        schema['metadataHashes']['editor.config.json']=hashlib.sha256(edited).hexdigest()
        with zipfile.ZipFile(bad_preview,'w') as dst:
            for item in src.infolist():
                content=src.read(item)
                if item.filename=='editor.config.json':content=edited
                elif item.filename=='s5studio-schema.json':content=json.dumps(schema,ensure_ascii=False,indent=2).encode('utf8')
                dst.writestr(item,content)
    with zipfile.ZipFile(bad_preview) as z:
        with pytest.raises(ValueError,match='Formato anteprima telefono'):validate_semantics(z)


def test_preview_prepare_and_reset_complete_after_720ms():
    from s5studio.chrono_pro import ProPreview
    p=pro_project();preview=ProPreview()
    assert preview.duration==720
    second=next(v for v in preview.bindings(p) if v.source=='studioIntegratedSecond')
    preview.tap(p,0,47)
    halfway=preview.values(p,320,47)
    assert preview.state=='arming' and 47<halfway[second.id]<60
    preview.values(p,719,47);assert preview.state=='arming'
    preview.values(p,720,47);assert preview.state=='ready'
    preview.tap(p,720,47);preview.tap(p,66176,52)
    assert preview.state=='stopped'
    preview.tap(p,66276,52);preview.values(p,66756,52)
    assert preview.state=='resetting'
    preview.values(p,66996,52)
    assert preview.state=='rest' and preview.values(p,66996,52)[second.id]==52


def test_hidden_pro_analog_keeps_mode_and_small_chrono_runtime(tmp_path):
    p,lua,core=pro_runtime(tmp_path,hide_main=True)
    analog=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    assert analog.chrono_pro and not analog.visible and pro_enabled(p)
    assert not p.validate() and core.main is None
    assert len(core.views)==3 and core.civilReady
    script=(tmp_path/'app/lua/studio_v0_scene.lua').read_text(encoding='utf8')
    assert 'require("studio_core_pro")' in script and 'studioChronoDecisecond' in script
    assert analog.id+'_second' not in script and 'studioIntegratedSecond' not in script
    start(lua,core)
    lua.globals().TICK=core.started+3661456;core.update(core,lua.globals().TICK)
    assert view(core,'studioChronoHour').last==1
    assert view(core,'studioChronoMinute').last==1
    assert view(core,'studioChronoDecisecond').last==4
    core.tap(core);assert core.state=='stopped'
    lua.globals().TICK+=1000;core.update(core,lua.globals().TICK)
    assert view(core,'studioChronoDecisecond').last==4
    core.tap(core);finish(lua,core)
    assert core.state=='rest' and all(v.last==0 for _,v in core.views.items())
    p.save(tmp_path/'hidden-pro.s5faceproj')
    loaded=Project.load(tmp_path/'hidden-pro.s5faceproj')
    assert loaded.metadata()==p.metadata() and pro_enabled(loaded)
    analog.visible=True
    assert pro_enabled(p) and not p.validate()
    assert any(v.source=='studioIntegratedSecond' for v in scene_bindings(p))


def test_hidden_pro_is_per_style_and_does_not_allow_a_missing_flag():
    p=pro_project();analog=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    analog.visible=False
    other=p.add_variant();design=p.editable_variant(other)
    second=next(e for e in design.elements if e.kind=='analog' and not e.aod)
    second.chrono_pro=False;p.commit_variant(other,design)
    assert pro_enabled(p.variant_project(0)) and not pro_enabled(p.variant_project(other))
    assert any(p.variants[other]['name'] in error and 'Decimi crono' in error for error in p.validate())
    second.chrono_pro=True;p.commit_variant(other,design)
    assert not p.validate()
    analog.chrono_pro=False
    assert any('Decimi crono' in error for error in p.validate())


def test_hidden_pro_preview_keeps_running_and_excludes_hidden_graphics():
    from s5studio.chrono_pro import ProPreview
    p=pro_project();preview=ProPreview()
    preview.tap(p,0,47);preview.values(p,720,47);preview.tap(p,800,47)
    before=preview.values(p,2256,48)
    analog=next(e for e in p.elements if e.kind=='analog' and not e.aod)
    analog.visible=False
    assert pro_enabled(p)
    hidden=preview.values(p,2256,48)
    assert preview.state=='running' and analog.id+'_second' not in hidden
    assert all(hidden[k]==v for k,v in before.items() if k in hidden)
    analog.visible=True
    assert preview.values(p,2256,48)==before and preview.state=='running'
