import json,struct,zipfile,time
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import Image
from s5studio.model import Project,Element,empty_project
from s5studio.gif_animation import import_gif,schedule,frame_index,native_frames,uses_lua
from s5studio.render import render
from s5studio.native import generate_fprj,build,inspect_binary
from s5studio.watchface_library import read_tables

ROOT=Path(__file__).resolve().parents[1]


def sample_gif(path):
    frames=[]
    for x,color in [(1,1),(3,2),(5,3)]:
        im=Image.new('P',(8,8),0)
        im.putpalette([0,0,0,255,0,0,0,255,0,255,255,0]+[0]*756)
        im.putpixel((x,3),color);frames.append(im)
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=[100,200,100],
                   loop=0,transparency=0,disposal=2,optimize=False)
    return path


def project_with_gif(tmp_path):
    p=Project(background='#0000ff')
    e=import_gif(p,sample_gif(tmp_path/'motion.gif'))
    e.x=e.y=100;e.width=e.height=8
    return p,e


def test_import_all_composited_frames_timing_and_transparency(tmp_path):
    p,e=project_with_gif(tmp_path)
    assert len(e.gif_frames)==3 and [f['duration'] for f in e.gif_frames]==[100,200,100]
    assert not p.validate()
    first=render(p,{'__gifMs':0},circular=False)
    second=render(p,{'__gifMs':100},circular=False)
    # Transparent pixels reveal the blue static background; prior GIF frames
    # must not remain after disposal=2.
    assert first.getpixel((101,103))[:3]==(255,0,0)
    assert second.getpixel((101,103))[:3]==(0,0,255)
    assert second.getpixel((103,103))[:3]==(0,255,0)
    assert schedule(e)==(100,[0,1,1,2])


def test_gif_layer_order_over_static_artwork_and_aod_first_frame(tmp_path):
    p,e=project_with_gif(tmp_path)
    background=tmp_path/'blue.png';Image.new('RGB',(480,480),'blue').save(background)
    static=p.add_image(background,background=True)
    assert [x.kind for x in p.ordered_layers()]==['image','gif']
    first=render(p,{'__gifMs':0},circular=False);second=render(p,{'__gifMs':300},circular=False)
    assert first.getpixel((101,103))[:3]==(255,0,0)
    assert second.getpixel((101,103))[:3]==(0,0,255)
    p.layer_order=[e.id,static.id]
    assert render(p,{'__gifMs':0},circular=False).getpixel((101,103))[:3]==(0,0,255)
    e.aod=True
    assert render(p,{'__gifMs':300},aod=True,circular=False).getpixel((101,103))[:3]==(255,0,0)


def test_exclusion_speed_and_project_roundtrip(tmp_path):
    p,e=project_with_gif(tmp_path);e.gif_frames[1]['included']=False;e.gif_speed=200
    assert schedule(e)==(50,[0,2])
    assert frame_index(e,50)==2 and frame_index(e,100)==0
    path=tmp_path/'roundtrip.s5faceproj';p.save(path)
    loaded=Project.load(path)
    assert loaded.metadata()==p.metadata() and loaded.assets==p.assets
    p.ensure_independent_variants();p.add_variant(0)
    owned=p.editable_variant(1);owned.elements[-1].gif_speed=50;p.commit_variant(1,owned)
    assert p.variant_project(0).elements[-1].gif_speed==200


@pytest.mark.parametrize('bad',['.png','.webp','.jpg'])
def test_only_gif_is_accepted(tmp_path,bad):
    path=tmp_path/('fake'+bad);path.write_bytes(sample_gif(tmp_path/'valid.gif').read_bytes())
    with pytest.raises(ValueError,match='file .gif'):import_gif(Project(),path)


def test_fake_gif_and_empty_selection_are_rejected(tmp_path):
    wrong=tmp_path/'wrong.gif';Image.new('RGB',(8,8)).save(wrong,format='PNG')
    with pytest.raises(ValueError,match='GIF valida'):import_gif(Project(),wrong)
    p,e=project_with_gif(tmp_path)
    for frame in e.gif_frames:frame['included']=False
    assert any('almeno un fotogramma' in problem for problem in p.validate())


def test_native_frames_crop_consistently_and_bound_frame_rate(tmp_path):
    p,e=project_with_gif(tmp_path);e.x=-200;e.y=-200;e.width=e.height=1000;e.gif_speed=400
    interval,sequence,bitmaps,position=native_frames(p,e)
    assert interval>=40 and set(bitmap.size for bitmap in bitmaps.values())=={(480,480)} and position==(0,0)
    assert not p.validate()


def test_native_sprite_source_and_static_aod(tmp_path):
    p,e=project_with_gif(tmp_path);e.aod=False;p.aod_enabled=True
    for frame in e.gif_frames:frame['duration']=100
    p.elements.append(Element(kind='gif',name='GIF AOD',aod=True,asset=e.asset,gif_frames=deepcopy(e.gif_frames),x=100,y=100,width=80,height=80))
    source=generate_fprj(p,tmp_path/'source')
    widget=ET.parse(source.project_path).find('.//Widget[@Shape="31"]')
    assert widget.get('Name').startswith('anim_[0@100]_RGBA_')
    assert len(widget.get('BitmapList').split('|'))==3
    assert not ET.parse(tmp_path/'source/AOD/quadrante.fprj').findall('.//Widget[@Shape="31"]')


def test_blank_document_and_new_hands_without_ticks_keep_legacy_defaults():
    p=empty_project();assert p.elements==[] and p.complications==[] and not p.aod_enabled
    assert not Element(kind='analog').show_ticks
    assert Element.from_dict({'kind':'analog','show_ticks':True}).show_ticks
    assert Element.from_dict({'kind':'analog'}).show_ticks


def test_long_native_sequence_uses_lua_without_discarding_frames(tmp_path):
    p,e=project_with_gif(tmp_path)
    for f,d in zip(e.gif_frames,[60000,40,50]):f['duration']=d
    assert uses_lua(e) and len(schedule(e)[1])>255
    source=generate_fprj(p,tmp_path/'source')
    assert ET.parse(source.project_path).find('.//Widget[@Shape="34"]') is not None
    assert (tmp_path/'source/app/lua/studio_gif.lua').exists()


def test_variable_delays_do_not_reencode_repeated_native_bitmaps(tmp_path):
    p,e=project_with_gif(tmp_path)
    assert schedule(e)==(100,[0,1,1,2]) and uses_lua(e) and not uses_lua(e,legacy=True)
    source=generate_fprj(p,tmp_path/'source')
    assert ET.parse(source.project_path).find('.//Widget[@Shape="34"]') is not None
    assert len(list((tmp_path/'source/app/lua/gfx').glob('*_gif_*.png')))==3


def test_ten_frame_export_limit_keeps_drafts_editable_and_blocks_before_compiler(tmp_path):
    from s5studio.gif_animation import export_errors
    from unittest.mock import patch
    p,e=project_with_gif(tmp_path);e.gif_frames=[deepcopy(e.gif_frames[0]) for _ in range(11)]
    assert not p.validate() and export_errors(p)
    path=tmp_path/'large-draft.s5faceproj';p.save(path)
    assert len(Project.load(path).elements[0].gif_frames)==11
    with patch('s5studio.native.compiler_probe',side_effect=AssertionError('compiler must not run')):
        with pytest.raises(ValueError,match='11 fotogrammi inclusi; massimo 10'):
            build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path/'export')
    assert not (tmp_path/'export').exists()
    e.gif_frames[-1]['included']=False
    assert not export_errors(p)
    e.gif_frames[-1]['included']=True;e.visible=False
    assert not export_errors(p)
    e.visible=True;e.aod=True
    assert not export_errors(p)


def test_frame_limit_checks_inactive_styles_too(tmp_path):
    from s5studio.gif_animation import export_errors
    p,e=project_with_gif(tmp_path);p.ensure_independent_variants();p.add_variant(0)
    p.variants[1]['name']='Other style';view=p.editable_variant(1)
    view.elements[0].gif_frames=[deepcopy(e.gif_frames[0]) for _ in range(11)]
    p.commit_variant(1,view)
    assert not p.validate()
    assert len(export_errors(p))==1 and 'Other style' in export_errors(p)[0]


def test_gif_shared_scene_lifecycle_and_write_on_change():
    from test_motion_interaction import lua_runtime
    lua,_=lua_runtime()
    runtime=lua.execute((ROOT/'s5studio/lua/studio_gif.lua').read_text(encoding='utf8'))
    lua.globals().GIF=runtime
    lua.execute('VIEW=GIF.add(LV.Object(nil,{}),{x=0,y=0,interval=100,frames={[1]="red.png",[2]="green.png"},sequence={1,2,2}})')
    v=lua.globals().VIEW
    assert v.image.src.endswith('red.png') and v.animation.run
    v.animation.exec_cb(v.root,100);assert v.image.src.endswith('green.png')
    lua.execute('WRITES=0;local old=VIEW.image.set;VIEW.image.set=function(self,t) WRITES=WRITES+1;old(self,t) end')
    v.animation.exec_cb(v.root,200);assert lua.globals().WRITES==0
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    assert not v.animation.run
    v.animation.exec_cb(v.root,0);assert lua.globals().WRITES==0
    lua.globals().ScreenStateChangedCB('AOD','ON',0);assert v.animation.run
    lua.globals().pageOnPause();assert not v.animation.run
    lua.globals().pageOnResume();assert v.animation.run
    v.root.events[5]();assert v.deleted and not v.animation.run
    v.animation.exec_cb(v.root,100)


@pytest.mark.integration
def test_real_compiler_native_long_gifs_variants_and_static_aod(tmp_path):
    from s5studio.semantic_package import validate_package
    p,e=project_with_gif(tmp_path);p.name='GIF compiler validation'
    for frame in e.gif_frames:frame['duration']=100
    image=tmp_path/'background.png';Image.new('RGB',(480,480),'#18284a').save(image)
    p.add_image(image,background=True)
    slow=deepcopy(e);from s5studio.model import identifier
    slow.id=identifier();slow.name='Long frame timings';slow.y=240
    for f,d in zip(slow.gif_frames,[60000,40,50]):f['duration']=d
    p.elements.append(slow)
    # Formerly interleaved Pro indicators are excluded by the 3.1 GIF policy;
    # both uniformly timed GIFs now use the native backend.
    small=Element(kind='pointer',name='Ore Crono',source='studioChronoHour',value_range=12,x=60,y=80,width=80,height=80)
    other=deepcopy(e);from s5studio.model import identifier
    other.id=identifier();other.name='GIF interleaved';other.x=220
    main=Element(kind='analog',name='Crono Pro',x=60,y=60,width=360,height=360,second_hand=True,chrono_pro=True)
    p.elements.extend([small,other,main,Element(kind='clock',name='AOD',aod=True,x=100,y=180,width=280,height=90,size=60)])
    aod_gif=deepcopy(e);aod_gif.id=identifier();aod_gif.aod=True;p.elements.append(aod_gif);p.aod_enabled=True
    p.ensure_independent_variants();p.add_variant(0);p.variants[1]['name']='Second style'
    before=p.metadata();start=time.perf_counter()
    result=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path/'export')
    assert p.metadata()==before
    report=json.loads((result/'build-report.json').read_text(encoding='utf8'))
    zpath=next(result.glob('*.zip'))
    validate_package(ROOT/'quadrante_funzionante.zip',zpath)
    with zipfile.ZipFile(zpath) as z:
        info=inspect_binary(z.read('resource.bin'));xml=ET.fromstring(z.read('resources/manifest.xml'))
        assert info['screenCount']==4
        for screen in info['screens']:
            tables=read_tables(z.read('resource.bin'),screen['index'])
            assert len(tables[4])==(0 if screen['aod'] else 2)
        assert len(xml.findall('.//SpriteGroup'))==4
        assert 'app/lua/studio_gif.lua' in z.namelist()
        assert xml.get('interactive')=='true'
        assert z.testzip() is None
        inside=json.loads(z.read('build-report.json'))
        assert len(inside['gifAnimations']['animations'])==6
        assert {a['engine'] for a in inside['gifAnimations']['animations']}=={'native-SpriteGroup','lvgl-frame-sequence'}
    evidence={'applicationVersion':'3.1','status':'passed','elapsedSeconds':round(time.perf_counter()-start,2),
              'styles':2,'aodScreens':2,'nativeGifAnimations':4,'sharedSceneGifAnimations':0,'longSequenceGifAnimations':2,
              'staticArtworkAndGifLayering':True,'gifRuntimeIncluded':True,'zipSemanticsVerified':True,
              'inputProjectUnchanged':True,'hardwareTestPerformed':False,'temporaryCompilerExport':True}
    (ROOT/'docs/export-validation-gif-paths-3.1.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
