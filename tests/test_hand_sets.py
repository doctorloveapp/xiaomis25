from pathlib import Path
from io import BytesIO
from dataclasses import replace
import hashlib,json,os,struct,xml.etree.ElementTree as ET,zipfile
import pytest
from PIL import Image,ImageDraw,ImageChops
from s5studio.model import Project,Element
from s5studio.hand_presets import preset_changes,clear_hand_changes
from s5studio.watchface_library import library,read_tables
from s5studio.render import hand_image,hand_shadow_offset,element_image,png_bytes,render
from s5studio.native import build,generate_fprj

ROOT=Path(__file__).resolve().parents[1]

def suit():
    return next(p for p in library()['hands'] if p['name']=='Suit and tie' and p['hand']=='hour' and p['shadow'] and not p['aod'])

def apply(p,e,preset,hand):
    for k,v in preset_changes(p,e,ROOT,preset,hand,library()['hands']).items():setattr(e,k,v)

def test_hour_set_pairs_three_shadows_manual_override_and_roundtrip(tmp_path):
    p=Project();e=Element(kind='analog',x=0,y=0,width=480,height=480,show_ticks=False);p.elements=[e]
    original=suit();apply(p,e,original,'hour')
    for h in ('hour','minute','second'):
        assert getattr(e,h+'_preset')==original['setMembers'][h]
        assert getattr(e,h+'_shadow_asset') in p.assets
    hour=e.hour_asset;second=e.second_asset
    another=next(m for m in library()['hands'] if m['hand']=='minute' and m['sourceSha256']!=hashlib.sha256(p.assets[e.minute_asset]).hexdigest())
    apply(p,e,another,'minute')
    assert e.hour_asset==hour and e.second_asset==second and e.minute_preset==another['id']
    p.variants.append({'id':'off','name':'Senza ombre','accent':'#6ce5c1','overrides':{e.id:{'show_shadows':False}}})
    p.save(tmp_path/'set.s5faceproj');loaded=Project.load(tmp_path/'set.s5faceproj')
    assert loaded.elements[0]==e and loaded.variant_project(1).elements[0].show_shadows is False
    assert all(getattr(e,h+'_shadow_asset') in loaded.assets for h in ('hour','second'))
    for k,v in clear_hand_changes('hour').items():setattr(e,k,v)
    assert not e.hour_shadow_asset and not e.hour_preset and e.second_asset==second

def test_shadows_preserve_their_colour_and_toggle_in_preview(tmp_path):
    p=Project();e=Element(kind='analog',x=0,y=0,width=480,height=480,show_ticks=False);p.elements=[e];apply(p,e,suit(),'hour')
    shadow_before=hand_image(e,'hour',p,shadow=True)[0].tobytes()
    e.hour_color='#ff0000'
    assert hand_image(e,'hour',p,shadow=True)[0].tobytes()==shadow_before
    on=element_image(p,e,{'hour':10,'minute':8,'second':30});off=element_image(p,replace(e,show_shadows=False),{'hour':10,'minute':8,'second':30})
    assert ImageChops.difference(on,off).getbbox()
    source=generate_fprj(p,tmp_path/'on')
    widgets=ET.parse(source.project_path).getroot().find('Screen').findall('Widget')
    assert sum(w.get('Shape')=='27' for w in widgets)==4
    e.show_shadows=False;source=generate_fprj(p,tmp_path/'off')
    assert sum(w.get('Shape')=='27' for w in ET.parse(source.project_path).getroot().find('Screen'))==1

def test_small_custom_pointer_uses_visible_endpoint_and_length(tmp_path):
    p=Project();e=Element(kind='pointer',source='second',x=160,y=160,width=160,height=160,second_length=40);p.elements=[e]
    image=Image.new('RGBA',(100,480));ImageDraw.Draw(image).rectangle((48,170,52,230),fill='white')
    raw=png_bytes(image);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw
    e.second_asset=key;e.second_anchor_x=50;e.second_anchor_y=200
    hand,anchor=hand_image(e,'second',p)
    assert anchor[1]==hand.height-1 and abs(hand.height-65)<=1
    assert hand.getchannel('A').getbbox()[3]==hand.height and p.assets[key]==raw
    source=generate_fprj(p,tmp_path)
    pointer=next(w for w in ET.parse(source.project_path).getroot().find('Screen') if w.get('Name','').startswith('pointer_'))
    assert (int(pointer.get('MinuteImage_rotate_xc')),int(pointer.get('MinuteImage_rotate_yc')))==anchor
    top=element_image(p,e,{'second':0});right=element_image(p,e,{'second':15});bottom=element_image(p,e,{'second':30})
    assert top.getbbox()[3]<=81 and right.getbbox()[0]>=79 and bottom.getbbox()[1]>=79
    # The manual mode retains a pivot set explicitly by the designer.
    e.pointer_end_pivot=False
    assert hand_image(e,'second',p)[1][1]<hand_image(e,'second',p)[0].height-1

def test_small_synthetic_pointer_and_external_vendor_pivot():
    e=Element(kind='pointer',width=120,height=120)
    hand,anchor=hand_image(e,'second',Project());assert anchor[1]==hand.height-1
    preset=next(m for m in library()['hands'] if m['externalPivot'])
    p=Project();apply(p,e,preset,'second');p.elements=[e]
    assert not p.validate()
    hand,anchor=hand_image(e,'second',p);assert 0<=anchor[1]<hand.height

def test_imported_clock_hand_preview_clips_at_watch_not_selection_box(tmp_path):
    p=Project(background='#000000')
    e=Element(kind='analog',x=190,y=190,width=100,height=100,show_ticks=False)
    image=Image.new('RGBA',(10,300));ImageDraw.Draw(image).rectangle((3,20,7,248),fill='#ff0000')
    raw=png_bytes(image);key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[key]=raw
    e.hour_asset=key;e.hour_anchor_x=5;e.hour_anchor_y=250;p.elements=[e]
    preview=render(p,{'hour':0,'minute':0,'second':0},circular=False)
    assert preview.getpixel((240,20))[:3]==(255,0,0)
    assert preview.getpixel((240,9))[:3]==(0,0,0)
    source=generate_fprj(p,tmp_path)
    widget=next(w for w in ET.parse(source.project_path).getroot().find('Screen') if w.get('Shape')=='27')
    origin_y=int(widget.get('Y'))+int(widget.get('Height'))//2-int(widget.get('HourImage_rotate_yc'))
    assert origin_y+20==10 and int(widget.get('HourImage_rotate_yc'))==250
    with Image.open(source.project_path.parent/'images'/widget.get('HourHand_ImageName')) as im:
        assert im.getpixel((5,30))[:3]==preview.getpixel((240,origin_y+30))[:3]

def test_every_save_prompts_and_cancel_retains_current_path(tmp_path,monkeypatch):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication,QFileDialog
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);owner=QObject();bridge=StudioBridge(owner,smoke=True)
    names=iter([str(tmp_path/'primo'),str(tmp_path/'secondo.s5faceproj'),'']);calls=[]
    def dialog(*args):calls.append(args[2]);return next(names),'Progetti S5'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',dialog)
    assert bridge.save() and bridge.save()
    bridge.dirty=True;before=bridge.path
    assert not bridge.save() and bridge.path==before and bridge.dirty
    assert len(calls)==3 and calls[1].endswith('primo.s5faceproj') and calls[2].endswith('secondo.s5faceproj')
    assert Project.load(tmp_path/'primo.s5faceproj') and Project.load(tmp_path/'secondo.s5faceproj')

def test_bridge_variant_set_and_common_manual_override(monkeypatch):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication
    from s5studio.web_ui import StudioBridge
    app=QApplication.instance() or QApplication([]);owner=QObject();bridge=StudioBridge(owner,smoke=True)
    element=next(e for e in bridge.project.elements if not e.aod and e.kind=='analog')
    def command(action,**kw):
        result=json.loads(bridge.command(json.dumps({'action':action,**kw})))
        assert not result.get('error'),result
    command('add-variant')
    command('hand-preset',id=element.id,hand='hour',preset=suit()['id'],variantOnly=True)
    resolved=bridge.project.variant_project(1).elements[0]
    assert resolved.hour_preset==suit()['id'] and resolved.minute_shadow_asset and resolved.second_shadow_asset
    assert not bridge.project.elements[0].hour_asset
    second=resolved.second_preset;hour=resolved.hour_preset
    minute=next(p for p in library()['hands'] if p['hand']=='minute' and p['id']!=resolved.minute_preset)
    command('hand-preset',id=element.id,hand='minute',preset=minute['id'])
    resolved=bridge.project.variant_project(1).elements[0]
    assert resolved.minute_preset==minute['id'] and resolved.hour_preset==hour and resolved.second_preset==second
    command('clear-hand',id=element.id,hand='hour')
    assert not bridge.project.variant_project(1).elements[0].hour_shadow_asset
    command('undo')
    assert bridge.project.variant_project(1).elements[0].hour_preset==hour

@pytest.mark.integration
def test_native_shadow_pointer_has_same_binding_and_real_endpoint_in_aod(tmp_path):
    p=Project(aod_enabled=True);analog=Element(kind='analog',x=0,y=0,width=480,height=480,show_ticks=False);apply(p,analog,suit(),'hour')
    needle=Element(kind='pointer',name='Sottoquadrante',source='batteryPercent',x=180,y=170,width=120,height=120,value_range=100,angle_start=-90,angle_range=180)
    small=next(m for m in library()['hands'] if m['small'] and m['shadow'])
    apply(p,needle,small,'second');aod=replace(needle,id='a0d000000001',aod=True)
    p.elements=[analog,needle,aod,Element(kind='clock',name='Ora AOD',aod=True,x=100,y=350,width=280,height=60,size=40)]
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(output/'resource.bin').read_bytes()
    for screen in (0,1):
        tables=read_tables(data,screen)
        pointers=[b for _,_,b in tables[7] if b[:2].hex()=='0841']
        assert len(pointers)==2
        for b in pointers:
            assert struct.unpack_from('<II',b,12)==(0,100<<8)
            assert struct.unpack_from('<hh',b,24)==(-900,1800)
        main,anchor=hand_image(needle,'second',p)
        assert tuple(struct.unpack_from('<HH',pointers[-1],20))==anchor and anchor[1]==main.height-1
        centres={}
        layouts={struct.unpack_from('<I',b)[0]:struct.unpack_from('<hh',b,4) for _,_,b in tables[0]}
        for uid,_,b in tables[7]:
            if b[3]>>4!=3:continue
            x,y=layouts[uid];ax,ay=struct.unpack_from('<HH',b,20)
            centres.setdefault(b[:2].hex(),[]).append((x+ax,y+ay))
        cx,cy=needle.x+needle.width//2,needle.y+needle.height//2
        dx,dy=hand_shadow_offset(needle,'second',p)
        assert centres['0841']==[(cx+dx,cy+dy),(cx,cy)]
        if screen==0:
            for h,code in [('hour','0811'),('minute','1011'),('second','1811')]:
                dx,dy=hand_shadow_offset(analog,h,p)
                assert centres[code]==[(240+dx,240+dy),(240,240)]
    with zipfile.ZipFile(next(output.glob('*_TEMPLATE.zip'))) as z:
        manifest=ET.fromstring(z.read('resources/manifest.xml'))
        assert len([n for n in manifest.iter('DataItemPointer') if n.get('source')=='systemStatusBattery'])==4
