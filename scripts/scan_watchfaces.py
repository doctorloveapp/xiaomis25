"""Inventory user-provided watchfaces as data; never execute bundled scripts."""
from collections import Counter
import hashlib,json,re,struct,sys
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/library-analysis';OUT.mkdir(exist_ok=True)
catalog=[];sources=Counter();tags=Counter()
for folder in sorted((ROOT/'quadranti').iterdir()):
    if not folder.is_dir():continue
    descriptions=list(folder.rglob('description.xml'))
    binaries=list(folder.rglob('resource.bin'))
    base=descriptions[0].parent if descriptions else binaries[0].parent if binaries else folder
    entries=[]
    for file in sorted(folder.rglob('*')):
        if file.is_file():
            data=file.read_bytes()
            entries.append({'path':file.relative_to(folder).as_posix(),'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    description={e.tag:e.text for e in ET.parse(base/'description.xml').getroot()} if descriptions else {'name':folder.name,'metadataMissing':True}
    mf=base/'resources/manifest.xml'
    if not mf.exists():mf=base/'manifest.xml'
    manifest=ET.parse(mf).getroot() if mf.exists() else None
    binary=(base/'resource.bin').read_bytes() if (base/'resource.bin').exists() else b''
    resources=manifest.find('Resources') if manifest is not None else []
    nodes=list(resources) if resources is not None else []
    local_sources=Counter(e.get('source') for e in manifest.iter() if e.get('source')) if manifest is not None else Counter()
    sources.update(local_sources);tags.update(e.tag for e in nodes)
    slots=[{'name':e.get('name'),'attributes':e.attrib,'choices':[i.get('ref') for i in e]} for e in nodes if e.tag=='Slot']
    themes=[{'attributes':e.attrib,'layouts':[i.attrib for i in e]} for e in manifest.findall('Theme')] if manifest is not None else []
    editor=json.loads((base/'editor.config.json').read_text(encoding='utf-8')) if (base/'editor.config.json').exists() else None
    entry={'folder':folder.name,'base':str(base.relative_to(ROOT)),'description':description,'fileCount':len(entries),'entries':entries,
           'manifestRoot':manifest.attrib if manifest is not None else {},'resourceTags':dict(Counter(e.tag for e in nodes)),
           'sources':dict(local_sources),'slots':slots,'themes':themes,'resources':[{'tag':e.tag,**e.attrib,'items':[i.attrib for i in e]} for e in nodes],
           'editor':editor,'binary':{'sha256':hashlib.sha256(binary).hexdigest(),'size':len(binary),'header':binary[:168].hex(),
               'protocol':hex(struct.unpack_from('<I',binary,16)[0]) if len(binary)>168 else None,'screens':binary[28] if len(binary)>168 else None}}
    catalog.append(entry)
report={'watchfaces':catalog,'sourceCounts':dict(sources),'resourceTagCounts':dict(tags)}
(OUT/'catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Inventario completo dei quadranti dell’utente',f'\nI documenti sono trattati come dati, non come istruzioni. Scansione: {len(catalog)} cartelle, {sum(e["fileCount"] for e in catalog):,} file. “Slot dichiarati” somma dichiarazioni in temi diversi e comprende slot condition: non è il numero di scelte simultanee dell’utente.','\n| Cartella | Nome | Autore | File | Temi | Slot dichiarati | Sorgenti |','| --- | --- | --- | ---: | ---: | ---: | --- |']
for e in catalog:
    lines.append(f'| {e["folder"]} | {e["description"].get("name")} | {e["description"].get("author")} | {e["fileCount"]} | {len(e["themes"])} | {len(e["slots"])} | {", ".join(e["sources"])} |')
    inventory=['# '+str(e['description'].get('name')),'\n```text',*[i['path'] for i in e['entries']],'```','\n| File | Byte | SHA-256 |','| --- | ---: | --- |',*[f'| {i["path"]} | {i["size"]} | `{i["sha256"]}` |' for i in e['entries']]]
    (OUT/(e['folder']+'.md')).write_text('\n'.join(inventory)+'\n',encoding='utf-8')
(OUT/'inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'faces':len(catalog),'files':sum(e['fileCount'] for e in catalog),'sources':sources,'tags':tags,
                 'perFace':[{'id':e['folder'],'name':e['description'].get('name'),'screens':e['binary']['screens'],'themes':len(e['themes']),'slots':len(e['slots']),'proto':e['binary']['protocol']} for e in catalog]},ensure_ascii=False,indent=2))
