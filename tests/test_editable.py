import json
import struct
from pathlib import Path
import zipfile

import pytest
from s5studio.model import Project,template
from s5studio.native import build,inspect_binary
from s5studio.editable import tables
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def editable_project():
    p=template('Analogico')
    p.name='S5 Analogico Studio'
    p.elements=[e for e in p.elements if e.aod or e.kind=='analog']
    for n,color in enumerate(('#6ce5c1','#5f87ff','#e8bb65','#d992fc','#ffffff')):
        p.variants.append({'id':f'v{n}','name':f'Stile {n+1}','accent':color,'background':'','imageAsset':'','overrides':{}})
    p.variants=p.variants[1:]
    options=['none','calories','steps','spo2','sleep','movement','heartRate','weatherCurrentWeather','weatherCurrentTemperature','systemSensorCompass']
    p.complications=[{'id':f'slot{n}','name':f'Slot {n+1}','x':x,'y':y,'options':options,'default':default}
                     for n,((x,y),default) in enumerate(zip([(90,112),(280,112),(28,228),(342,228),(185,332)],['steps','heartRate','weatherCurrentTemperature','systemSensorCompass','weatherCurrentWeather']))]
    return p


def test_roundtrip_and_schema_migration(tmp_path):
    p=editable_project()
    path=tmp_path/'editable.s5faceproj'
    p.save(path)
    assert Project.load(path).metadata()==p.metadata()
    old=p.metadata()
    old['schemaVersion']=1
    old.pop('variants');old.pop('complications')
    with zipfile.ZipFile(tmp_path/'old.s5faceproj','w') as z:z.writestr('project.json',json.dumps(old))
    migrated=Project.load(tmp_path/'old.s5faceproj')
    assert migrated.schema_version==2 and len(migrated.variants)==1 and not migrated.complications


@pytest.mark.integration
def test_five_analog_styles_native_choices_and_previews(tmp_path):
    p=editable_project()
    folder=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(folder/'resource.bin').read_bytes()
    info=inspect_binary(data)
    assert info['screenCount']==10 and info['nativeSlots']==25 and info['directoryStride']==176
    previews=set()
    for index,screen in enumerate(info['screens']):
        assert screen['aod']==bool(index%2)
        assert screen['title']==p.variants[index//2]['name']
        if index%2==0:
            assert sorted(w['source'] for w in screen['widgets'] if w['source'] in ('0811','1011','1811'))==['0811','1011','1811']
            slots=tables(data,index)[8]
            assert sorted(struct.unpack_from('<H',payload)[0] for _,_,payload in slots)==[10]*5
            previews.add(struct.unpack_from('<I',data,168+176*index+4)[0])
    assert len(previews)==5
    # Default steps resolves to a live numeric source, while the frame is
    # an actual runtime child, not a dial baked into someone else's background.
    available={uid:(i,b) for i,rows in enumerate(tables(data)) for uid,_,b in rows if i}
    slot=tables(data)[8][0][2];default_group=struct.unpack_from('<I',slot,4)[0]
    group=available[default_group][1];count=struct.unpack_from('<H',group,40)[0]
    children=[struct.unpack_from('<I',group,48+12*n)[0] for n in range(count)]
    assert any(available[u][0]==2 for u in children)
    assert any(available[u][0]==7 and available[u][1][:2].hex().upper()=='0821' for u in children)
    with zipfile.ZipFile(next(folder.glob('*_TEMPLATE.zip'))) as z:
        import xml.etree.ElementTree as ET
        manifest=ET.fromstring(z.read('resources/manifest.xml'))
        assert [t.get('name') for t in manifest.findall('Theme')]==[s['title'] for s in info['screens']]
        images={n.get('name'):n.get('src') for n in manifest.find('Resources') if n.tag=='Image'}
        thumbs=[z.read('resources/'+images[t.get('preview')[1:]]) for t in manifest.findall('Theme') if t.get('type')=='normal']
        assert len(set(thumbs))==5
    corrupt=bytearray(data)
    _,offset=struct.unpack_from('<II',data,168+8+8*8)
    _,_,pos,_=struct.unpack_from('<IIII',data,offset)
    struct.pack_into('<I',corrupt,pos+4,0x0900ffff)
    with pytest.raises(ValueError,match='riferimenti'):inspect_binary(bytes(corrupt))


@pytest.mark.integration
def test_custom_hand_bitmap_pivot_and_real_center(tmp_path):
    p=template('Analogico');p.aod_enabled=False;p.elements=[e for e in p.elements if e.kind=='analog' and not e.aod]
    bitmap=tmp_path/'mia_lancetta.png'
    im=Image.new('RGBA',(17,120));ImageDraw.Draw(im).line((4,2,4,116),fill='#ddaa44',width=3);im.save(bitmap)
    imported=p.add_image(bitmap);p.elements.remove(imported)
    hand=p.elements[0];hand.hour_asset=imported.asset;hand.hour_anchor_x=4;hand.hour_anchor_y=110
    project=tmp_path/'personalizzato.s5faceproj';p.save(project)
    bitmap.unlink()
    p=Project.load(project)
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path/'built')
    rows=tables((output/'resource.bin').read_bytes())
    uid,_,payload=next(row for row in rows[7] if row[2][:2].hex().upper()=='0811')
    assert struct.unpack_from('<HH',payload,20)==(4,110)
    layout=next(row[2] for row in rows[0] if struct.unpack_from('<I',row[2])[0]==uid)
    x,y=struct.unpack_from('<hh',layout,4)
    assert (x+4,y+110)==(240,240)
    image_uid=struct.unpack_from('<I',payload,8)[0]
    native_image=next(row[2] for row in rows[2] if row[0]==image_uid)
    assert struct.unpack_from('<HH',native_image,4)==(17,120)
