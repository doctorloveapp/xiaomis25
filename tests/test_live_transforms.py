"""Dynamic values, shared raster geometry, compiler closure; no demo ZIP/EXE."""
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import os,shutil,subprocess,zipfile,xml.etree.ElementTree as ET
import pytest
from PIL import Image,ImageChops
from s5studio.model import Project,Element
from s5studio.render import render,element_image
from s5studio.transforms import raster
from s5studio.live_data import write_live,complete_aod_apps
from s5studio.native import generate_fprj,inspect_binary
from s5studio.native_graph import collect_nodes
from s5studio.lua_runtime import interaction_report,unpack_app
from s5studio.watchface_library import read_tables

ROOT=Path(__file__).resolve().parents[1]


def live_runtime(p,e,tmp_path):
    from lupa import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
        DATA={};LV={FLAG={HIDDEN=1,CLICKABLE=2,SCROLLABLE=3},EVENT={DELETE=4}}
        local methods={}
        function methods:set(t) self.writes=(self.writes or 0)+1;for k,v in pairs(t) do self[k]=v end end
        function methods:clear_flag(f) self.flags[f]=false end
        function methods:add_flag(f) self.flags[f]=true end
        function methods:onevent(event,cb) self.events[event]=cb end
        function make(parent,t) t=t or {};t.flags={};t.events={};return setmetatable(t,{__index=methods}) end
        LV.Object=make
        function methods:Image(t) return make(self,t) end
        package.preload.lvgl=function()return LV end
        package.preload.dataman=function()return {subscribe=function(name,obj,cb)
            DATA[name]=function(value)cb(obj,value)end
        end}end
        SCRIPT_PATH=''
    ''')
    module=lua.execute((ROOT/'s5studio/lua/studio_live_data.lua').read_text(encoding='utf8'))
    lua.globals().LIVE=module;lua.execute('package.loaded.studio_live_data=LIVE')
    name=write_live(p,e,tmp_path,0)
    lua.execute((tmp_path/'app'/name).read_text(encoding='utf8'))
    return lua,module,module.views[1]


@pytest.mark.parametrize('align,decimals,zero,values',[
    ('right',0,False,[1,15,999,-12,None]),
    ('center',1,False,[1.5,12.3,-0.5,1000,None]),
    ('left',0,True,[0,5,15,-12,None]),
])
def test_real_sensor_changes_match_preview_glyph_positions(tmp_path,align,decimals,zero,values):
    e=Element(kind='number',source='heartRate',x=135,y=90,width=210,height=44,size=28,
              rotation=32,arc=-100,digits=4,align=align,decimals=decimals,leading_zero=zero)
    p=Project(elements=[e]);assert not p.validate()
    lua,module,view=live_runtime(p,e,tmp_path)
    for value in values:
        lua.globals().DATA.healthHeartRate(value*256 if value is not None else 2147483647)
        actual=Image.new('RGBA',(480,480))
        for _,img in view.images.items():
            if not img.flags[1]:
                with Image.open(tmp_path/'app/lua'/img.src) as bitmap:actual.alpha_composite(bitmap.convert('RGBA'),(img.x,img.y))
        expected=Image.new('RGBA',(480,480));bitmap,x,y=raster(p,e,element_image(p,e,{'heartRate':value}));expected.alpha_composite(bitmap,(x,y))
        difference=ImageChops.difference(actual,expected)
        assert max(high for low,high in difference.getextrema())<=1
        writes=[img.writes or 0 for _,img in view.images.items()]
        lua.globals().DATA.healthHeartRate(value*256 if value is not None else 2147483647)
        assert writes==[img.writes or 0 for _,img in view.images.items()]
    assert lua.globals().LV.Timer is None and lua.globals().LV.Anim is None
    lua.globals().ScreenStateChangedCB('ON','AOD',0);assert view.root.flags[1]
    lua.globals().DATA.healthHeartRate(256*72)
    lua.globals().ScreenStateChangedCB('AOD','ON',0);assert not view.root.flags[1] and view.last==('0072' if zero else '72.0' if decimals else '72')
    lua.globals().pageOnPause();lua.globals().DATA.healthHeartRate(256*80)
    assert view.last!=('0080' if zero else '80.0' if decimals else '80')
    lua.globals().pageOnResume();assert view.last==('0080' if zero else '80.0' if decimals else '80')
    view.root.events[4]();lua.globals().DATA.healthHeartRate(256*10);assert view.deleted


def test_aod_live_number_never_uses_chrono_or_animation(tmp_path):
    e=Element(kind='number',source='batteryPercent',rotation=90,aod=True)
    lua,module,view=live_runtime(Project(elements=[e]),e,tmp_path)
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    lua.globals().DATA.systemStatusBattery(256*82)
    assert not view.root.flags[1] and view.last=='82'
    lua.globals().ScreenStateChangedCB('AOD','OFF',0);assert view.root.flags[1]
    assert not (tmp_path/'app/lua/studio_core.lua').exists()


def test_calendar_transforms_remain_native_and_preview_changes(tmp_path):
    e=Element(kind='number',source='dateWeek',x=100,y=70,width=180,height=40,size=26,rotation=18,arc=90)
    p=Project(elements=[e]);p.add_variant();p.editable_variant(1).elements[0].rotation=-18
    # Round trip and independent styles keep both geometry properties.
    p.save(tmp_path/'live.s5faceproj');q=Project.load(tmp_path/'live.s5faceproj')
    assert q.variant_project(0).elements[0].rotation==18
    assert q.variant_project(1).elements[0].rotation==-18
    source=generate_fprj(Project(elements=[e]),tmp_path/'source')
    w=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')[1]
    assert w.get('Shape')=='31' and w.get('Index_Src')=='2012'
    images=w.get('BitmapList').split('|');assert len(images)==7
    bitmap,x,y=raster(p,e,element_image(p,e,{'dateWeek':1}))
    with Image.open(source.project_path.parent/'images'/images[1].split(':')[1]) as exported:
        assert exported.tobytes()==bitmap.tobytes()
    assert (int(w.get('X')),int(w.get('Y')))==(x,y)
    assert render(Project(elements=[e]),{'dateWeek':1}).tobytes()!=render(Project(elements=[e]),{'dateWeek':2}).tobytes()


@pytest.mark.parametrize('pro',[True,False])
def test_real_compile_live_data_in_pro_scene_and_aod(tmp_path,pro):
    main=Element(kind='analog',chrono_pro=True,second_hand=True,width=480,height=480,x=0,y=0,show_center_cap=False)
    live=Element(kind='number',source='heartRate',rotation=25,arc=60,width=160,height=40,size=24)
    small=Element(kind='pointer',source='studioChronoMinute',width=60,height=60,x=200,y=280)
    separate=replace(live,id='outside',source='steps',x=190,y=340,digits=5)
    aod=replace(live,id='aodlive',source='batteryPercent',aod=True)
    p=Project(elements=[main,live,small,separate,aod],aod_enabled=True)
    if pro:p.add_variant()
    else:p.elements=[replace(live,rotation=0,arc=0),aod]
    source=generate_fprj(p,tmp_path/'source')
    runtime=tmp_path/'runtime';runtime.mkdir();output=tmp_path/'out';output.mkdir()
    for name in ('Compiler.exe','DeviceInfo.db'):shutil.copy2(ROOT/'tools/easyface-4.23'/name,runtime/name)
    env=dict(os.environ);env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
    result=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source.project_path),str(output),'live.face','167210065'],
        cwd=runtime,env=env,capture_output=True,stdin=subprocess.DEVNULL,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0 and b'No Errors' in result.stdout+result.stderr
    data=complete_aod_apps((output/'live.face').read_bytes(),source.project_path);assert inspect_binary(data)['screenCount']==(3 if pro else 2)
    compiled={}
    for i,path in [(0,source.project_path),(1,tmp_path/'source/AOD/quadrante.fprj')]:
        nodes=collect_nodes(data,i,path);assert any(n['tag']=='App' for n in nodes.values())
        compiled.update(dict(unpack_app(b) for _,_,b in read_tables(data,i)[5]))
    assert 'lua/studio_live_data.lua' in compiled
    if pro:assert 'healthHeartRate' in compiled['lua/studio_v0_scene.lua'].decode('utf8')
    else:assert 'lua/studio_v0_live_aod_registry.lua' in compiled
    assert any(n.startswith('lua/gfx/live_') for n in compiled)
    report=interaction_report(p,data,b'<Watchface interactive="true"/>')
    assert report['liveDataTransforms']['injected'] and not report['liveDataTransforms']['sampleValueBaked']
    assert bool(report.get('chronoPro',{}).get('injected'))==pro and report['aodSecondsExcluded']
    # Verify the final editable graph/manifest in memory; no watchface ZIP.
    from s5studio.native_graph import compose
    with zipfile.ZipFile(ROOT/'quadrante_funzionante.zip') as z:reference=z.read('resource.bin')
    preview=read_tables(data,0)[2][0][2]
    final,metadata=compose(data,p,reference,source.project_path.parent,
                           [preview]*max(1,len(p.variants)),{},{},aod_preview=preview)
    assert inspect_binary(final)['directoryStride']==176
    final_report=interaction_report(p,final,metadata['resources/manifest.xml'])
    assert final_report['liveDataTransforms']['injected']
    assert metadata['app/lua/studio_live_data.lua']==(ROOT/'s5studio/lua/studio_live_data.lua').read_bytes()
