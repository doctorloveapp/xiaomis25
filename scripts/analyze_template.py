"""Read-only full inventory and reproducible comparison of the two reference ZIPs."""
from collections import Counter
from pathlib import Path
import difflib
import hashlib
from io import BytesIO
import json
import sys
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.model import archive_members
from s5studio.template_package import template_profile

OUT=ROOT/'docs/template-analysis'
OUT.mkdir(parents=True,exist_ok=True)
META=['capability.json','description.xml','resources/manifest.xml','hashCode','uidmap.map']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scan(path,label):
    with zipfile.ZipFile(path) as z:
        members=archive_members(z)
        entries=[]
        for info in members.values():
            data=z.read(info)
            entry={'name':info.filename,'directory':info.is_dir(),'size':len(data),
                   'compressedSize':info.compress_size,'compression':info.compress_type,
                   'flags':info.flag_bits,'crc32':f'{info.CRC:08x}','sha256':digest(data)}
            if Path(info.filename).suffix.lower() in {'.png','.webp','.jpg','.jpeg'}:
                with Image.open(BytesIO(data)) as im:
                    im.load()
                    entry['image']={'format':im.format,'size':list(im.size),'frames':getattr(im,'n_frames',1)}
            if info.filename in META:
                target=OUT/label/info.filename
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
            entries.append(entry)
        description={e.tag:e.text for e in ET.fromstring(z.read('description.xml'))}
        manifest=ET.fromstring(z.read('resources/manifest.xml'))
        caps={c['name']:c for c in json.loads(z.read('capability.json'))}
        hashes=z.read('hashCode').decode().split(',')
        matching={h:[e['name'] for e in entries if e['sha256']==h] for h in hashes}
        missing=sorted({e.get('src') for e in manifest.iter() if e.get('src') and 'resources/'+e.get('src') not in members})
        return {'filename':path.name,'sha256':digest(path.read_bytes()),'zipCrc':'passed',
                'entryCount':len(entries),'fileCount':sum(not e['directory'] for e in entries),
                'uncompressedSize':sum(e['size'] for e in entries),'entries':entries,
                'capabilities':caps,'description':description,'manifestRoot':manifest.attrib,
                'manifestTagCounts':dict(Counter(e.tag for e in manifest.iter())),
                'manifestMissingSrcPaths':missing,'hashCodeMatchesToFileSha256':matching,
                'binaryId':z.read('resource.bin')[40:104].split(b'\0',1)[0].decode(),
                'binaryHeader40Hex':z.read('resource.bin')[:40].hex()}


def changes(a,b):
    return {k:{'working':a.get(k),'original':b.get(k)} for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)}


working=scan(ROOT/'quadrante_funzionante.zip','working')
original=scan(ROOT/'S5_Custom_digital_original.mwz','original')
wa={e['name']:e for e in working['entries']}
oa={e['name']:e for e in original['entries']}
diff={'capabilityChanges':changes(working['capabilities'],original['capabilities']),
      'descriptionChanges':changes(working['description'],original['description']),
      'manifestRootChanges':changes(working['manifestRoot'],original['manifestRoot']),
      'workingOnly':sorted(wa.keys()-oa.keys()),'originalOnly':sorted(oa.keys()-wa.keys()),
      'commonChanged':[n for n in sorted(wa.keys()&oa.keys()) if wa[n]['sha256']!=oa[n]['sha256']],
      'commonIdentical':[n for n in sorted(wa.keys()&oa.keys()) if wa[n]['sha256']==oa[n]['sha256']]}
for name in META[:3]:
    a=(OUT/'working'/name).read_text(encoding='utf-8').splitlines(keepends=True)
    b=(OUT/'original'/name).read_text(encoding='utf-8').splitlines(keepends=True)
    target=OUT/(Path(name).name+'.diff')
    target.write_text(''.join(difflib.unified_diff(b,a,fromfile='original/'+name,tofile='working/'+name)),encoding='utf-8')
profile=template_profile(ROOT/'quadrante_funzionante.zip')
report={'working':working,'original':original,'differences':diff,'templateProfile':profile}
(OUT/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for label,archive in [('working',working),('original',original)]:
    lines=[f'# Inventario completo: {archive["filename"]}',f'\nSHA-256: `{archive["sha256"]}`; CRC: passato.',
           f'\n{archive["entryCount"]} voci, {archive["fileCount"]} file. Gerarchia completa (percorsi ZIP esatti):','\n```text']
    lines += [e['name'] for e in archive['entries']]
    lines += ['```','\n| Percorso | Byte | Byte compressi | Metodo | Flag | SHA-256 contenuto |','| --- | ---: | ---: | ---: | ---: | --- |']
    lines += [f'| {e["name"]} | {e["size"]} | {e["compressedSize"]} | {e["compression"]} | {e["flags"]} | `{e["sha256"]}` |' for e in archive['entries']]
    (OUT/f'inventory-{label}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'entries':[working['entryCount'],original['entryCount']],
                  'files':[working['fileCount'],original['fileCount']],
                  'capabilityChanges':diff['capabilityChanges'],
                  'hashMatches':working['hashCodeMatchesToFileSha256'],
                  'missingManifestImages':working['manifestMissingSrcPaths'],
                  'structuralFingerprint':profile['structuralFingerprint']},ensure_ascii=False,indent=2))
