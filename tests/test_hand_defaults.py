"""1.6.1: applying a model must honor visible dimensions on its first render."""
from dataclasses import replace
from pathlib import Path
import json
import os
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from s5studio.hand_presets import preset_changes
from s5studio.lua_runtime import pro_views
from s5studio.model import Project,Element,template
from s5studio.native import generate_fprj
from s5studio.render import SCENARIOS,hand_image,hand_edit_changes,png_bytes,render,element_image
from s5studio.watchface_library import library

ROOT=Path(__file__).resolve().parents[1]


def model():
    return next(p for p in library()['hands'] if p['name']=='Suit and tie' and p['hand']=='hour' and p['shadow'] and not p['aod'])


def apply(p,e):
    for k,v in preset_changes(p,e,ROOT,model(),'hour',library()['hands']).items():setattr(e,k,v)


def test_new_elements_and_template_use_50_percent_and_15_px():
    for e in [Element(kind='analog'),Element(kind='pointer'),*template('Analogico').elements]:
        if e.kind not in ('analog','pointer'):continue
        assert all(getattr(e,h+'_length')==50 and getattr(e,h+'_width')==15 for h in ('hour','minute','second'))


@pytest.mark.parametrize('pro',[False,True])
def test_apply_set_first_render_equals_same_value_edit_and_export(tmp_path,pro):
    p=Project();e=Element(kind='analog',x=60,y=60,width=360,height=360,second_hand=True,show_ticks=False,chrono_pro=pro)
    p.elements=[e];apply(p,e)
    assert all(getattr(e,h+'_length_adjusted') and getattr(e,h+'_width_adjusted') for h in ('hour','minute','second'))
    before=png_bytes(render(p))
    for h in ('hour','minute','second'):
        for k,v in hand_edit_changes(e,{h+'_length':50,h+'_width':15},p).items():setattr(e,k,v)
    assert png_bytes(render(p))==before # No more "wake up" after touching the controls.
    # Both modes now use the exact same raster dimensions and pivot.
    for h,view in zip(('hour','minute','second'),pro_views(e)):
        for shadow in (False,True):
            a=hand_image(e,h,p,shadow=shadow);b=hand_image(view,'second',p,shadow=shadow)
            assert a[0].size==b[0].size and a[1]==b[1] and png_bytes(a[0])==png_bytes(b[0])
    source=generate_fprj(p,tmp_path/'source')
    if not pro:
        for hand,attribute in [('hour','HourHand_ImageName'),('minute','MinuteHand_Image'),('second','SecondHand_Image')]:
            widget=next(w for w in ET.parse(source.project_path).getroot().find('Screen') if w.get(attribute,'').endswith('_'+hand+'.png'))
            bitmap,pivot=hand_image(e,hand,p)
            with Image.open(source.project_path.parent/'images'/widget.get(attribute)) as actual:
                assert actual.size==bitmap.size and actual.convert('RGBA').tobytes()==bitmap.tobytes()
    else:
        for h,view in zip(('hour','minute','second'),pro_views(e)):
            exported=tmp_path/'source/app/lua/gfx'/('v0_'+view.id+'.png')
            with Image.open(exported) as actual:assert png_bytes(actual.convert('RGBA'))==png_bytes(hand_image(e,h,p)[0])


def test_apply_retains_explicit_dimensions_and_saved_old_projects(tmp_path):
    p=Project();e=Element(kind='analog',hour_length=31,minute_length=10,second_length=67,hour_width=9,minute_width=5,second_width=3)
    p.elements=[e];p.save(tmp_path/'old.s5faceproj');loaded=Project.load(tmp_path/'old.s5faceproj')
    assert loaded.elements[0]==e and not loaded.elements[0].minute_length_adjusted
    apply(loaded,loaded.elements[0]);result=loaded.elements[0]
    assert [getattr(result,h+'_length') for h in ('hour','minute','second')]==[31,10,67]
    assert [getattr(result,h+'_width') for h in ('hour','minute','second')]==[9,5,3]
    assert all(getattr(result,h+'_length_adjusted') and getattr(result,h+'_width_adjusted') for h in ('hour','minute','second'))


def test_small_model_uses_length_and_thickness_without_an_edit():
    p=Project();e=Element(kind='pointer',width=120,height=120)
    p.elements=[e];preset=next(x for x in library()['hands'] if x['small'])
    for k,v in preset_changes(p,e,ROOT,preset,'second',library()['hands']).items():setattr(e,k,v)
    assert e.second_length==50 and e.second_width==15 and e.second_width_adjusted and e.second_length_adjusted
    before=hand_image(e,'second',p)
    for k,v in hand_edit_changes(e,{'second_length':50,'second_width':15},p).items():setattr(e,k,v)
    after=hand_image(e,'second',p)
    assert before[1]==after[1] and png_bytes(before[0])==png_bytes(after[0])


def test_day_number_uses_two_digit_preview_without_changing_live_source():
    p=Project();e=Element(kind='number',source='day',digits=2,width=100,height=50,size=36)
    p.elements=[e]
    assert SCENARIOS['Normale']['day']==15
    assert element_image(p,e,SCENARIOS['Normale']).tobytes()==element_image(p,e,{'day':15}).tobytes()
    assert element_image(p,e,SCENARIOS['Normale']).tobytes()!=element_image(p,e,{'day':6}).tobytes()
    assert e.source=='day' and not p.validate()


def test_bridge_returns_current_preview_immediately_after_applying_model(tmp_path,monkeypatch):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject
    import s5studio.web_ui as ui
    app=QApplication.instance() or QApplication([]);owner=QObject()
    monkeypatch.setattr(ui,'user_data_root',lambda:tmp_path/'user')
    b=ui.StudioBridge(owner,smoke=True)
    def command(action,**args):
        reply=json.loads(b.command(json.dumps({'action':action,**args})));assert 'error' not in reply,reply
        return reply['state']
    e=next(x for x in b.design.elements if x.kind=='analog' and not x.aod)
    initial=b.state()['preview'];state=command('hand-preset',id=e.id,hand='hour',preset=model()['id'])
    assert state['preview']!=initial
    assert state['preview']==b.image_url(b.project.variant_project(b.variant))
    same=command('edit',id=e.id,changes={'hour_length':50,'hour_width':15})
    assert same['preview']==state['preview']
    state=command('add',kind='pointer');added=next(x for x in state['resolvedElements'] if x['kind']=='pointer')
    assert added['second_length']==50 and added['second_width']==15 and state['values']['day']==15
    messages=[];b.event.connect(messages.append);b.preview_tick()
    assert json.loads(messages[-1])['previewSequence']==b.state_sequence
    b.timer.stop();b.motion_timer.stop()
