"""Read-only inventory: provenance is metadata plus the user's correction."""
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.native import inspect_binary

folder=ROOT/'ORIGINALE_quadrante'
out=ROOT/'docs/folder-analysis';out.mkdir(exist_ok=True)
entries=[]
for path in sorted(folder.rglob('*')):
    if not path.is_file():continue
    data=path.read_bytes()
    entry={'path':path.relative_to(folder).as_posix(),'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if path.suffix.lower() in ('.png','.webp','.jpg'):
        with Image.open(BytesIO(data)) as im:entry['image']={'format':im.format,'size':list(im.size)}
    entries.append(entry)
description={e.tag:e.text for e in ET.parse(folder/'description.xml').getroot()}
manifest=ET.parse(folder/'resources/manifest.xml').getroot()
binary=(folder/'resource.bin').read_bytes()
capabilities=json.loads((folder/'capability.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(ROOT/'quadrante_funzionante.zip') as z:
    reference=ET.fromstring(z.read('resources/manifest.xml'))
    resources={e.get('name'):e for e in reference.find('Resources')}
    suit={e.tag:e.text for e in ET.fromstring(z.read('description.xml'))}
    suitcaps=json.loads(z.read('capability.json'))
    pointers=[e.attrib for e in reference.find('Resources') if e.tag=='DataItemPointer']
    binding=inspect_binary(z.read('resource.bin'))
    normal=next(t for t in reference.findall('Theme') if t.get('type')=='normal')
    hand_layouts=[e.attrib for e in normal if e.get('ref','').startswith('@Pointer')]
    hand_images=[]
    for layout in hand_layouts:
        pointer=resources[layout['ref'][1:]]
        item={**pointer.attrib,'layout':layout}
        item['images']=[resources[value[1:]].attrib for value in pointer.attrib.values() if value.startswith('@') and value[1:] in resources and resources[value[1:]].tag=='Image']
        hand_images.append(item)
def encoded_path(path):
    return ''.join(f'#U{ord(c):04x}' if ord(c)>127 else c for c in path)

missing=sorted({e.get('src') for e in manifest.iter() if e.get('src') and not (folder/'resources'/e.get('src')).is_file()})
encoded_matches={p:encoded_path(p) for p in missing if (folder/'resources'/encoded_path(p)).is_file()}
report={'folder':folder.name,'description':description,'provenance':'Quadrante creator HaloX78; non originale Xiaomi, come confermato dall’utente.',
        'fileCount':len(entries),'totalBytes':sum(e['size'] for e in entries),'entries':entries,'capabilities':capabilities,
        'manifestRoot':manifest.attrib,'manifestTagCounts':dict(Counter(e.tag for e in manifest.iter())),
        'missingManifestImages':missing,'encodedFilenameMatches':encoded_matches,'actuallyMissingImages':[p for p in missing if p not in encoded_matches],
        'binary':{'size':len(binary),'headerProtocol':hex(struct.unpack_from('<I',binary,16)[0]),'screens':binary[28],
                  'id':binary[40:104].split(b'\0',1)[0].decode()},
        'suitAndTie':{'description':suit,'capabilities':suitcaps,'binary':binding,'pointerResources':pointers,'firstNormalHands':hand_images},
        'hardwareEvidence':'Il nome del folder non dimostra provenienza OEM. Nessuna compilazione né installazione di questo folder effettuata.'}
(out/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Analisi del quadrante HaloX78',report['provenance'],
       f'\nNome: {description.get("name")}; autore: {description.get("author")}; ID: {description.get("pkgName")}.',
       f'\n{len(entries)} file, {report["totalBytes"]} byte. Nessuno slot modificabile e nessun tema AOD nel manifest. Il protocollo del binario è 0x800; Suit and tie usa 0x903 e directory da 176 byte.',
       '\nGerarchia completa:\n```text',*[e['path'] for e in entries],'```',
       '\n| Percorso | Byte | SHA-256 |','| --- | ---: | --- |',
       *[f'| {e["path"]} | {e["size"]} | `{e["sha256"]}` |' for e in entries],
       '\nMetadati, capacità, immagini e risorse Pointer analogiche di Suit and tie: `analysis.json`.']
(out/'inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'folderFiles':len(entries),'author':description.get('author'),'missingImages':report['missingManifestImages'],
                  'suitPointers':len(pointers),'firstNormalHandLayers':len(hand_layouts)},ensure_ascii=False))
