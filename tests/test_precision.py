from dataclasses import replace
from io import BytesIO
from pathlib import Path
import hashlib
import json
import struct
import xml.etree.ElementTree as ET

import pytest
from PIL import Image,ImageDraw
from s5studio.model import Project,Element,SOURCES
from s5studio.render import hand_image,hand_edit_changes,hand_preview,render,png_bytes,hand_shadow_offset
from s5studio.watchface_library import library,read_tables
from s5studio.compass_catalog import preset_changes
from s5studio.native import generate_fprj,build
from s5studio.template_package import validate_template_output
from s5studio.source_help import source_choices

ROOT=Path(__file__).resolve().parents[1]


def graphic(project,bitmap):
    raw=png_bytes(bitmap);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
    project.assets[key]=raw;return key


def hand_project(kind='analog'):
    p=Project();im=Image.new('RGBA',(48,180));ImageDraw.Draw(im).rectangle((18,20,29,159),fill='#e0ac6e')
    shadow=Image.new('RGBA',(48,180));ImageDraw.Draw(shadow).rectangle((18,20,29,159),fill=(0,0,0,180))
    e=Element(kind=kind,x=80,y=80,width=320,height=320,hour_asset=graphic(p,im),hour_anchor_x=24,hour_anchor_y=160,
              hour_pivot_reference_x=24,hour_pivot_reference_y=160,
              hour_shadow_asset=graphic(p,shadow),hour_shadow_anchor_x=24,hour_shadow_anchor_y=160,
              hour_shadow_offset_x=2,hour_shadow_offset_y=3)
    p.elements=[e];return p,e


def edit(p,e,**changes):
    for k,v in hand_edit_changes(e,changes,p).items():setattr(e,k,v)


def test_imported_hand_keeps_old_geometry_until_axis_is_adjusted():
    p,e=hand_project();before,anchor=hand_image(e,'hour',p)
    assert before.size==(48,180) and anchor==(24,160)
    edit(p,e,hour_length=35)
    main,pivot=hand_image(e,'hour',p);bounds=main.getchannel('A').getbbox()
    assert pivot[1]-bounds[1]==112  # 35% of the 320px level
    assert bounds[2]-bounds[0]==12  # changing length doesn't change thickness
    edit(p,e,hour_width=24)
    wide,pivot=hand_image(e,'hour',p)
    assert wide.width==24 and pivot[1]==112
    assert hashlib.sha256(p.assets[e.hour_asset]).digest()==hashlib.sha256(png_bytes(before)).digest()


def test_imported_shadow_uses_the_same_anisotropic_transform_and_pivot():
    p,e=hand_project();edit(p,e,hour_length=70,hour_width=24)
    main,pivot=hand_image(e,'hour',p);shadow,shadow_pivot=hand_image(e,'hour',p,shadow=True)
    assert main.size==shadow.size and pivot==shadow_pivot
    assert hand_shadow_offset(e,'hour',p)==(4,5)
    edit(p,e,hour_anchor_x=22,hour_anchor_y=150)
    assert e.hour_pivot_reference_x==24 and e.hour_pivot_reference_y==160
    assert hand_image(e,'hour',p)[1]==hand_image(e,'hour',p,shadow=True)[1]


def test_small_pointer_thickness_and_manual_pivot_are_independent():
    p,e=hand_project();e.kind='pointer';e.second_asset=e.hour_asset;e.second_anchor_x=24;e.second_anchor_y=160
    original=hand_image(e,'second',p)[0]
    edit(p,e,second_width=30)
    wide,anchor=hand_image(e,'second',p)
    assert wide.width==30 and wide.height==original.height and anchor[1]==wide.height-1
    edit(p,e,second_anchor_x=20,second_anchor_y=140)
    assert not e.pointer_end_pivot
    _,anchor=hand_image(e,'second',p)
    assert anchor[1]<hand_image(e,'second',p)[0].height-1


def test_hand_preview_reports_source_pixels_including_transparent_padding():
    p,e=hand_project();preview=hand_preview(e,'hour',p)
    assert preview['pivotX']+preview['originX']==24 and preview['pivotY']+preview['originY']==160
    assert preview['asset']==e.hour_asset
    edit(p,e,hour_length=70,hour_width=60)
    assert hand_preview(e,'hour',p)==preview  # click mapping doesn't depend on export scaling


def test_shadow_remains_aligned_when_small_pointer_switches_from_endpoint_to_click():
    p,e=hand_project();e.kind='pointer'
    for suffix in ('_asset','_anchor_x','_anchor_y','_shadow_asset','_shadow_anchor_x','_shadow_anchor_y','_pivot_reference_x','_pivot_reference_y'):
        setattr(e,'second'+suffix,getattr(e,'hour'+suffix))
    edit(p,e,second_anchor_x=25,second_anchor_y=150)
    assert not e.pointer_end_pivot
    assert hand_image(e,'second',p)[1]==hand_image(e,'second',p,shadow=True)[1]


def test_source_menu_removes_aliases_and_explains_distinct_digit_fields():
    labels,descriptions=source_choices(SOURCES)
    assert len(labels)==len(set(labels.values()))==58
    assert 'hour' not in labels and 'timeHour' in labels
    assert all(descriptions[k] for k in labels)
    assert '14' in descriptions['timeHour'] and 'vale 4' in descriptions['timeHourLow'] and 'vale 1' in descriptions['timeHourHigh']
    assert SOURCES['timeHour'][1]!=SOURCES['timeHourLow'][1]!=SOURCES['timeHourHigh'][1]


def test_all_compass_graphics_have_verified_hashes_and_central_pivots():
    compasses=library()['compasses'];assert len(compasses)==10
    for c in compasses:
        raw=(ROOT/c['assetPath']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==c['sourceSha256']
        with Image.open(BytesIO(raw)) as im:assert c['pivot']==[im.width//2,im.height//2]
        assert (c['source'],c['valueRange'],c['angleRange'])==('systemSensorCompass',360,-360)
    assert sum('components' in c for c in compasses)==2


def compass_fixture():
    p=Project(name='Verifica bussola');e=Element(kind='compass',x=180,y=160,width=120,height=120)
    c=next(c for c in library()['compasses'] if c['name']=='Ferrari' and c['kind']=='Rosa completa')
    for k,v in preset_changes(p,ROOT,c).items():setattr(e,k,v)
    p.elements=[e];return p,e


def test_compass_uses_counterclockwise_real_heading_and_the_same_fprj_centre(tmp_path):
    p,e=compass_fixture();assert not p.validate()
    north=render(p,{'systemSensorCompass':0},circular=False)
    east=render(p,{'systemSensorCompass':90},circular=False)
    expected=north.rotate(90,center=(240,220),resample=Image.Resampling.BICUBIC)
    # Compare the visible dial away from the full-canvas background.
    assert east.crop((170,150,310,290)).tobytes()==expected.crop((170,150,310,290)).tobytes()
    source=generate_fprj(p,tmp_path)
    widget=next(w for w in ET.parse(source.project_path).getroot().iter('Widget') if w.attrib['Name']=='pointer_'+e.id)
    assert int(widget.attrib['X'])+int(widget.attrib['MinuteImage_rotate_xc'])==240
    assert int(widget.attrib['Y'])+int(widget.attrib['MinuteImage_rotate_yc'])==220


def test_precision_changes_survive_save_variants_and_reload(tmp_path):
    p,e=hand_project();edit(p,e,hour_length=60,hour_width=18,hour_anchor_x=23,hour_anchor_y=152)
    p.variants[0]['overrides']={e.id:{'minute_length_adjusted':True,'minute_width_adjusted':True,'minute_length':50,'minute_width':10}}
    before=render(p).tobytes();path=tmp_path/'precision.s5faceproj';p.save(path);loaded=Project.load(path)
    assert loaded.elements[0].hour_length_adjusted and loaded.elements[0].hour_width_adjusted
    assert loaded.elements[0].hour_pivot_reference_y==160 and render(loaded).tobytes()==before
    assert loaded.variant_project(0).elements[0].minute_length_adjusted


def test_bridge_pivot_sets_exact_source_coordinates_and_undo():
    from PySide6.QtWidgets import QApplication,QMainWindow
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);win=QMainWindow();bridge=StudioBridge(win,smoke=True)
    p,e=hand_project();e.kind='pointer';e.second_asset=e.hour_asset;e.second_anchor_x=24;e.second_anchor_y=160
    bridge.project=p
    result=json.loads(bridge.command(json.dumps({'action':'hand-pivot','id':e.id,'hand':'second','x':25,'y':143,'asset':e.second_asset})))
    assert not result.get('error') and (e.second_anchor_x,e.second_anchor_y)==(25,143) and not e.pointer_end_pivot
    bridge.command(json.dumps({'action':'undo'}));assert bridge.project.elements[0].pointer_end_pivot
    result=json.loads(bridge.command(json.dumps({'action':'hand-pivot','id':e.id,'hand':'second','x':25,'y':143,'asset':'stale'})))
    assert result.get('error') and bridge.project.elements[0].second_anchor_y==160


@pytest.mark.integration
def test_compass_sensor_and_resized_hand_are_written_into_native_payload(tmp_path):
    p,compass=compass_fixture();hands,clock=hand_project();p.assets.update(hands.assets)
    edit(p,clock,hour_length=40,hour_width=20,hour_anchor_x=24,hour_anchor_y=152)
    p.elements.append(clock)
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(output/'resource.bin').read_bytes();tables=read_tables(data)
    pointers=[(uid,b) for uid,_,b in tables[7] if b[:2]==bytes.fromhex(SOURCES['systemSensorCompass'][1])]
    assert len(pointers)==1
    uid,b=pointers[0];assert b[3]>>4==3
    assert struct.unpack_from('<II',b,12)==(0,360<<8)
    assert struct.unpack_from('<hh',b,24)==(0,-3600)
    layout=next(b for _,_,b in tables[0] if struct.unpack_from('<I',b)[0]==uid)
    assert tuple(a+c for a,c in zip(struct.unpack_from('<hh',layout,4),struct.unpack_from('<HH',b,20)))==(240,220)
    shape=ET.parse(output/'sorgenti-easyface/quadrante.fprj').getroot()
    clock_widget=next(w for w in shape.iter('Widget') if w.attrib['Name'].startswith('el_') and w.attrib.get('HourHand_ImageName','').endswith('_hour.png'))
    bitmap=Image.open(output/'sorgenti-easyface/images'/clock_widget.attrib['HourHand_ImageName'])
    expected,anchor=hand_image(clock,'hour',p)
    assert bitmap.size==expected.size and int(clock_widget.attrib['HourImage_rotate_yc'])==anchor[1]
    assert validate_template_output(ROOT/'quadrante_funzionante.zip',next(output.glob('*_TEMPLATE.zip')))['status']=='passed'
