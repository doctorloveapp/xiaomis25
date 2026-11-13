"""Formatting persistence and shared native/live/preview geometry."""
from dataclasses import replace
import xml.etree.ElementTree as ET

import pytest
from s5studio.model import Element, Project
from s5studio.render import (static_image, digit_metrics, digit_image, number_parts,
                             element_image, layout_errors, png_bytes)
from s5studio.live_data import glyph_positions
from s5studio.native import generate_fprj


def test_formatting_roundtrip_and_old_defaults(tmp_path):
    e=Element(italic=True,underline=True,letter_spacing=7,bold=False)
    p=Project(elements=[e])
    path=tmp_path/'format.s5faceproj'
    p.save(path)
    loaded=Project.load(path).elements[0]
    assert (loaded.italic,loaded.underline,loaded.letter_spacing,loaded.bold)==(True,True,7,False)
    assert (Element().italic,Element().underline,Element().letter_spacing)==(False,False,0)


@pytest.mark.parametrize('spacing',[-1,41,1.5,True])
def test_invalid_tracking_is_rejected(spacing):
    assert any('spaziatura' in error for error in Project(elements=[Element(letter_spacing=spacing)]).validate())


@pytest.mark.parametrize('align',['left','center','right'])
def test_native_tracking_matches_live_positions_and_preview(tmp_path,align):
    e=Element(kind='number',source='batteryPercent',width=300,height=80,size=30,
              digits=3,letter_spacing=8,underline=True,align=align)
    p=Project(elements=[e])
    cw,ch,_=digit_metrics(p,e)
    positions=glyph_positions(p,e,2)
    assert positions[1][0]-positions[0][0]==cw+8
    expected=element_image(p,replace(e,leading_zero=False),{'batteryPercent':12})
    from PIL import Image
    actual=Image.new('RGBA',(e.width,e.height))
    for char,position in zip('12',positions):actual.alpha_composite(digit_image(p,e,char),position)
    assert actual.tobytes()==expected.tobytes()
    source=generate_fprj(p,tmp_path/'source')
    widget=next(w for w in ET.parse(source.project_path).iter('Widget') if w.get('Shape')=='32')
    assert widget.get('Spacing')=='8'
    assert int(widget.get('Width'))==3*cw+16
    assert int(widget.get('Height'))==ch


def test_text_tracking_underline_and_italic_change_pixels():
    p=Project()
    e=Element(text='12345',width=300,height=90,size=36)
    base=png_bytes(static_image(p,e))
    for changes in ({'letter_spacing':8},{'underline':True},{'italic':True},{'bold':False}):
        assert png_bytes(static_image(p,replace(e,**changes)))!=base
    tracked=static_image(p,replace(e,letter_spacing=8)).getbbox()
    regular=static_image(p,e).getbbox()
    assert tracked[2]-tracked[0]>regular[2]-regular[0]


def test_tracking_is_included_in_layout_validation():
    e=Element(kind='number',source='batteryPercent',width=100,height=80,size=30,letter_spacing=40)
    assert layout_errors(Project(elements=[e]))


def test_clock_separator_accounts_for_tracking():
    p=Project()
    e=Element(kind='clock',width=400,height=100,align='left',letter_spacing=9)
    cw,_,_=digit_metrics(p,e)
    groups,sep=number_parts(p,e)
    assert sep[1]==2*cw+18
    assert groups[1][2]==sep[1]+sep[3]+9
