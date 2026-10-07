"""Deterministic ZIP surgery: only the compiled payload and preview images may change.

Structural signatures here are local fingerprints, not Xiaomi cryptographic signatures.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib

from PIL import Image
from .model import archive_members
from .native import MAGIC, inspect_binary, sha256, compiler_probe

WORKING_TEMPLATE_SHA256='5c7a3bb0c81762e7bb0749fd1b1cd941e0578d8e0eec0d567b37c44dd6695627'


def resolve_template(path: Path | None=None) -> Path:
    if path is not None:
        return Path(path).resolve()
    from .paths import resource_root
    root=resource_root()
    path=root/'quadrante_funzionante.zip'
    if not path.is_file() or sha256(path.read_bytes())!=WORKING_TEMPLATE_SHA256:
        raise ValueError('Template quadrante_funzionante.zip mancante o modificato. Ripristina il file collaudato; nessun packaging ipotetico viene usato.')
    return path


def preview_member(name: str) -> bool:
    return (name.startswith(('preview/','resources/_preview/')) or name in {'preview.png','aod-preview.png'}) and Path(name).suffix.lower() in {'.png','.webp','.jpg','.jpeg'}


def is_aod_preview(name: str) -> bool:
    return 'aod' in name.lower() or '息屏' in name


def entry_metadata(info: zipfile.ZipInfo) -> dict:
    return {'name':info.filename,'directory':info.is_dir(),'compression':info.compress_type,
            'dateTime':list(info.date_time),'createSystem':info.create_system,
            'createVersion':info.create_version,'extractVersion':info.extract_version,
            'flags':info.flag_bits,'externalAttributes':info.external_attr,
            'internalAttributes':info.internal_attr,'extra':base64.b64encode(info.extra).decode(),
            'comment':base64.b64encode(info.comment).decode()}


def local_records(z: zipfile.ZipFile, raw: bytes) -> dict[str,bytes]:
    ordered=sorted(z.infolist(),key=lambda i:i.header_offset)
    ends=[i.header_offset for i in ordered[1:]]+[z.start_dir]
    return {i.filename:raw[i.header_offset:end] for i,end in zip(ordered,ends)}


def _surgery_bytes(template: Path, replacements: dict[str,bytes]) -> bytes:
    """Retain untouched local records verbatim, including compressed bytes/descriptors.

    Standard single-volume ZIP only; refuse ZIP64/unknown encodings rather than
    silently normalize the vendor's headers. Central-directory offsets/CRCs and
    payload lengths are the only header fields rewritten.
    """
    raw=template.read_bytes()
    with zipfile.ZipFile(BytesIO(raw)) as z:
        records=local_records(z,raw)
        ordered=sorted(z.infolist(),key=lambda i:i.header_offset)
        result=bytearray(raw[:ordered[0].header_offset])
        offsets={}
        updates={}
        for info in ordered:
            record=records[info.filename]
            offsets[info.filename]=len(result)
            if info.filename not in replacements:
                result.extend(record)
                continue
            if record[:4]!=b'PK\x03\x04' or info.compress_type not in {zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED}:
                raise ValueError('Compressione/header template non supportati: '+info.filename)
            name_len,extra_len=struct.unpack_from('<HH',record,26)
            prefix_len=30+name_len+extra_len
            data=replacements[info.filename]
            if info.compress_type==zipfile.ZIP_DEFLATED:
                compressor=zlib.compressobj(level=6,wbits=-15)
                compressed=compressor.compress(data)+compressor.flush()
            else:
                compressed=data
            crc=zlib.crc32(data)&0xffffffff
            sizes=(crc,len(compressed),len(data))
            header=bytearray(record[:prefix_len])
            if info.flag_bits&8:
                # Keep the original zero/nonzero convention for descriptor ZIPs.
                old=struct.unpack_from('<III',header,14)
                struct.pack_into('<III',header,14,*(new if prior else 0 for prior,new in zip(old,sizes)))
            else:
                struct.pack_into('<III',header,14,*sizes)
            tail=record[prefix_len+info.compress_size:]
            if info.flag_bits&8:
                signed=tail.startswith(b'PK\x07\x08')
                length=16 if signed else 12
                if len(tail)<length:
                    raise ValueError('Data descriptor del template troncato.')
                tail=(b'PK\x07\x08' if signed else b'')+struct.pack('<III',*sizes)+tail[length:]
            result.extend(header+compressed+tail)
            updates[info.filename]=sizes
        start_dir=len(result)
        central=bytearray()
        cursor=z.start_dir
        for info in z.infolist():
            if raw[cursor:cursor+4]!=b'PK\x01\x02':
                raise ValueError('Directory ZIP non standard.')
            lengths=struct.unpack_from('<HHH',raw,cursor+28)
            length=46+sum(lengths)
            entry=bytearray(raw[cursor:cursor+length])
            if len(entry)!=length or 0xffffffff in struct.unpack_from('<III',entry,16)[1:] or struct.unpack_from('<I',entry,42)[0]==0xffffffff:
                raise ValueError('ZIP64 non supportato per chirurgia template.')
            if info.filename in updates:
                struct.pack_into('<III',entry,16,*updates[info.filename])
            struct.pack_into('<I',entry,42,offsets[info.filename])
            central.extend(entry)
            cursor+=length
        footer=bytearray(raw[cursor:])
        if footer[:4]!=b'PK\x05\x06' or len(footer)!=22+len(z.comment) or struct.unpack_from('<HH',footer,4)!=(0,0):
            raise ValueError('Fine ZIP non standard / multivolume non supportata.')
        if struct.unpack_from('<HH',footer,8)!=(len(z.infolist()),len(z.infolist())):
            raise ValueError('Conteggio directory ZIP incoerente.')
        struct.pack_into('<II',footer,12,len(central),start_dir)
        return bytes(result+central+footer)


def template_profile(path: Path) -> dict:
    path=Path(path)
    with zipfile.ZipFile(path) as z:
        members=archive_members(z)
        records=local_records(z,path.read_bytes())
        required={'resource.bin','capability.json','description.xml','resources/manifest.xml','preview/preview.png'}
        if required-set(members):
            raise ValueError('Template incompleto: '+', '.join(sorted(required-set(members))))
        description=ET.fromstring(z.read('description.xml'))
        metadata={e.tag:e.text for e in description}
        manifest=ET.fromstring(z.read('resources/manifest.xml'))
        if description.tag!='watch' or metadata.get('deviceType')!='P62' or metadata.get('size')!='480x480':
            raise ValueError('Il template non dichiara S5 P62 / 480x480.')
        face_id=metadata.get('pkgName','')
        if not re.fullmatch(r'[1-9][0-9]{8,11}',face_id):
            raise ValueError('ID template non supportato (9–12 cifre).')
        if manifest.tag!='Watchface' or manifest.get('id')!=face_id or manifest.get('width')!='480' or manifest.get('height')!='480':
            raise ValueError('Manifest e descrizione del template non sono coerenti.')
        binary=z.read('resource.bin')
        if len(binary)<256 or binary[:4]!=MAGIC or binary[40:104].split(b'\0',1)[0]!=face_id.encode():
            raise ValueError('ID/header del binario template incoerente.')
        capabilities=json.loads(z.read('capability.json'))
        if not isinstance(capabilities,list) or not capabilities or any(not isinstance(c,dict) or not {'name','type','value'}<=c.keys() for c in capabilities):
            raise ValueError('Capacità del template non riconosciute.')
        entries=[]
        for info in members.values():
            data=z.read(info)
            mutable=info.filename=='resource.bin' or preview_member(info.filename)
            item={**entry_metadata(info),'mutable':mutable}
            if not mutable:
                item['sha256']=sha256(data)
                item['localRecordSha256']=sha256(records[info.filename])
            elif preview_member(info.filename):
                with Image.open(BytesIO(data)) as im:
                    im.load()
                    item['imageFormat']=im.format
                    item['imageSize']=list(im.size)
            entries.append(item)
        signature={'schemaVersion':1,'archiveComment':base64.b64encode(z.comment).decode(),'entries':entries}
        fingerprint=sha256(json.dumps(signature,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
        themes=[e.attrib for e in manifest.iter('Theme')]
        return {'templateSha256':sha256(path.read_bytes()),'faceId':face_id,'metadata':metadata,'themes':themes,
                'capabilities':capabilities,'signature':signature,'structuralFingerprint':fingerprint,
                'mutableMembers':[e['name'] for e in entries if e['mutable']],
                'hardwareVerified':False}


@lru_cache(maxsize=4)
def _project_defaults(path: str, modified: int, size: int) -> dict:
    profile=template_profile(Path(path))
    normal=next((t for t in profile['themes'] if t.get('type')=='normal'),{})
    return {'name':profile['metadata']['name'],'author':profile['metadata'].get('author') or '',
            'faceId':profile['faceId'],'version':profile['metadata'].get('version') or '1.0.0',
            'background':normal.get('bgColor','#000000'),
            'aodEnabled':any(t.get('type')=='AOD' for t in profile['themes']),
            'metadata':profile['metadata'],'capabilities':profile['capabilities'],
            'templateSha256':profile['templateSha256'],'structuralFingerprint':profile['structuralFingerprint'],
            'normalThemeCount':sum(t.get('type')=='normal' for t in profile['themes'])}


def default_project_values() -> dict | None:
    try:
        path=resolve_template()
    except ValueError:
        return None  # The editor still opens; export requires the pinned template.
    stat=path.stat()
    return _project_defaults(str(path),stat.st_mtime_ns,stat.st_size)


def template_identity(data: bytes, face_id: str) -> bytes:
    """Assign the template ID only to a structurally checked EasyFace payload."""
    inspect_binary(data)
    if not re.fullmatch(r'[1-9][0-9]{8,11}',face_id):
        raise ValueError('ID template non supportato.')
    result=bytearray(data)
    result[40:104]=face_id.encode().ljust(64,b'\0')
    inspect_binary(bytes(result))
    return bytes(result)


def validate_template_output(template: Path, output: Path, expected_replacements: dict[str,bytes] | None=None) -> dict:
    with zipfile.ZipFile(output) as z:
        if 's5studio-schema.json' in z.namelist():
            from .semantic_package import validate_package
            return validate_package(template,output,expected_replacements)
        # Reject the old partial graft: native themes and editor metadata did
        # not describe the same watchface even when all fixed records matched.
        binary=inspect_binary(z.read('resource.bin'))
        if binary['directoryStride']==176:
            themes=ET.fromstring(z.read('resources/manifest.xml')).findall('Theme')
            if len(themes)!=binary['screenCount'] or any(t.get('name')!=s['title'] for t,s in zip(themes,binary['screens'])):
                raise ValueError('Metadati del template obsoleti: temi del manifest diversi dal binario.')
    base=template_profile(template)
    actual=template_profile(output)
    if actual['structuralFingerprint']!=base['structuralFingerprint']:
        raise ValueError('Firma strutturale diversa: ordine/nomi, attributi ZIP, metadati o file preservati alterati.')
    binary=None
    with zipfile.ZipFile(output) as z:
        binary=inspect_binary(z.read('resource.bin'))
        if binary['faceId']!=base['faceId']:
            raise ValueError('ID binario non corrispondente al template.')
        if expected_replacements is not None:
            if set(expected_replacements)!=set(base['mutableMembers']):
                raise ValueError('Le sostituzioni devono corrispondere esattamente ai file modificabili del template.')
            for name,data in expected_replacements.items():
                if z.read(name)!=data:
                    raise ValueError('Sostituzione non corrispondente: '+name)
    return {'status':'passed','scope':'CRC, struttura ZIP e hash di tutti i file preservati; ID e binario EasyFace; formati e dimensioni preview.',
            'templateSha256':base['templateSha256'],'outputSha256':actual['templateSha256'],
            'structuralFingerprint':base['structuralFingerprint'],'entries':len(base['signature']['entries']),
            'preservedFiles':sum(not e['mutable'] and not e['directory'] for e in base['signature']['entries']),
            'mutableMembers':base['mutableMembers'],'binary':binary,'hardwareVerified':False,
            'warnings':[
                'Identità originale del template mantenuta: può sostituire il quadrante originale nello stesso slot.',
                'capability.json conservato byte per byte: non prova che la maschera descriva il nuovo payload.',
                'hashCode, uidmap.map, manifest ed editor.config.json conservati: potrebbero riferirsi al payload originale. Integrità crittografica e coerenza semantica non certificate.',
                'Stili e risorse del template sono conservati; i WEBP di anteprima sostituiti sono statici.',
                'Accettazione nella mod e funzionamento sul firmware del pacchetto modificato restano da provare.'
            ]}


def _encode_preview(source: bytes, entry: dict) -> bytes:
    with Image.open(BytesIO(source)) as im:
        im.load()
        if im.size!=(480,480):
            raise ValueError('Le preview sorgenti devono essere 480x480.')
        im=im.convert('RGBA').resize(tuple(entry['imageSize']),Image.Resampling.LANCZOS)
        fmt=entry['imageFormat']
        if fmt=='JPEG':
            im=im.convert('RGB')
        out=BytesIO()
        im.save(out,format=fmt,**({'lossless':True} if fmt=='WEBP' else {}))
        return out.getvalue()


def apply_template(template: Path, data: bytes, preview: bytes, output: Path, aod_preview: bytes | None=None, *, variant_previews: list[bytes] | None=None) -> dict:
    template=Path(template).resolve()
    output=Path(output).resolve()
    if template==output or output.exists():
        raise ValueError('Scegli un output nuovo: il template e i file esistenti non vengono sovrascritti.')
    profile=template_profile(template)  # Validate before any output is created.
    data=template_identity(data,profile['faceId'])
    if aod_preview is None:
        buf=BytesIO()
        Image.new('RGB',(480,480),'black').save(buf,format='PNG')
        aod_preview=buf.getvalue()
    replacements={'resource.bin':data}
    for entry in profile['signature']['entries']:
        if preview_member(entry['name']):
            source=aod_preview if is_aod_preview(entry['name']) else preview
            match=re.search(r'(?:style[_-]?|Theme|样式)([1-5])',entry['name'],re.I)
            if variant_previews and match and not is_aod_preview(entry['name']):
                source=variant_previews[min(int(match[1])-1,len(variant_previews)-1)]
            replacements[entry['name']]=_encode_preview(source,entry)
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix='.template-',suffix='.zip',dir=output.parent)
    os.close(fd)
    temporary=Path(temporary)
    try:
        temporary.write_bytes(_surgery_bytes(template,replacements))
        report=validate_template_output(template,temporary,replacements)
        # Python 3.13 makes temporary files private on Windows. Copy to inherit
        # the destination ACL; then validate the public file before returning.
        with output.open('xb') as target:
            target.write(temporary.read_bytes())
        try:
            validate_template_output(template,output,replacements)
        except Exception:
            output.unlink()
            raise
        return {**report,'output':str(output),'packaging':'template-surgery'}
    finally:
        temporary.unlink(missing_ok=True)


def _stage_fprj(path: Path, destination: Path) -> tuple[Path,bytes,bytes | None]:
    """Copy only FPRJ/images/AOD; never pass the user's source tree to the compiler."""
    root=ET.fromstring(path.read_bytes())
    screen=root.find('Screen')
    if root.tag!='FaceProject' or root.get('DeviceType')!='562' or screen is None or screen.get('Width')!='480' or screen.get('Height')!='480':
        raise ValueError('Il progetto FPRJ deve dichiarare target S5 562 e canvas 480x480.')
    thumbnail=screen.get('Bitmap','')
    if not thumbnail or Path(thumbnail).name!=thumbnail or '\\' in thumbnail or ':' in thumbnail:
        raise ValueError('Screen Bitmap deve essere un file nella cartella images del progetto.')
    destination.mkdir(parents=True)
    target=destination/path.name
    root.set('Id','167210065')
    ET.ElementTree(root).write(target,encoding='utf-8',xml_declaration=True)
    for other in sorted(path.parent.glob('*.fprj')):
        if other.resolve()==path.resolve():continue
        extra=ET.fromstring(other.read_bytes())
        extra_screen=extra.find('Screen')
        if extra.tag!='FaceProject' or extra.get('DeviceType')!='562' or extra_screen is None or extra_screen.get('Width')!='480' or extra_screen.get('Height')!='480':
            raise ValueError('Variante FPRJ con target/geometria non validi.')
        extra.set('Id','167210065')
        ET.ElementTree(extra).write(destination/other.name,encoding='utf-8',xml_declaration=True)
    (destination/'output').mkdir()
    images=path.parent/'images'
    if not images.is_dir() or images.is_symlink():
        raise ValueError('Cartella images mancante o non supportata.')
    total=0
    count=0
    for asset in images.rglob('*'):
        if asset.is_symlink():
            raise ValueError('Link simbolici non ammessi nelle risorse FPRJ.')
        if not asset.is_file():
            continue
        count+=1
        total+=asset.stat().st_size
        if total>128*1024*1024 or count>2000:
            raise ValueError('Risorse FPRJ oltre il limite 128 MB / 2000 file.')
        out=destination/'images'/asset.relative_to(images)
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(asset,out)
    preview=(destination/'images'/thumbnail).read_bytes()
    aod_preview=None
    aod=path.parent/'AOD'
    if aod.exists():
        if aod.is_symlink():
            raise ValueError('AOD con link simbolico non supportato.')
        projects=list(aod.glob('*.fprj'))
        if len(projects)!=1:
            raise ValueError('La cartella AOD deve contenere un solo progetto FPRJ.')
        if (aod/'AOD').exists():
            raise ValueError('AOD annidato non supportato.')
        _,aod_preview,_=_stage_fprj(projects[0],destination/'AOD')
    return target,preview,aod_preview


def compile_and_apply_template(project: Path, template: Path, output_dir: Path, compiler: Path) -> Path:
    from .model import Project
    from .native import build
    project=Path(project).resolve()
    template=Path(template).resolve()
    profile=template_profile(template)
    if project.suffix.lower()=='.s5faceproj':
        return build(Project.load(project),compiler,output_dir,template_path=template)
    if project.suffix.lower()!='.fprj':
        raise ValueError('Usa un progetto .fprj o .s5faceproj.')
    reproduction=project.parent/'studio-export.json'
    if reproduction.exists():
        spec=json.loads(reproduction.read_text(encoding='utf8'))
        for name,digest in spec['files'].items():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Percorso sorgente Studio non valido.')
            if sha256((project.parent/relative).read_bytes())!=digest:raise ValueError('Sorgenti Studio modificati: apri il .s5faceproj per ricompilare il grafo completo.')
        full=build(Project.load(project.parent/'studio.s5faceproj'),compiler,output_dir,template_path=template)
        result=next(full.glob('*_TEMPLATE.zip'))
        shutil.copyfile(full/'build-report.json',result.with_suffix('.report.json'))
        return result
    tool=compiler_probe(compiler)
    output_dir=Path(output_dir).resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    filename=project.stem+'_TEMPLATE.zip'
    output=output_dir/filename
    if output.exists():
        raise ValueError('Output già presente: scegli una cartella nuova.')
    with tempfile.TemporaryDirectory(prefix='.s5-fprj-',dir=output_dir) as work:
        work=Path(work)
        staged,preview,aod_preview=_stage_fprj(project,work/'source')
        runtime=work/'runtime'
        runtime.mkdir()
        shutil.copyfile(compiler,runtime/'Compiler.exe')
        db=Path(compiler).parent/'DeviceInfo.db'
        if db.exists():
            shutil.copyfile(db,runtime/db.name)
        compiled=work/'compiled'
        compiled.mkdir()
        env=dict(os.environ)
        env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
        result=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(staged),str(compiled),'quadrante.face','167210065'],
                              cwd=runtime,env=env,capture_output=True,stdin=subprocess.DEVNULL,timeout=90,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log=(result.stdout+result.stderr).decode('utf-8',errors='replace')
        raw=compiled/'quadrante.face'
        if result.returncode or not raw.exists() or 'No Errors' not in log or 'Watch: MiWatchS5' not in log:
            raise ValueError('Compilazione FPRJ fallita:\n'+log[-1800:])
        data=raw.read_bytes()
        binary=inspect_binary(data)
        if binary['screenCount']!=len(list((work/'source').glob('*.fprj')))+int(aod_preview is not None):
            raise ValueError('Numero schermate compilate diverso dal progetto FPRJ.')
        expected=[]
        for fprj in (work/'source').rglob('*.fprj'):
            for widget in ET.parse(fprj).getroot().iter('Widget'):
                if widget.get('Shape') in ('31','32'):
                    expected.append(widget.get('Value_Src',widget.get('Index_Src','')).upper())
                elif widget.get('Shape')=='27':
                    expected+=['0811','1011']
                    if widget.get('SecondHand_Image'):expected.append('1811')
        got=[w['source'] for s in binary['screens'] for w in s['widgets']]
        if sorted(expected)!=sorted(got):
            raise ValueError('Binding del binario diversi dal progetto FPRJ.')
        from .native_graph import compose
        from .editable import preview_blob
        from .semantic_package import package
        data=template_identity(data,profile['faceId'])
        paths=[staged]+[f for f in (work/'source').glob('*.fprj') if f!=staged]
        p=Project(name=ET.parse(staged).getroot().find('Screen').get('Title','S5 Studio'),aod_enabled=aod_preview is not None,variants=[])
        png_previews=[];native_previews=[preview_blob(data)]
        single_dir=work/'single';single_dir.mkdir();(single_dir/'output').mkdir();shutil.copytree(work/'source/images',single_dir/'images')
        for n,f in enumerate(paths):
            screen=ET.parse(f).getroot().find('Screen');png=(work/'source/images'/screen.get('Bitmap')).read_bytes();png_previews.append(png)
            el=p.add_image(work/'source/images'/screen.get('Bitmap'));p.elements.remove(el)
            p.variants.append({'id':f'style{n}','name':p.name if len(paths)==1 else f'Stile {n+1}','accent':'#6ce5c1','background':'','imageAsset':el.asset,'overrides':{}})
            if n:
                source=single_dir/'single.fprj';shutil.copyfile(f,source)
                extra=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source),str(compiled),'preview.face','167210065'],cwd=runtime,env=env,capture_output=True,stdin=subprocess.DEVNULL,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if extra.returncode or b'No Errors' not in extra.stdout+extra.stderr:raise ValueError('Compilazione preview FPRJ fallita.')
                native_previews.append(preview_blob((compiled/'preview.face').read_bytes()))
        if aod_preview is not None:
            asset=work/'aod-preview.png';asset.write_bytes(aod_preview);p.add_image(asset,background=True,aod=True)
        with zipfile.ZipFile(template) as z:reference=z.read('resource.bin')
        data=template_identity(data,p.face_id)
        aod_blob=None
        if aod_preview is not None:
            aod_single=work/'aod-single';aod_single.mkdir();(aod_single/'output').mkdir()
            source=aod_single/'single.fprj';shutil.copyfile(next((work/'source/AOD').glob('*.fprj')),source)
            shutil.copytree(work/'source/AOD/images',aod_single/'images')
            extra=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source),str(compiled),'aod-preview.face','167210065'],cwd=runtime,env=env,capture_output=True,stdin=subprocess.DEVNULL,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if extra.returncode or b'No Errors' not in extra.stdout+extra.stderr:raise ValueError('Compilazione preview AOD FPRJ fallita.')
            aod_blob=preview_blob((compiled/'aod-preview.face').read_bytes())
        data,generated=compose(data,p,reference,work/'source',native_previews,{}, {},source_paths=paths,aod_preview=aod_blob)
        report=package(template,data,png_previews[0],output,aod_preview,png_previews,p,generated)
        report['compiler']=tool
        report['sourceProject']=str(project)
        report['sourceSha256']=sha256(project.read_bytes())
        output.with_suffix('.report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        output.with_suffix('.compiler.log').write_text(log,encoding='utf-8')
    return output
