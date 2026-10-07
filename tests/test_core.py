from io import BytesIO
from pathlib import Path
import json
import zipfile
import struct
import pytest
from PIL import Image
from io import BytesIO

from s5studio.model import Project, template, Element, archive_members
from s5studio.render import render, png_bytes, layout_errors, SCENARIOS
from s5studio.native import generate_fprj, inspect_binary, inspect_mwz, build, assign_binary_id

ROOT=Path(__file__).resolve().parents[1]


def test_project_roundtrip_with_images_font_and_aod(tmp_path):
    image=tmp_path/'foto personale.png'
    Image.new('RGB',(900,600),'#456789').save(image)
    p=template('Salute')
    p.add_image(image,background=True)
    font=Path('C:/Windows/Fonts/arial.ttf')
    if font.exists():
        p.elements[2].font_asset=p.add_font(font)
    p.aod_enabled=True
    p.elements.append(Element(kind='clock',aod=True,width=260,height=80,size=58))
    path=tmp_path/'trasportabile.s5faceproj'
    p.save(path,png_bytes(render(p)))
    image.unlink()
    restored=Project.load(path)
    assert restored.metadata()==p.metadata()
    assert restored.assets==p.assets
    assert render(restored).tobytes()==render(p).tobytes()


@pytest.mark.parametrize('member',['../outside','C:/evil','assets\\escape.png','/absolute'])
def test_archive_rejects_unsafe_paths(tmp_path,member):
    path=tmp_path/'bad.zip'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr(member,b'x')
    if '\\' in member:
        # Windows ZipInfo normalizes backslashes when constructing a ZIP.
        # Write a genuinely malformed external archive, including both headers.
        path.write_bytes(path.read_bytes().replace(member.replace('\\','/').encode(),member.encode()))
    with zipfile.ZipFile(path) as z:
        with pytest.raises(ValueError,match='non sicuro'):
            archive_members(z)


def test_schema_rejects_newer_projects(tmp_path):
    path=tmp_path/'future.s5faceproj'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('project.json',json.dumps({'schemaVersion':900}))
    with pytest.raises(ValueError,match='Versione'):
        Project.load(path)


def test_missing_assets_prevent_save(tmp_path):
    p=template()
    p.elements.append(Element(kind='image',asset='assets/'+'a'*24+'.png'))
    with pytest.raises(ValueError,match='risorsa mancante'):
        p.save(tmp_path/'broken.s5faceproj')


@pytest.mark.parametrize('name',['Digitale','Analogico','Salute'])
def test_templates_fit_and_extreme_preview(name):
    p=template(name)
    assert not p.validate()
    assert not layout_errors(p)
    for values in SCENARIOS.values():
        im=render(p,values)
        assert im.size==(480,480)
        assert im.getpixel((0,0))[3]==0
        assert im.getpixel((240,240))[3]==255


@pytest.mark.skipif(not (ROOT/'S5_Custom_digital_original.mwz').exists(),reason='Campione originale non incluso nella distribuzione.')
def test_original_package_is_intact_and_ids_agree():
    result=inspect_mwz(ROOT/'S5_Custom_digital_original.mwz')
    assert result['sha256']=='33fb3a1dfc162b3121f69ed0be66bb97b90f156ea3bda6dd398437ca0d5f9f55'
    assert result['zipCrc']=='passed'
    assert result['binaryId']=='120917403994'
    assert not result['hardwareVerified']
    assert any('Regione' in w for w in result['warnings'])


@pytest.mark.skipif(not (ROOT/'S5_Custom_digital_original.mwz').exists(),reason='Campione originale non incluso nella distribuzione.')
def test_mwz_rejects_conflicting_id(tmp_path):
    original=ROOT/'S5_Custom_digital_original.mwz'
    path=tmp_path/'conflict.mwz'
    with zipfile.ZipFile(original) as src,zipfile.ZipFile(path,'w') as dst:
        for name in src.namelist():
            data=src.read(name)
            if name=='description.xml':
                data=data.replace(b'120917403994',b'120917403995')
            dst.writestr(name,data)
    with pytest.raises(ValueError,match='ID del binario'):
        inspect_mwz(path)


def test_native_sources_do_not_flatten_simulated_numbers(tmp_path):
    p=template('Salute')
    source=generate_fprj(p,tmp_path)
    import xml.etree.ElementTree as ET
    root=ET.parse(source.project_path).getroot()
    widgets=root.find('Screen').findall('Widget')
    sources=[w.get('Value_Src') for w in widgets if w.get('Shape')=='32']
    assert sources==['0811','1011','1812','1012','0822','0821']
    assert root.get('DeviceType')=='562'
    for w in widgets:
        if w.get('Shape')=='32':
            bitmaps=w.get('BitmapList').split('|')
            assert len(bitmaps)==12 and bitmaps[10].endswith('_minus.png') and bitmaps[11].endswith('_dot.png')


def test_corrupt_binary_offsets_rejected(tmp_path):
    data=bytearray(512)
    data[:4]=b'\x5a\xa5\x34\x12'
    data[40:49]=b'555555555'
    data[28]=1
    struct.pack_into('<I',data,16,0x800)
    struct.pack_into('<I',data,180,256)
    struct.pack_into('<II',data,176,1,9999)
    with pytest.raises(ValueError,match='offset'):
        inspect_binary(bytes(data))


@pytest.mark.integration
@pytest.mark.parametrize('name',['Digitale','Analogico','Salute','AOD'])
def test_real_s5_compilation(tmp_path,name):
    compiler=ROOT/'tools/easyface-4.23/Compiler.exe'
    if not compiler.exists():
        pytest.skip('Toolchain locale non installata.')
    p=template('Digitale' if name=='AOD' else name)
    p.elements=[e for e in p.elements if not e.aod]
    p.aod_enabled=False
    if name=='AOD':
        p.aod_enabled=True
        p.elements.append(Element(kind='clock',name='Ora AOD',aod=True,x=95,y=190,width=290,height=75,size=64))
    folder=build(p,compiler,tmp_path)
    report=json.loads((folder/'build-report.json').read_text(encoding='utf-8'))
    data=(folder/'resource.bin').read_bytes()
    assert inspect_binary(data)['faceId']==p.face_id
    assert report['compiler']['declaresS5']
    assert report['localMwz']['available']
    package=folder/report['templatePackage']['filename']
    checked=inspect_mwz(package)
    assert checked['zipCrc']=='passed'
    assert checked['capabilityCheckAvailable']
    assert not checked['hardwareVerified']
    assert checked['metadata']['deviceRegion']=='international'
    assert checked['metadata']['pkgName']==p.face_id
    with zipfile.ZipFile(package) as z:
        assert z.read('resource.bin')==data
        assert {'capability.json','hashCode','uidmap.map'} <= set(z.namelist())
        for preview in ('preview/preview.png','preview/market-preview.png'):
            with Image.open(BytesIO(z.read(preview))) as im:
                im.load()
                assert im.size==(480,480)
        assert 's5studio-test.json' not in z.namelist()
        assert 'preview/aod-preview.png' in z.namelist()
    assert (folder/'sorgenti-easyface/quadrante.fprj').exists()
    assert not list(folder.glob('*.info'))
    # Every numeric binding requested by the user is still dynamic in the binary.
    assert report['binary']['widgets']
    if name=='AOD':
        assert report['binary']['screenCount']==2
    restored=Project.load(next(folder.glob('*.s5faceproj')))
    assert restored.metadata()==p.metadata()


def test_assign_id_is_narrowly_scoped():
    data=bytearray(512)
    data[:4]=b'\x5a\xa5\x34\x12'
    data[40:49]=b'555555555'
    data[28]=1
    struct.pack_into('<I',data,16,0x800)
    struct.pack_into('<I',data,180,256)
    with pytest.raises(ValueError,match='Campo ID inatteso'):
        assign_binary_id(bytes(data),'666666666')
