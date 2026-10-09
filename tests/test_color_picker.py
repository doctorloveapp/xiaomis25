import os
import hashlib
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
import json

from PIL import Image
import pytest

from s5studio.color_picker import graphic_color_changes,graphic_color_state,choose_graphic_color
from s5studio.model import Element,Project
from s5studio.render import hand_image,static_image,png_bytes
from s5studio.native import generate_fprj


@pytest.mark.parametrize('kind,key,asset_key',[('analog','hour_color','hour_asset'),('analog','minute_color','minute_asset'),('analog','second_color','second_asset'),('pointer','second_color','second_asset'),('pointer','color','second_asset'),('image','color','asset'),('compass','color','asset')])
def test_absent_tint_restores_original_pixels_and_keeps_alpha(kind,key,asset_key,tmp_path):
    raw=png_bytes(Image.new('RGBA',(20,80),(44,133,211,173)))
    key_asset='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
    p=Project();p.assets[key_asset]=raw
    e=Element(kind=kind,width=20,height=80,tint=True,color='#ff0000',hour_color='#ff0000',minute_color='#ff0000',second_color='#ff0000')
    if kind=='compass':e.source='systemSensorCompass';e.value_range=360;e.angle_range=-360
    setattr(e,asset_key,key_asset);p.elements=[e]
    state=graphic_color_state(e,key);assert not state['original']
    for prop,value in graphic_color_changes(e,key,None).items():setattr(e,prop,value)
    assert graphic_color_state(e,key)['original']
    bitmap=static_image(p,e) if kind=='image' else hand_image(e,state['role'] or 'second',p)[0]
    # RGBA resize can round premultiplied RGB by one unit; compare with the
    # original PNG resized identically, rather than interpreting that as tint.
    expected=Image.open(BytesIO(raw)).convert('RGBA').resize(bitmap.size,Image.Resampling.LANCZOS)
    assert bitmap.tobytes()==expected.tobytes() and bitmap.getchannel('A').getextrema()==(173,173)
    assert p.assets[key_asset]==raw
    p.save(tmp_path/'original.s5faceproj');loaded=Project.load(tmp_path/'original.s5faceproj')
    assert graphic_color_state(loaded.elements[0],key)['original']


def test_selected_color_reenables_tint_and_invalid_colors_do_not_change_element():
    e=Element(kind='compass',asset='assets/source.png',tint=False)
    assert graphic_color_changes(e,'color','#abcdef')=={'color':'#abcdef','tint':True}
    before=asdict(e)
    with pytest.raises(ValueError):graphic_color_changes(e,'color','transparent')
    assert asdict(e)==before
    assert graphic_color_changes(Element(kind='text'),'color',None)=={'color':'none'}


@pytest.mark.parametrize('choice',['original','color','cancel'])
def test_real_qt_color_dialog_checkbox_and_cancel(choice):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication,QColorDialog,QCheckBox
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QColor
    app=QApplication.instance() or QApplication([])
    e=Element(kind='analog',hour_asset='assets/source.png',hour_color='#ff0000')
    observations=[]
    def operate():
        dialog=app.activeModalWidget();assert isinstance(dialog,QColorDialog)
        box=dialog.findChild(QCheckBox,'studio-original-color')
        observations.append(box.isVisible() and not box.isChecked())
        box.setChecked(True)
        if choice=='color':
            dialog.setCurrentColor(QColor('#123456'));observations.append(not box.isChecked())
        if choice=='cancel':dialog.reject()
        else:dialog.accept()
    QTimer.singleShot(0,operate)
    result=choose_graphic_color(e,'hour_color',None)
    assert all(observations)
    assert result==({'hour_color':''} if choice=='original' else {'hour_color':'#123456'} if choice=='color' else None)
    assert e.hour_color=='#ff0000'


def test_no_tint_png_is_used_in_native_export(tmp_path):
    import xml.etree.ElementTree as ET
    p=Project();p.assets['assets/source.png']=png_bytes(Image.new('RGBA',(20,80),(44,133,211,173)))
    e=Element(kind='image',asset='assets/source.png',width=20,height=80,tint=True,color='#ff0000');p.elements=[e]
    for key,value in graphic_color_changes(e,'color',None).items():setattr(e,key,value)
    generated=generate_fprj(p,tmp_path/'native')
    screen=ET.parse(generated.project_path).getroot().find('Screen')
    bitmaps=[generated.project_path.parent/'images'/w.get('Bitmap') for w in screen if w.get('Bitmap')]
    assert any(Image.open(path).convert('RGBA').getpixel((0,0))==(44,133,211,173) for path in bitmaps)


def test_general_hand_color_hides_only_cap_in_preview_native_and_lua(tmp_path):
    from s5studio.render import element_image,render
    from s5studio.lua_runtime import write_scene,scene_layers
    e=Element(kind='analog',width=480,height=480,x=0,y=0,second_hand=True,show_ticks=False)
    p=Project(elements=[e]);before=asdict(e)
    for key,value in graphic_color_changes(e,'color',None).items():setattr(e,key,value)
    assert not e.show_center_cap and e.color==before['color']
    assert all(getattr(e,key)==before[key] for key in ('hour_color','minute_color','second_color'))
    source=generate_fprj(p,tmp_path/'native')
    assert not any(path.name.endswith('_center.png') for path in (tmp_path/'native/images').glob('*.png'))
    e.chrono_pro=True
    name=write_scene(p,scene_layers(p),tmp_path/'pro',0)
    assert '_center.png' not in (tmp_path/'pro/app'/name).read_text(encoding='utf8')
    p.save(tmp_path/'cap.s5faceproj');assert not Project.load(tmp_path/'cap.s5faceproj').elements[0].show_center_cap
    assert Element.from_dict({'kind':'analog'}).show_center_cap


@pytest.mark.parametrize('kind',['text','rect','circle','number'])
def test_absent_fill_and_background_are_transparent_and_persist(kind,tmp_path):
    from s5studio.render import element_image,render
    e=Element(kind=kind)
    for key,value in graphic_color_changes(e,'color',None).items():setattr(e,key,value)
    p=Project(elements=[e],background='none')
    assert not p.validate() and element_image(p,e,{'batteryPercent':82}).getchannel('A').getbbox() is None
    assert render(p).getchannel('A').getbbox() is None
    p.save(tmp_path/'transparent.s5faceproj');q=Project.load(tmp_path/'transparent.s5faceproj')
    assert q.background=='none' and q.elements[0].color=='none'
    assert graphic_color_changes(q.elements[0],'color','#123456')=={'color':'#123456'}


@pytest.mark.parametrize('target,key,expected',[
    ({'background':'#112233'},'background','none'),
    ({'color':'#112233','background':'#223344'},'color','none'),
    ({'color':'#112233','background':'#223344'},'background','none'),
    ({'accent':'#112233'},'accent',''),
])
def test_all_dictionary_color_contexts_support_absent_color(target,key,expected):
    changes=graphic_color_changes(target,key,None);assert changes=={key:expected}
    target.update(changes);assert graphic_color_state(target,key)['original']
