from pathlib import Path
import json
from io import BytesIO
import struct
import zipfile

import pytest
from PIL import Image
from s5studio.model import template
from s5studio.semantic_package import EDITABLE
from s5studio.native import build, inspect_binary, sha256
from s5studio.template_package import (WORKING_TEMPLATE_SHA256,template_profile,
    validate_template_output,apply_template,local_records,_surgery_bytes,
    compile_and_apply_template)

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/'quadrante_funzionante.zip'
COMPILER=ROOT/'tools/easyface-4.23/Compiler.exe'
pytestmark=pytest.mark.skipif(not REFERENCE.exists(),reason='Template locale non distribuito.')


@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
    if not COMPILER.exists():
        pytest.skip('Compilatore locale non presente.')
    folder=build(template(),COMPILER,tmp_path_factory.mktemp('compiled'))
    report=json.loads((folder/'build-report.json').read_text(encoding='utf-8'))
    return folder,folder/report['templatePackage']['filename']


def test_defaults_are_read_from_working_template():
    p=template()
    profile=template_profile(REFERENCE)
    assert sha256(REFERENCE.read_bytes())==WORKING_TEMPLATE_SHA256
    assert p.face_id!=profile['faceId']=='120917386745'
    assert len(p.face_id)==9
    assert p.name=='S5 Digitale'
    assert p.author=='S5 Studio'
    assert p.version==profile['metadata']['version']=='1.1.16'
    assert p.background=='#000000'
    assert p.aod_enabled and any(e.aod and e.kind=='clock' for e in p.elements)
    assert p.profile['templateDefaults']['capabilities']==profile['capabilities']


def test_every_fixed_record_including_compressed_bytes_is_identical(compiled):
    folder,output=compiled
    profile=template_profile(REFERENCE)
    checked=validate_template_output(REFERENCE,output)
    assert checked['status']=='passed'
    assert checked['entries']>228 and checked['preservedFiles']==187
    assert not checked['hardwareVerified']
    with zipfile.ZipFile(REFERENCE) as src,zipfile.ZipFile(output) as dst:
        assert set(src.namelist())<set(dst.namelist())
        sr=local_records(src,REFERENCE.read_bytes())
        dr=local_records(dst,output.read_bytes())
        for entry in profile['signature']['entries']:
            if not entry['mutable'] and entry['name'] not in EDITABLE:
                name=entry['name']
                assert src.read(name)==dst.read(name)
                assert sr[name]==dr[name]
        assert dst.testzip() is None
        for theme in json.loads(dst.read('editor.config.json'))['themes']:
            if theme['type']=='AOD':assert not theme.get('previewAni')
            else:assert 'preview/'+theme['previewAni'] in dst.namelist()
        assert dst.read('resource.bin')==(folder/'resource.bin').read_bytes()
        assert src.read('resource.bin')!=dst.read('resource.bin')
        assert inspect_binary(dst.read('resource.bin'))['screenCount']==2
    assert sha256(REFERENCE.read_bytes())==WORKING_TEMPLATE_SHA256


@pytest.mark.parametrize('name',['capability.json','hashCode','uidmap.map','resources/manifest.xml','editor.config.json'])
def test_validator_rejects_a_changed_preserved_file(compiled,tmp_path,name):
    _,output=compiled
    with zipfile.ZipFile(output) as z:
        data=z.read(name)
    # Keep XML/JSON parseable so this proves preservation, not only parsing.
    changed=data+b'\n'
    target=tmp_path/'tampered.zip'
    target.write_bytes(_surgery_bytes(output,{name:changed}))
    with pytest.raises(ValueError,match='protetto|modificata'):
        validate_template_output(REFERENCE,target)


def test_validator_rejects_corrupt_native_payload(compiled,tmp_path):
    _,output=compiled
    with zipfile.ZipFile(output) as z:
        data=bytearray(z.read('resource.bin'))
    table=168+4*(data[24]+data[29])
    struct.pack_into('<I',data,table+12,len(data)+64)
    target=tmp_path/'bad-payload.zip'
    target.write_bytes(_surgery_bytes(output,{'resource.bin':bytes(data)}))
    with pytest.raises(ValueError,match='offset'):
        validate_template_output(REFERENCE,target)


def test_validator_rejects_wrong_manifest_identity_even_with_updated_local_hash(compiled,tmp_path):
    import xml.etree.ElementTree as ET
    _,output=compiled
    with zipfile.ZipFile(output) as z:
        manifest=ET.fromstring(z.read('resources/manifest.xml'))
        schema=json.loads(z.read('s5studio-schema.json'))
    manifest.set('id','999999999')
    changed=ET.tostring(manifest,encoding='utf8',xml_declaration=True)
    schema['metadataHashes']['resources/manifest.xml']=sha256(changed)
    target=tmp_path/'wrong-identity.zip'
    target.write_bytes(_surgery_bytes(output,{'resources/manifest.xml':changed,
                                            's5studio-schema.json':json.dumps(schema).encode()}))
    with pytest.raises(ValueError,match='Identità/geometria'):
        validate_template_output(REFERENCE,target)


def test_validator_rejects_preview_wrong_dimensions(compiled,tmp_path):
    _,output=compiled
    image=BytesIO()
    Image.new('RGB',(320,320)).save(image,format='PNG')
    target=tmp_path/'bad-preview.zip'
    target.write_bytes(_surgery_bytes(output,{'preview/preview.png':image.getvalue()}))
    with pytest.raises(ValueError,match='protetto|modificata'):
        validate_template_output(REFERENCE,target)


def test_apply_refuses_to_overwrite_reference(compiled):
    folder,_=compiled
    with pytest.raises(ValueError,match='output nuovo'):
        apply_template(REFERENCE,(folder/'resource.bin').read_bytes(),(folder/'preview.png').read_bytes(),REFERENCE)


@pytest.mark.integration
def test_real_fprj_compile_and_template_patch(compiled,tmp_path):
    folder,_=compiled
    output=compile_and_apply_template(folder/'sorgenti-easyface/quadrante.fprj',REFERENCE,tmp_path,COMPILER)
    assert output.is_file()
    assert validate_template_output(REFERENCE,output)['status']=='passed'
    report=json.loads(output.with_suffix('.report.json').read_text(encoding='utf-8'))
    assert report['binary']['faceId']==json.loads((folder/'build-report.json').read_text(encoding='utf8'))['binary']['faceId']
    assert report['binary']['screenCount']==2
    assert sha256(REFERENCE.read_bytes())==WORKING_TEMPLATE_SHA256
