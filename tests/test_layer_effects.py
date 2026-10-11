from dataclasses import replace
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from PIL import Image,ImageChops
from s5studio.model import Project,Element
from s5studio.render import static_image,canvas_static,render,element_image
from s5studio.native import generate_fprj
from s5studio.color_picker import graphic_color_changes
from s5studio.live_data import preview_live,live_element
from test_live_transforms import live_runtime


@pytest.mark.parametrize('kind',['rect','circle'])
@pytest.mark.parametrize('fill',[True,False])
def test_outline_and_fill_have_independent_colors_and_width(kind,fill):
    e=Element(kind=kind,width=100,height=60,fill_enabled=fill,color='#ff0000',border_color='#00ff00',border_width=6)
    bitmap=static_image(Project(),e)
    assert bitmap.size==(100,60)
    assert bitmap.getpixel((50,30))==((255,0,0,255) if fill else (0,0,0,0))
    assert bitmap.getpixel((50,1))==(0,255,0,255)
    thin=static_image(Project(),replace(e,fill_enabled=False,border_width=1))
    thick=static_image(Project(),replace(e,fill_enabled=False))
    assert sum(thick.getchannel('A').getdata())>sum(thin.getchannel('A').getdata())
    e.border_color='none';e.fill_enabled=False
    assert static_image(Project(),e).getchannel('A').getbbox() is None


def test_legacy_defaults_persistence_independent_styles_and_color_dialog(tmp_path):
    old=Element.from_dict({'kind':'circle','width':120,'height':60})
    assert old.fill_enabled and old.border_width==0 and not old.shadow_enabled
    assert not Project(elements=[old]).validate()
    for key in ('border_color','shadow_color'):
        assert graphic_color_changes(old,key,'#abcdef')=={key:'#abcdef'}
        assert graphic_color_changes(old,key,None)=={key:'none'}
    old.fill_enabled=False;old.border_width=4;old.shadow_enabled=True;old.shadow_color='#ff00ff'
    p=Project(elements=[old]);p.add_variant();style=p.editable_variant(1)
    style.elements[0].shadow_offset_x=-8;style.elements[0].border_color='#0000ff';p.commit_variant(1,style)
    p.save(tmp_path/'effects.s5faceproj');q=Project.load(tmp_path/'effects.s5faceproj')
    assert q.metadata()==p.metadata()
    assert q.variant_project(0).elements[0].shadow_offset_x==3
    assert q.variant_project(1).elements[0].shadow_offset_x==-8


@pytest.mark.parametrize('kind',['rect','circle','text'])
def test_shadow_color_offset_opacity_and_clipping_are_shared_with_export(tmp_path,kind):
    e=Element(kind=kind,x=15,y=30,width=120,height=40,text='S5',size=28,
              color='#ff0000',shadow_enabled=True,shadow_color='#0000ff',
              shadow_offset_x=-30,shadow_offset_y=45,shadow_blur=3,shadow_spread=2,shadow_opacity=180,
              rotation=20,arc=25,border_width=3)
    p=Project(elements=[e]);assert not p.validate()
    bitmap,x,y=canvas_static(p,e)
    assert 0<=x and 0<=y and x+bitmap.width<=480 and y+bitmap.height<=480
    expected=Image.new('RGBA',(480,480),p.background);expected.alpha_composite(bitmap,(x,y))
    assert render(p,circular=False).tobytes()==expected.tobytes()
    assert any(b>r and a for r,g,b,a in bitmap.getdata())
    source=generate_fprj(p,tmp_path);widget=ET.parse(source.project_path).find('Screen').findall('Widget')[1]
    with Image.open(source.project_path.parent/'images'/widget.get('Bitmap')) as exported:
        assert exported.tobytes()==bitmap.tobytes()
    assert (int(widget.get('X')),int(widget.get('Y')))==(x,y)
    assert canvas_static(p,replace(e,opacity=0)) is None
    no_shadow=replace(e,shadow_opacity=0)
    assert not any(b>r and a for r,g,b,a in canvas_static(p,no_shadow)[0].getdata())


@pytest.mark.parametrize('align,rotation,arc',[('right',0,0),('left',25,70),('center',-20,-60)])
def test_live_shadow_follows_sensor_glyphs_under_all_foreground_digits(tmp_path,align,rotation,arc):
    e=Element(kind='number',source='heartRate',width=180,height=44,size=28,x=140,y=130,
              digits=4,align=align,rotation=rotation,arc=arc,shadow_enabled=True,
              shadow_color='#2399ff',shadow_offset_x=4,shadow_offset_y=6,shadow_blur=3,shadow_spread=1)
    p=Project(elements=[e]);assert not p.validate() and live_element(e)
    lua,module,view=live_runtime(p,e,tmp_path)
    assert len(view.shadows)==e.digits and len(view.images)==e.digits
    for value in (1,15,1234,-12,None):
        lua.globals().DATA.healthHeartRate(value*256 if value is not None else 2147483647)
        actual=Image.new('RGBA',(480,480))
        for group in (view.shadows,view.images):
            for _,img in group.items():
                if not img.flags[1]:
                    with Image.open(tmp_path/'app/lua'/img.src) as bitmap:actual.alpha_composite(bitmap.convert('RGBA'),(img.x,img.y))
        assert actual.tobytes()==preview_live(p,e,{'heartRate':value}).tobytes()
        expected=Image.new('RGBA',(480,480),p.background);expected.alpha_composite(actual)
        assert render(p,{'heartRate':value},circular=False).tobytes()==expected.tobytes()
        writes=[img.writes for group in (view.shadows,view.images) for _,img in group.items()]
        lua.globals().DATA.healthHeartRate(value*256 if value is not None else 2147483647)
        assert writes==[img.writes for group in (view.shadows,view.images) for _,img in group.items()]
    assert lua.globals().LV.Timer is None and lua.globals().LV.Anim is None
    lua.globals().ScreenStateChangedCB('ON','AOD',0);assert view.root.flags[1]
    lua.globals().ScreenStateChangedCB('AOD','ON',0);assert not view.root.flags[1]


@pytest.mark.parametrize('source',['dateWeek','dateMonth'])
def test_calendar_shadow_preserves_native_dynamic_binding(tmp_path,source):
    e=Element(kind='number',source=source,width=270,height=45,size=26,x=100,y=180,
              shadow_enabled=True,shadow_color='#ff0000',rotation=12,arc=40)
    p=Project(elements=[e]);fprj=generate_fprj(p,tmp_path)
    widget=ET.parse(fprj.project_path).find('Screen').findall('Widget')[1]
    assert widget.get('Shape')=='31' and widget.get('Index_Src')==('2012' if source=='dateWeek' else '1012')
    first,second=(1,2)
    name=widget.get('BitmapList').split('|')[first if source=='dateWeek' else first-1].split(':')[1]
    expected,x,y=canvas_static(p,e,element_image(p,e,{source:first}))
    with Image.open(fprj.project_path.parent/'images'/name) as exported:assert exported.tobytes()==expected.tobytes()
    assert render(p,{source:first}).tobytes()!=render(p,{source:second}).tobytes()


@pytest.mark.parametrize('change',[{'border_width':-1},{'shadow_blur':41},{'shadow_opacity':256},
                                   {'shadow_spread':33},{'fill_enabled':'no'},{'shadow_color':'bad'},
                                   {'shadow_enabled':True,'kind':'analog'}])
def test_invalid_effects_are_rejected(change):
    assert Project(elements=[replace(Element(kind='rect'),**change)]).validate()
