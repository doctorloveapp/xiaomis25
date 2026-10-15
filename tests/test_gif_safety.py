from copy import deepcopy
import json,struct,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import ImageChops
from s5studio.model import Element,Project
from s5studio.gif_animation import runtime_project,safety_state,safety_report,validate_safety
from s5studio.native import generate_fprj,build,inspect_binary
from s5studio.render import render
from s5studio.watchface_library import read_tables
from test_gif_animation import project_with_gif,ROOT


def design(tmp_path):
    p,gif=project_with_gif(tmp_path)
    p.elements.append(Element(kind='analog',name='Pro',x=60,y=60,width=360,height=360,second_hand=True,chrono_pro=True,only_chrono=True))
    for source,value_range in [('timeSecond',60),('studioDecisecond',10),('studioChronoHour',12),('studioChronoMinute',60),('studioChronoSecond',60),('studioChronoDecisecond',10),('studioChronoCentisecond',100),('studioChronoMillisecond',1000)]:
        p.elements.append(Element(kind='pointer',name=source,source=source,value_range=value_range,x=120,y=120,width=80,height=80))
    p.elements.append(Element(kind='clock',name='AOD',aod=True,x=100,y=180,width=280,height=90,size=60))
    p.aod_enabled=True
    assert not p.validate()
    return p,gif


def test_gif_safety_detached_copy_preserves_preferences_and_aod(tmp_path):
    p,gif=design(tmp_path);before=p.metadata();safe=runtime_project(p)
    assert p.metadata()==before and not safe.validate()
    main=next(e for e in safe.elements if e.kind=='analog')
    assert not main.second_hand and not main.chrono_pro and not main.only_chrono
    assert all(not e.visible for e in safe.elements if e.kind=='pointer')
    assert [e for e in safe.elements if e.aod]==[e for e in p.elements if e.aod]
    assert safety_report(p)==safety_report(safe)
    saved=tmp_path/'editable.s5faceproj';p.save(saved);loaded=Project.load(saved)
    loaded.elements[0].visible=False
    restored=runtime_project(loaded)
    assert restored is loaded and next(e for e in restored.elements if e.kind=='analog').chrono_pro
    assert all(e.visible for e in restored.elements if e.kind=='pointer')


def test_safety_is_per_style_including_legacy_overrides(tmp_path):
    p,gif=design(tmp_path);p.variants=[{'name':'GIF'},{'name':'No GIF','overrides':{gif.id:{'visible':False}}}]
    before=p.metadata();safe=runtime_project(p)
    assert safety_state(safe.variant_project(0))['active']
    assert not next(e for e in safe.variant_project(0).elements if e.kind=='analog').second_hand
    second=safe.variant_project(1)
    assert not safety_state(second)['active'] and next(e for e in second.elements if e.kind=='analog').chrono_pro
    assert p.metadata()==before


def test_hidden_and_aod_only_gifs_do_not_restrict_normal_hands(tmp_path):
    p,gif=design(tmp_path);gif.visible=False
    assert runtime_project(p) is p
    gif.visible=True;gif.aod=True
    assert runtime_project(p) is p
    gif.aod=False
    for frame in gif.gif_frames[1:]:frame['included']=False
    # A visible GIF object remains subject to the conservative rule, even
    # when reduced to a single included frame or paused in the PC preview.
    assert safety_state(p)['active']


def test_preview_and_fprj_exclude_seconds_shadows_and_chrono(tmp_path):
    p,gif=design(tmp_path);before=p.metadata()
    a=render(p,{'hour':10,'minute':8,'second':0})
    b=render(p,{'hour':10,'minute':8,'second':30})
    assert ImageChops.difference(a,b).convert('RGB').getbbox() is None
    source=generate_fprj(p,tmp_path/'source')
    tree=ET.parse(source.project_path)
    assert not any(w.get('SecondHand_Image') for w in tree.findall('.//Widget'))
    assert '1811' not in source.expected_sources
    assert not list((tmp_path/'source/app/lua').glob('studio_core*.lua'))
    assert p.metadata()==before
    gif.visible=False
    p.elements[1].chrono_pro=p.elements[1].only_chrono=False
    # Normal seconds return when no GIF is visible.
    assert ImageChops.difference(render(p,{'hour':10,'minute':8,'second':0}),render(p,{'hour':10,'minute':8,'second':30})).convert('RGB').getbbox() is not None


@pytest.mark.integration
def test_real_compiler_mixed_gif_and_chrono_styles_with_aod(tmp_path):
    from s5studio.semantic_package import validate_package
    p,gif=design(tmp_path);p.ensure_independent_variants();p.add_variant(0)
    p.variants[0]['name']='GIF safe';p.variants[1]['name']='Crono without GIF'
    other=p.editable_variant(1);other.elements[0].visible=False;p.commit_variant(1,other)
    before=p.metadata();result=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path/'export')
    assert p.metadata()==before
    report=json.loads((result/'build-report.json').read_text(encoding='utf8'))
    assert report['applicationVersion']=='3.1' and report['gifSafety']['styles'][0]['active'] and not report['gifSafety']['styles'][1]['active']
    reopened=Project.load(next(result.glob('*.s5faceproj')))
    assert next(e for e in reopened.elements if e.kind=='analog').second_hand and next(e for e in reopened.elements if e.kind=='analog').chrono_pro
    with zipfile.ZipFile(next(result.glob('*.zip'))) as z:
        data=z.read('resource.bin');info=inspect_binary(data)
        assert info['screenCount']==4
        assert not any(b[:2]==bytes.fromhex('1811') for _,_,b in read_tables(data,0)[7])
        assert not any(not screen['aod'] and screen['index']==0 for screen in report['secondsMotion']['pointers'])
        assert report['interactive']['luaArchitecture']['type']=='single-scene-per-theme'
        assert b'studio_core_pro' in z.read('app/lua/studio_v1_scene.lua')
        assert 'app/lua/studio_v0_scene.lua' not in z.namelist()
        with pytest.raises(ValueError,match='Rapporto limitazioni'):
            validate_safety(runtime_project(p),data,{})
        from s5studio.watchface_library import directory_bases
        changed=bytearray(data);base=directory_bases(data)[0]
        count,offset=struct.unpack_from('<II',data,base+8+7*8)
        assert count
        uid,flags,position,length=struct.unpack_from('<IIII',data,offset)
        changed[position:position+2]=bytes.fromhex('1811')
        with pytest.raises(ValueError,match='Lancetta secondi'):
            validate_safety(runtime_project(p),bytes(changed),report['gifSafety'])
    validate_package(ROOT/'quadrante_funzionante.zip',next(result.glob('*.zip')))
    evidence={'applicationVersion':'3.1','status':'passed','styles':2,'aodScreens':2,'gifStyleSecondsAndChronoExcluded':True,'nonGifStyleChronoPreserved':True,'editablePreferencesPreservedInExportedProject':True,'inputProjectUnchanged':True,'zipSemanticsVerified':True,'hardwareTestPerformed':False}
    (ROOT/'docs/export-validation-3.1.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf8')
