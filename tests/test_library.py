from pathlib import Path
import hashlib,json,struct,zipfile
import pytest
from PIL import Image
from s5studio.watchface_library import library,read_tables
from s5studio.model import template
from s5studio.native import build,inspect_binary
from s5studio.template_package import validate_template_output

ROOT=Path(__file__).resolve().parents[1]

def test_every_local_folder_is_inventoried_and_hands_keep_real_pivots():
    catalog=json.loads((ROOT/'docs/library-analysis/catalog.json').read_text(encoding='utf8'))
    assert len(catalog['watchfaces'])==len([p for p in (ROOT/'quadranti').iterdir() if p.is_dir()])==39
    assert not library()['errors']
    assert len(library()['hands'])==595
    report=json.loads((ROOT/'docs/library-analysis/hands-0.8.json').read_text(encoding='utf8'))
    covered={(g['face'],name) for g in report['coverage'] for name in g['resources']}
    pointers={(f['folder'],n['name']) for f in catalog['watchfaces'] for n in f['resources'] if n['tag']=='DataItemPointer'}
    assert covered==pointers and len(pointers)==1310
    for preset in library()['hands']:
        path=ROOT/preset['assetPath']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==preset['sourceSha256']
        with Image.open(path) as image:
            assert all(0<=v<480 for v in preset['pivot'])
            assert preset['externalPivot']==any(v>=s for v,s in zip(preset['pivot'],image.size))
        by_id={p['id']:p for p in library()['hands']}
        assert all(by_id[identity]['hand']==role for role,identity in preset['setMembers'].items())
        if preset['shadow']:
            shadow=preset['shadow']
            assert hashlib.sha256((ROOT/shadow['assetPath']).read_bytes()).hexdigest()==shadow['sourceSha256']
    for face in catalog['watchfaces']:
        if not face['binary']['size']:continue
        data=(ROOT/face['base']/'resource.bin').read_bytes()
        for index in range(data[28]):read_tables(data,index)

def test_old_partial_template_graft_is_rejected():
    old=ROOT/'S5_Analogico_Varianti_TEMPLATE.zip'
    if not old.exists():
        copies=sorted((ROOT/'test_upload').glob('S5_Analogico_Varianti-*/*_TEMPLATE.zip'))
        if not copies:pytest.skip('Vecchio artefatto locale assente.')
        old=copies[-1]
    with pytest.raises(ValueError,match='obsoleti'):
        validate_template_output(ROOT/'quadrante_funzionante.zip',old)

@pytest.mark.integration
def test_every_observed_source_is_preserved_and_weather_has_real_icon_mapping(tmp_path):
    p=template('Analogico');p.aod_enabled=False;p.elements=[e for e in p.elements if not e.aod and e.kind=='analog']
    sources=list(library()['sources'])
    p.complications=[{'id':'all','name':'Tutti i dati','x':160,'y':320,'width':160,'height':120,'options':['none',*sources],'default':'weatherCurrentWeather'}]
    output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',tmp_path)
    data=(output/'resource.bin').read_bytes();info=inspect_binary(data)
    assert {s['code'] for s in library()['sources'].values()}<={w['source'] for w in info['widgets']}
    t=read_tables(data);group_uid=struct.unpack_from('<I',t[8][0][2],4)[0]
    group=next(b for uid,_,b in t[9] if uid==group_uid)
    refs=[struct.unpack_from('<I',group,48+12*n)[0] for n in range(struct.unpack_from('<H',group,40)[0])]
    weather=next(b for uid,_,b in t[7] if uid in refs and b[:2].hex().upper()=='3031')
    assert struct.unpack_from('<18i',weather,16)==(0,1,2,4,5,6,7,8,9,13,15,16,18,19,20,29,53,99)
    sleep=next(b for _,_,b in t[7] if b[:2].hex().upper()=='0828')
    distance=next(b for _,_,b in t[7] if b[:2].hex().upper()=='1821')
    assert sleep[2]>>4==1 and distance[2]>>4==2
    assert struct.unpack_from('<H',sleep,6)[0]==struct.unpack_from('<H',distance,6)[0]==1000
    assert validate_template_output(ROOT/'quadrante_funzionante.zip',next(output.glob('*_TEMPLATE.zip')))['status']=='passed'
