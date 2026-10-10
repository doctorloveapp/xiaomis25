"""Civil small seconds must tick in preview and keep their native time source."""
from dataclasses import replace
from pathlib import Path
import hashlib,os,shutil,struct,subprocess,zipfile
import xml.etree.ElementTree as ET
from PIL import Image,ImageDraw
import pytest
from s5studio.model import Project,Element,SOURCES
from s5studio.render import render,png_bytes,hand_image,hand_shadow_offset
from s5studio.native import generate_fprj,inspect_binary
from s5studio.native_graph import compose
from s5studio.watchface_library import read_tables

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('source',['second','timeSecond'])
def test_seconds_tick_without_sweep_and_wrap_at_sixty(source):
    e=Element(kind='pointer',source=source,x=180,y=160,width=120,height=120,
              second_length=40,second_width=5,value_start=0,value_range=60,angle_start=0,angle_range=360)
    p=Project(elements=[e]);frames=[]
    for elapsed in (0.1,0.9,1.1,15.2,30.4,59.8,60.2,61.2,121.2):
        preview=render(p,{'second':0,'__secondFraction':elapsed,'__chronoMs':55000},circular=False)
        expected=render(p,{'second':int(elapsed)%60,'__chronoMs':0},circular=False)
        assert preview.tobytes()==expected.tobytes()
        frames.append(preview.tobytes())
    assert frames[0]==frames[1]==frames[6] and frames[2]==frames[7]==frames[8]
    assert len(set(frames))==5 and not e.smooth_seconds
    # A zero elapsed phase preserves the exact civil second selected by the user.
    assert render(p,{'second':58,'__secondFraction':3.1}).tobytes()==render(p,{'second':1}).tobytes()


@pytest.mark.parametrize('chrono_ms',[0,1000,60000,3600000])
def test_civil_seconds_never_use_chrono_elapsed_or_other_sensor_animation(chrono_ms):
    second=Element(kind='pointer',source='timeSecond',width=120,height=120)
    p=Project(elements=[second])
    assert render(p,{'second':15,'__chronoMs':chrono_ms,'__proValues':{'other':42}}).tobytes()==render(p,{'second':15}).tobytes()
    battery=replace(second,source='batteryPercent');p.elements=[battery]
    assert render(p,{'batteryPercent':50,'__secondFraction':15}).tobytes()==render(p,{'batteryPercent':50}).tobytes()


def test_custom_pivot_angle_and_start_are_not_silently_changed():
    e=Element(kind='pointer',source='timeSecond',value_start=1,angle_start=-90,second_anchor_x=22,second_anchor_y=132,pointer_end_pivot=False)
    p=Project(elements=[e]);before=p.metadata()
    render(p,{'second':0,'__secondFraction':61})
    assert p.metadata()==before


def test_real_compiler_keeps_native_civil_seconds_with_pro_variants_and_no_aod_seconds(tmp_path):
    raw=Image.new('RGBA',(44,200));ImageDraw.Draw(raw).rectangle((19,0,24,132),fill='white')
    shadow=Image.new('RGBA',raw.size);ImageDraw.Draw(shadow).rectangle((19,0,24,132),fill=(0,0,0,150))
    assets={}
    def asset(im):
        b=png_bytes(im);key='assets/'+hashlib.sha256(b).hexdigest()[:24]+'.png';assets[key]=b;return key
    e=Element(kind='pointer',source='timeSecond',x=86,y=180,width=120,height=120,second_asset=asset(raw),
        second_anchor_x=22,second_anchor_y=132,pointer_end_pivot=False,second_shadow_asset=asset(shadow),
        second_shadow_anchor_x=22,second_shadow_anchor_y=132,second_shadow_offset_x=2,second_shadow_offset_y=3,
        value_start=0,value_range=60,angle_start=0,angle_range=360)
    main=Element(kind='analog',x=0,y=0,width=480,height=480,chrono_pro=True,second_hand=True)
    crono=Element(kind='pointer',source='studioChronoMinute',value_range=60,x=300,y=180,width=80,height=80)
    aod=replace(e,id='aodsmall',aod=True)
    p=Project(elements=[main,crono,e,aod],assets=assets,aod_enabled=True);p.add_variant()
    style=p.editable_variant(1);style.elements[2].angle_start=-90;p.commit_variant(1,style)
    source=generate_fprj(p,tmp_path/'source')
    runtime=tmp_path/'runtime';runtime.mkdir();output=tmp_path/'out';output.mkdir()
    for name in ('Compiler.exe','DeviceInfo.db'):shutil.copy2(ROOT/'tools/easyface-4.23'/name,runtime/name)
    env=dict(os.environ);env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
    result=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source.project_path),str(output),'seconds.face','167210065'],
        cwd=runtime,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0 and b'No Errors' in result.stdout+result.stderr
    compiled=(output/'seconds.face').read_bytes()
    preview=read_tables(compiled,0)[2][0][2]
    with zipfile.ZipFile(ROOT/'quadrante_funzionante.zip') as z:reference=z.read('resource.bin')
    data,metadata=compose(compiled,p,reference,source.project_path.parent,[preview,preview],{},{},aod_preview=preview)
    assert inspect_binary(data)['screenCount']==4
    for vi,screen in [(0,0),(1,2)]:
        resolved=p.variant_project(vi);hand=next(v for v in resolved.elements if v.id==e.id)
        t=read_tables(data,screen)
        pointers=[(uid,b) for uid,_,b in t[7] if b[:2]==bytes.fromhex(SOURCES['timeSecond'][1])]
        assert len(pointers)==2  # Original plus its shadow, both native timeSecond.
        for (uid,b),is_shadow in zip(pointers,[True,False]):
            assert struct.unpack_from('<H',b,6)[0]==1000  # 1 Hz; independent of Pro.
            assert struct.unpack_from('<II',b,12)==(0,60<<8)
            assert struct.unpack_from('<hh',b,24)==(hand.angle_start*10,3600)
            pivot=struct.unpack_from('<HH',b,20);assert pivot==hand_image(hand,'second',resolved,shadow=is_shadow)[1]
            layout=next(b for _,_,b in t[0] if struct.unpack_from('<I',b)[0]==uid)
            dx,dy=hand_shadow_offset(hand,'second',resolved) if is_shadow else (0,0)
            assert tuple(a+c for a,c in zip(struct.unpack_from('<hh',layout,4),pivot))==(hand.x+hand.width//2+dx,hand.y+hand.height//2+dy)
            node=ET.fromstring(metadata['resources/manifest.xml']).find("Resources/DataItemPointer[@name='Studio_%08x']"%uid)
            assert node.get('source')=='timeSecond' and node.get('pointerFps')=='1' and node.get('valueStart')=='0'
    for screen in (1,3):
        assert not any(b[:2]==bytes.fromhex('1811') for _,_,b in read_tables(data,screen)[7])
    assert not (tmp_path/'source/AOD/app').exists()
