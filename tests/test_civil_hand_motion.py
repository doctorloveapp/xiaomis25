from dataclasses import replace
from pathlib import Path
import hashlib,os,shutil,struct,subprocess,zipfile
import xml.etree.ElementTree as ET
from PIL import Image
import pytest
from s5studio.model import Project,Element
from s5studio.render import render,hand_image,png_bytes
from s5studio.lua_runtime import pro_views,unpack_app,interaction_report
from s5studio.civil_hands import write_civil_hand,civil_entry
from s5studio.native import generate_fprj,inspect_binary
from s5studio.native_graph import compose
from s5studio.watchface_library import read_tables
from test_motion_interaction import lua_runtime
from test_chrono_pro import pro_runtime,view,start

ROOT=Path(__file__).resolve().parents[1]


def test_separate_flags_keep_legacy_defaults_and_survive_save_and_styles(tmp_path):
    legacy=Element.from_dict({'kind':'analog','smooth_seconds':True})
    assert not legacy.smooth_hours and not legacy.smooth_minutes and legacy.smooth_seconds
    p=Project(elements=[legacy]);p.add_variant()
    style=p.editable_variant(1);style.elements[0].smooth_minutes=True;p.commit_variant(1,style)
    p.save(tmp_path/'motion.s5faceproj');copy=Project.load(tmp_path/'motion.s5faceproj')
    assert not copy.variant_project(0).elements[0].smooth_minutes
    assert copy.variant_project(1).elements[0].smooth_minutes
    assert all(v.smooth_seconds==enabled for v,enabled in zip(pro_views(replace(legacy,smooth_hours=True)),[True,False,True]))
    invalid=Project(elements=[replace(legacy,smooth_hours='yes')])
    assert any('Movimento Fluido' in error for error in invalid.validate())


@pytest.mark.parametrize('hours,minutes,seconds',[(False,False,True),(True,False,False),(False,True,False),(True,True,True)])
def test_preview_uses_independent_civil_positions_and_disables_smooth_in_aod(monkeypatch,hours,minutes,seconds):
    e=Element(kind='analog',width=360,height=360,second_hand=True,show_ticks=False,show_shadows=False,
              smooth_hours=hours,smooth_minutes=minutes,smooth_seconds=seconds)
    p=Project(elements=[e]);angles=[];original=Image.Image.rotate
    def rotate(image,angle,*args,**kwargs):
        angles.append(angle);return original(image,angle,*args,**kwargs)
    monkeypatch.setattr(Image.Image,'rotate',rotate)
    render(p,{'hour':10,'minute':8,'second':30,'__secondFraction':.5},circular=False)
    assert angles==pytest.approx([-(304.25 if hours else 304),-(51 if minutes else 48),-(183 if seconds else 180)])
    angles.clear();p.elements=[replace(e,aod=True)]
    render(p,{'hour':10,'minute':8,'second':30,'__secondFraction':.5},aod=True,circular=False)
    assert angles==pytest.approx([-304,-48])


@pytest.mark.parametrize('role',['hour','minute'])
def test_civil_lua_seconds_positions_shadow_cache_and_lifecycle_without_timers(tmp_path,role):
    lua,_=lua_runtime()
    lua.execute('''
        DATA={};package.preload.dataman=function() return {subscribe=function(name,obj,cb)
            DATA[name]=function(value) cb(obj,value) end end} end
        LV.Timer=function() error('Civil hands must not create a timer') end
        local object=getmetatable(make(nil,{})).__index;local oldset=object.set
        function object:set(t) self.writes=(self.writes or 0)+1;oldset(self,t) end
    ''')
    module=lua.execute((ROOT/'s5studio/lua/studio_civil_hand.lua').read_text(encoding='utf8'))
    lua.globals().CIVIL=module;lua.execute('package.loaded.studio_civil_hand=CIVIL')
    e=Element(kind='analog',width=360,height=360,smooth_hours=True,smooth_minutes=True,
              **{role+'_asset':'assets/main.png',role+'_shadow_asset':'assets/shadow.png'})
    assets={'assets/main.png':png_bytes(Image.new('RGBA',(20,100),'white')),
            'assets/shadow.png':png_bytes(Image.new('RGBA',(20,100),(0,0,0,120)))}
    p=Project(elements=[e],assets=assets);name=write_civil_hand(p,e,role,tmp_path,0)
    result=lua.execute((tmp_path/'app'/name).read_text(encoding='utf8')+'\nreturn {root=root,hands=hands}\n')
    hand=result.hands[1]
    assert len(result.hands)==2
    lua.execute('DATA.timeHour(14*256);DATA.timeMinute(8*256);DATA.timeSecond(47*256)')
    assert hand.value==(2*3600 if role=='hour' else 0)+8*60+47
    assert result.hands[2].value==hand.value
    writes=hand.writes;lua.execute('DATA.timeSecond(47*256)');assert hand.writes==writes
    lua.execute('DATA.timeSecond(48*256)');assert hand.value==(2*3600 if role=='hour' else 0)+8*60+48
    assert hand.range.valueRange==(43200 if role=='hour' else 3600)
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    before=hand.value;lua.execute('DATA.timeSecond(49*256)');assert hand.value==before
    lua.globals().ScreenStateChangedCB('AOD','ON',0);assert hand.value==before+1
    lua.globals().pageOnPause();lua.execute('DATA.timeSecond(50*256)');assert hand.value==before+1
    lua.globals().pageOnResume();assert hand.value==before+2
    lua.execute('DATA.timeHour(0);DATA.timeMinute(0);DATA.timeSecond(0)');assert hand.value==0
    result.root.events[5]();writes=hand.writes;lua.execute('DATA.timeSecond(256)');assert hand.writes==writes


def test_pro_civil_flags_do_not_change_chrono_running_or_timer_periods(tmp_path):
    p,lua,core=pro_runtime(tmp_path)
    hour=view(core,'studioTimeHour');minute=view(core,'studioTimeMinute')
    assert not hour.smooth and not minute.smooth and view(core,'studioIntegratedSecond').smooth
    hour.smooth=True;minute.smooth=True;core.update(core,lua.globals().TICK)
    assert hour.last==pytest.approx(round((2+8/60+47/3600)*1000)/1000)
    assert minute.last==pytest.approx(round((8+47/60)*1000)/1000)
    start(lua,core);assert core.restTimer.paused and core.runTimer.period==100
    lua.globals().TICK=core.started+65456;core.update(core,lua.globals().TICK)
    assert view(core,'studioIntegratedSecond').last==5
    assert view(core,'studioChronoMinute').last==1
    assert view(core,'studioChronoDecisecond').last==4


def test_compiled_flags_mixed_styles_pro_manifest_original_geometry_and_aod(tmp_path):
    # One temporary binary, no distributable ZIP or executable launch.
    raw=Image.new('RGBA',(12,110),'white');asset='assets/hand.png'
    e=Element(kind='analog',x=60,y=60,width=360,height=360,second_hand=True,smooth_hours=True,
              hour_asset=asset,hour_anchor_x=6,hour_anchor_y=90,hour_length_adjusted=False)
    aod=replace(e,id='a0d0a0d0a0d0',aod=True,smooth_minutes=True)
    small=Element(kind='pointer',source='studioChronoMinute',value_range=60,width=80,height=80)
    p=Project(elements=[e,small,aod],assets={asset:png_bytes(raw)},aod_enabled=True);p.add_variant();p.add_variant()
    style=p.editable_variant(1);style.elements[0].smooth_hours=False;style.elements[0].smooth_minutes=True
    style.elements[0].smooth_seconds=True;p.commit_variant(1,style)
    style=p.editable_variant(2);style.elements[0].chrono_pro=True;style.elements[0].smooth_minutes=True;p.commit_variant(2,style)
    source=generate_fprj(p,tmp_path/'source')
    # The hour bitmap and its native pivot must retain their original geometry.
    emitted=tmp_path/'source/app/lua/gfx'/('v0_'+e.id+'_hour.png')
    with Image.open(emitted) as im:assert im.size==hand_image(e,'hour',p)[0].size
    runtime=tmp_path/'runtime';runtime.mkdir();output=tmp_path/'out';output.mkdir()
    for name in ('Compiler.exe','DeviceInfo.db'):shutil.copy2(ROOT/'tools/easyface-4.23'/name,runtime/name)
    env=dict(os.environ);env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
    result=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source.project_path),str(output),'motion.face','167210065'],
        cwd=runtime,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0 and b'No Errors' in result.stdout+result.stderr
    compiled=(output/'motion.face').read_bytes();preview=read_tables(compiled,0)[2][0][2]
    with zipfile.ZipFile(ROOT/'quadrante_funzionante.zip') as z:reference=z.read('resource.bin')
    data,metadata=compose(compiled,p,reference,source.project_path.parent,[preview]*3,{},{},aod_preview=preview)
    assert inspect_binary(data)['screenCount']==6
    report=interaction_report(p,data,metadata['resources/manifest.xml'])
    assert report['appLayoutCount']==5 and report['chronoPro']['runningSmoothForcedOff']
    assert report['civilHandMotion']['entries']==[[civil_entry(e,'hour',0)],[civil_entry(e,'minute',1)],[]]
    assert 'app/lua/studio_civil_hand.lua' in report['files']
    assert 'app/lua/studio_civil_clock.lua' in report['files'] and report['civilClock']['coherentSamples']
    for screen in (1,3,5):
        tables=read_tables(data,screen);apps={uid for uid,_,_ in tables[5]}
        assert not any(struct.unpack_from('<I',b)[0] in apps for _,_,b in tables[0])
        pointers=[b for _,_,b in tables[7] if b[3]>>4==3]
        assert len(pointers)==2 and {b[:2] for b in pointers}=={bytes.fromhex('0811'),bytes.fromhex('1011')}
        assert all(struct.unpack_from('<H',b,6)[0]==1000 for b in pointers)
    for screen,code,period in [(0,'1011',1000),(0,'1811',1000),(2,'0811',1000),(2,'1811',40)]:
        matched=[b for _,_,b in read_tables(data,screen)[7] if b[:2]==bytes.fromhex(code)]
        assert matched and all(struct.unpack_from('<H',b,6)[0]==period for b in matched)
    assert not any(b[:2]==bytes.fromhex('0811') for _,_,b in read_tables(data,0)[7])
    assert not any(b[:2]==bytes.fromhex('1011') for _,_,b in read_tables(data,2)[7])
