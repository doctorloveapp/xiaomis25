"""Original adapter for the documented EasyFace FPRJ interface.

This does not implement Xiaomi's proprietary image compression or capability masks.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw
from .model import Project, Element, SOURCES, archive_members
from .render import (render, png_bytes, static_image, digit_image, digit_metrics,
                     number_parts, font_for, rgba, analog_face, hand_image, hand_shadow_offset, layout_errors, canvas_image)

MAGIC = b"\x5a\xa5\x34\x12"
DEFAULT_COMPILER_SHA = "bfb8c3b6666b79de165884d832c69d46e5bbfa581c65c1e188cddfc4b9d6723a"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compiler_probe(path: Path) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("Compiler.exe non trovato. Seleziona EasyFace Compiler 4.23.")
    if path.stat().st_size > 100 * 1024 * 1024:
        raise ValueError("Il file del compilatore è troppo grande.")
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise ValueError("Il compilatore deve essere un eseguibile Windows.")
    if b"MiWatchS5" not in data:
        raise ValueError("Questo compilatore non dichiara MiWatchS5 al suo interno.")
    if sha256(data) != DEFAULT_COMPILER_SHA:
        raise ValueError("Versione del compilatore non verificata. Usa Compiler.exe dalla release ufficiale EasyFace 4.23.")
    return {"path": str(path), "sha256": sha256(data), "declaresS5": True,
            "interface": "Compiler -b project.fprj output name.face id"}


def inspect_binary(data: bytes) -> dict:
    """Check EasyFace 88-byte and observed Suit editable 176-byte directories.

    This validates bounds and native references; it is not firmware certification.
    """
    if len(data) < 256 or data[:4] != MAGIC:
        raise ValueError("Header del binario non riconosciuto.")
    face_id = data[40:104].split(b"\0",1)[0].decode("ascii", errors="strict")
    if not re.fullmatch(r"\d{9,12}", face_id):
        raise ValueError("ID del binario non valido.")
    def check_preview(pos):
        if pos<168 or pos+12>len(data):raise ValueError('Offset anteprima binaria non valido.')
        width,height,length=struct.unpack_from('<HHI',data,pos+4)
        if not 1<=width<=480 or not 1<=height<=480 or pos+12+length>len(data):raise ValueError('Anteprima binaria troncata o non valida.')
    preview_offset=struct.unpack_from('<I',data,32)[0]
    if preview_offset:check_preview(preview_offset)
    from .watchface_library import directory_stride,directory_bases
    entry,stride=directory_stride(data)
    table_count=12 if stride==176 else 10
    if not 1<=data[28]<=255 or entry+stride*data[28] > len(data):
        raise ValueError("Numero di schermate o directory binaria non supportati.")
    screens=[]
    for screen_index in range(data[28]):
        base=directory_bases(data)[screen_index]
        if stride==176:
            mode=struct.unpack_from('<I',data,base+172)[0]&1
            preview=struct.unpack_from('<I',data,base+4)[0]
            if not mode:check_preview(preview)
        counts=[]
        widgets=[]
        assets=[]
        references=[]
        resource_ids=set()
        slots=[]
        groups=[]
        for index in range(table_count):
            count, offset=struct.unpack_from("<II",data,base+8+index*8)
            if count>10000 or offset>len(data) or offset+count*16>len(data):
                raise ValueError(f"Schermata {screen_index}, tabella {index}: offset fuori dal binario.")
            counts.append(count)
            for row in range(count):
                uid,_,pos,length=struct.unpack_from("<IIII",data,offset+row*16)
                if uid in resource_ids:
                    raise ValueError('UID duplicato nella schermata.')
                resource_ids.add(uid)
                if pos>len(data) or length>len(data)-pos:
                    raise ValueError(f"Risorsa {uid:x}: offset fuori dal binario.")
                if index == 0:
                    if length<8:
                        raise ValueError("Elemento nativo troncato.")
                    references.append(struct.unpack_from('<I',data,pos)[0])
                if index == 7:
                    if length<12:
                        raise ValueError("Widget nativo troncato.")
                    target=struct.unpack_from('<I',data,pos+8)[0]
                    references.append(target)
                    widgets.append({"id": f"{uid:x}", "source": data[pos:pos+2].hex().upper(),
                                    "digits": data[pos+2]&15,'decimals':data[pos+2]>>4, "type":data[pos+3]>>4,"target":f"{target:x}"})
                if index==8:
                    if length<12:
                        raise ValueError('Slot nativo troncato.')
                    options=struct.unpack_from('<H',data,pos)[0]
                    trailer=pos+4+options*4
                    if not 1<=options<=64 or trailer+4>pos+length:
                        raise ValueError('Directory opzioni dello slot non valida.')
                    text_length=struct.unpack_from('<I',data,trailer)[0]
                    if 4+options*4+4+((text_length+3)//4)*4!=length:raise ValueError('Nome gruppo slot troncato.')
                    choices=list(struct.unpack_from('<'+'I'*options,data,pos+4))
                    references+=choices
                    slots.append({'id':f'{uid:x}','choices':[f'{v:x}' for v in choices]})
                if index==9:
                    groups.append(data[pos:pos+length])
                if index in (2,3):
                    if length<12:
                        raise ValueError("Risorsa immagine troncata.")
                    w,h=struct.unpack_from("<HH",data,pos+4)
                    if not 1<=w<=480 or not 1<=h<=480:
                        raise ValueError("Dimensione di una risorsa immagine non valida.")
                    assets.append({"id":f"{uid:x}","width":w,"height":h,"array":index==3})
        for group in groups:
            if len(group)<52:raise ValueError('Gruppo modificabile troncato.')
            children=struct.unpack_from('<H',group,40)[0]
            if 44+12*children+8!=len(group):raise ValueError('Struttura figli del gruppo modificabile non valida.')
            references.extend(struct.unpack_from('<I',group,48+n*12)[0] for n in range(children))
            references.extend(struct.unpack_from('<I',group,pos)[0] for pos in (4,36,44+12*children))
        references=[target for target in references if target!=0xffffffff]
        if any(target not in resource_ids for target in references):
            raise ValueError("Il binario contiene riferimenti a risorse inesistenti.")
        screens.append({"index":screen_index,"sectionCounts":counts,"widgets":widgets,"images":assets,'slots':slots,
                        'title':data[base+104:base+168].split(b'\0',1)[0].decode('utf-8') if stride==176 else '',
                        'aod':bool(struct.unpack_from('<I',data,base+172)[0]&1) if stride==176 else screen_index==1 and bool(data[30]&4)})
    return {"faceId":face_id,"size":len(data),"sha256":sha256(data),
            "screenCount":data[28],'directoryStride':stride,'nativeSlots':sum(len(s['slots']) for s in screens),"sectionCounts":screens[0]['sectionCounts'],
            "widgets":screens[0]['widgets'],"images":screens[0]['images'],"screens":screens,
            "scope":"Header, limiti delle tabelle, dimensioni risorse e binding. Nessuna prova sul firmware."}


def assign_binary_id(data: bytes, face_id: str) -> bytes:
    # Documented in Mi Create's binary adapter and m0tral emulator instructions.
    # Limit to the 9-digit field emitted by this exact backend, never vendor MWZs.
    inspect_binary(data)
    if data[40:49] != b"167210065" or data[49] != 0:
        raise ValueError("Campo ID inatteso: il backend richiede una nuova verifica.")
    if not re.fullmatch(r"[1-9][0-9]{8}",face_id):
        raise ValueError("L'adattatore EasyFace supporta ID di 9 cifre.")
    updated=bytearray(data)
    updated[40:49]=face_id.encode("ascii")
    return bytes(updated)


@dataclass
class NativeSource:
    project_path: Path
    expected_sources: list[str]


def generate_fprj(p: Project, directory: Path, aod=False, filename='quadrante', variant_index=0) -> NativeSource:
    if not aod and p.variants:
        expected=[]
        main=None
        for index,v in enumerate(p.variants):
            resolved=p.variant_project(index)
            if index:resolved.aod_enabled=False
            result=generate_fprj(resolved,directory,filename='quadrante' if index==0 else f'variante_{index+1:02}',variant_index=index)
            main=main or result.project_path
            expected+=result.expected_sources
        return NativeSource(main,expected)
    from .motion import LUA_SOURCES, excluded_from_aod, pointer_period, SWEEP_PERIOD_MS
    directory.mkdir(parents=True,exist_ok=True)
    images=directory/"images"
    images.mkdir(exist_ok=True)
    (directory/"output").mkdir(exist_ok=True)
    thumbnail=f'thumbnail_{filename}.png'
    render(p,aod=aod,circular=False).convert("RGB").save(images/thumbnail)
    # EasyFace's CLI parses IDs as Int32; Xiaomi template IDs have 12 digits.
    # Use its verified intermediate ID and assign the full template ID afterwards.
    face=ET.Element("FaceProject",DeviceType="562",Id="167210065")
    screen=ET.SubElement(face,"Screen",Title=p.name,Bitmap=thumbnail,Width="480",Height="480")
    expected=[]

    def widget(shape,name,x,y,width,height,**attrs):
        values=dict(Shape=str(shape),Name=name,X=str(x),Y=str(y),Width=str(width),Height=str(height),Alpha="255",Visible_Src="0")
        values.update({k:str(v) for k,v in attrs.items()})
        return ET.SubElement(screen,"Widget",values)

    def image(name,im,x,y,visible="0"):
        filename=name+".png"
        im.save(images/filename)
        widget(30,name,x,y,im.width,im.height,Bitmap=filename,Visible_Src=visible)

    image(f'background_{variant_index}',Image.new("RGB",(480,480),"#000000" if aod else p.background),0,0)
    from .lua_runtime import scene_layers,write_scene
    lua_scene=scene_layers(p,aod)
    lua_ids={e.id for e in lua_scene}
    for e in p.ordered_layers(aod):
        if isinstance(e,dict):
            if e['visible']:
                # Replaced with the real native Slot by compose(), at this exact
                # point in the layer stack. Transparent pixels never show up.
                image('slot_'+e['id'],Image.new('RGBA',(e['width'],e['height'])),e['x'],e['y'])
            continue
        if not e.visible or e.aod!=aod or (aod and excluded_from_aod(e)):
            continue
        if e.id in lua_ids:
            if e.id==lua_scene[-1].id:
                from urllib.parse import quote
                name=write_scene(p,lua_scene,directory,variant_index)
                widget(34,'app_'+quote(name,safe=''),0,0,480,480)
            continue
        prefix=f'el_{variant_index}_'+e.id
        if e.kind=='image':
            clipped=canvas_image(p,e)
            if clipped:
                bitmap,x,y=clipped;image(prefix,bitmap,x,y)
        elif e.kind in {"text","rect","circle"}:
            from .render import canvas_static
            clipped=canvas_static(p,e)
            if clipped:
                bitmap,x,y=clipped;image(prefix,bitmap,x,y)
        elif e.kind=='image_values':
            names=[]
            for value,asset in e.value_assets.items():
                name=f'{prefix}_value_{value}.png'
                from dataclasses import replace
                from .render import canvas_static
                clipped=canvas_static(p,replace(e,kind='image',asset=asset,fit='contain'))
                if clipped is None:continue
                bitmap,x,y=clipped;bitmap.save(images/name)
                names.append(f'({value}):{name}')
            code=SOURCES[e.source][1];expected.append(code)
            if not names:continue
            widget(31,prefix,x,y,bitmap.width,bitmap.height,BitmapList='|'.join(names),Index_Src=code,DefaultIndex=list(e.value_assets).index('99') if '99' in e.value_assets else 0)
        elif e.kind in {"clock","date","number"}:
            cw,ch,_=digit_metrics(p,e)
            groups,sep=number_parts(p,e)
            for n,(src,count,x,y) in enumerate(groups):
                code=SOURCES[src][1]
                expected.append(code)
                names=[]
                for digit in "0123456789-.":
                    name=f"{prefix}_{n}_{'minus' if digit=='-' else 'dot' if digit=='.' else digit}.png"
                    digit_image(p,e,digit).save(images/name)
                    names.append(name)
                widget(32,f"{prefix}_{n}",e.x+x,e.y+y,count*cw,ch,
                       BitmapList="|".join(names),Digits=count|(e.decimals<<4 if e.kind=='number' else 0),Alignment=0,Value_Src=code,
                       Spacing=0,Blanking=0 if e.leading_zero or e.kind in {"clock","date"} else 1)
            if sep:
                char,x,y,w,h=sep
                im=Image.new("RGBA",(w,h))
                box=font_for(p,e).getbbox(char)
                ImageDraw.Draw(im).text(((w-(box[2]-box[0]))//2-box[0],1-digit_metrics(p,e)[2]),char,font=font_for(p,e),fill=rgba(e))
                image(prefix+"_separator",im,e.x+x,e.y+y)
        elif e.kind in ('pointer','compass'):
            if e.show_shadows:
                pair=hand_image(e,'second',p,shadow=True)
                if pair:
                    shadow,sa=pair;shadow.save(images/(prefix+'_pointer_shadow.png'))
                    dx,dy=hand_shadow_offset(e,'second',p)
                    widget(27,'pointer_shadow_'+e.id,e.x+e.width//2-sa[0]+dx,e.y+e.height//2-sa[1]+dy,e.width,e.height,
                           HourHand_ImageName='',MinuteHand_Image=prefix+'_pointer_shadow.png',SecondHand_Image='',
                           MinuteImage_rotate_xc=sa[0],MinuteImage_rotate_yc=sa[1],
                           Background_ImageName='',BgImage_rotate_xc=0,BgImage_rotate_yc=0,
                           HourHandCorrection_En=0,MinuteHandCorrection_En=0)
                    expected.append('1011')
            hand,anchor=hand_image(e,'second',p);hand.save(images/(prefix+'_pointer.png'))
            # One native pointer encoded by EasyFace. compose() assigns the
            # configured source/range using the observed S5 pointer descriptor.
            # EasyFace centres a clock when HourHand is present. A lone
            # MinuteHand/SecondHand instead uses X/Y as bitmap origin.
            widget(27,'pointer_'+e.id,e.x+e.width//2-anchor[0],e.y+e.height//2-anchor[1],e.width,e.height,
                   HourHand_ImageName='',MinuteHand_Image=prefix+'_pointer.png',SecondHand_Image='',
                   MinuteImage_rotate_xc=anchor[0],MinuteImage_rotate_yc=anchor[1],
                   Background_ImageName='',BgImage_rotate_xc=0,BgImage_rotate_yc=0,
                   HourHandCorrection_En=0,MinuteHandCorrection_En=0)
            expected.append('1011')
        elif e.kind == "analog":
            image(prefix+"_ticks",analog_face(e),e.x,e.y)
            # Separate native pointers let each shadow overlap the lower hands.
            # Keep EasyFace's hour-centred / minute-second bitmap origins.
            for h,title,attr,code in [('hour','Hour','HourHand_ImageName','0811'),('minute','Minute','MinuteHand_Image','1011'),('second','Second','SecondHand_Image','1811')]:
                if h=='second' and (not e.second_hand or aod):continue
                for is_shadow in ([True,False] if e.show_shadows else [False]):
                    pair=hand_image(e,h,p,shadow=is_shadow)
                    if pair is None:continue
                    bitmap,sa=pair;suffix='_shadow' if is_shadow else ''
                    name=prefix+'_'+h+suffix+'.png';bitmap.save(images/name)
                    dx,dy=hand_shadow_offset(e,h,p) if is_shadow else (0,0)
                    attrs=dict(HourHand_ImageName='',MinuteHand_Image='',SecondHand_Image='',
                               Background_ImageName='',BgImage_rotate_xc=0,BgImage_rotate_yc=0,
                               HourHandCorrection_En=1,MinuteHandCorrection_En=0)
                    attrs.update({attr:name,title+'Image_rotate_xc':sa[0],title+'Image_rotate_yc':sa[1]})
                    x,y=e.x+dx,e.y+dy
                    if h!='hour':x+=e.width//2-sa[0];y+=e.height//2-sa[1]
                    widget(27,prefix+'_'+h+suffix+(f'_smooth[{SWEEP_PERIOD_MS}]' if h=='second' and e.smooth_seconds and not aod else ''),x,y,e.width,e.height,**attrs)
                    expected.append(code)
            dot=Image.new("RGBA",(14,14))
            ImageDraw.Draw(dot).ellipse((1,1,13,13),fill=rgba(e))
            image(prefix+"_center",dot,e.x+e.width//2-7,e.y+e.height//2-7)
    path=directory/(filename+'.fprj')
    ET.indent(face)
    ET.ElementTree(face).write(path,encoding="utf-8",xml_declaration=True)
    if p.aod_enabled and not aod:
        extra=generate_fprj(p,directory/"AOD",True)
        expected+=extra.expected_sources
    return NativeSource(path,expected)


def export_local_test_zip(p: Project, data: bytes, target: Path) -> dict:
    """Experimental wrapper for the user-tested uploader with capability checking off.

    Only our compiled payload and our metadata/previews are packaged. The Xiaomi
    reference's capability masks, hashes, resource map and graphics are not reused.
    This is a hardware test candidate, not a certified native Xiaomi MWZ export.
    """
    errors=p.validate()+layout_errors(p)
    for index in range(len(p.variants)):
        resolved=p.variant_project(index)
        errors+=resolved.validate()+layout_errors(resolved)
    if errors:
        raise ValueError('\n'.join(errors))
    binary=inspect_binary(data)
    if binary['faceId'] != p.face_id or binary['screenCount'] != (2 if p.aod_enabled else 1):
        raise ValueError('Il binario non corrisponde all’ID o alle schermate del progetto.')
    watch=ET.Element('watch')
    fields={'shape':'circle','name':p.name,'deviceType':'P62','version':p.version,
            'size':'480x480','author':p.author or 'S5 Studio','pkgName':p.face_id,
            'watchOS':'vela','deviceRegion':'international'}
    for name,value in fields.items():
        ET.SubElement(watch,name).text=value
    ET.indent(watch)
    description=ET.tostring(watch,encoding='utf-8',xml_declaration=True)
    preview=png_bytes(render(p))
    info={'kind':'experimental-easyface-local-zip','device':'M2530W1','target':562,
          'faceId':p.face_id,'binarySha256':binary['sha256'],
          'requiresCapabilityVerificationOff':True,'hardwareVerified':False,
          'regionMetadata':'international','compilerRegionParameter':None,
          'note':'Metadati regione, non modifica del firmware o delle capacità. Accettazione uploader e preview da provare.'}
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.suffix.lower()!='.zip':
        raise ValueError('Usa l’estensione .zip per il pacchetto di prova locale.')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('resource.bin',data)
        z.writestr('description.xml',description)
        # The vendor reference uses preview/; root PNG is a compatibility candidate
        # for uploader versions that look there. Neither display path is certified.
        for name in ('preview.png','preview/preview.png','preview/market-preview.png'):
            z.writestr(name,preview)
        if p.aod_enabled:
            aod_preview=png_bytes(render(p,aod=True))
            z.writestr('aod-preview.png',aod_preview)
            z.writestr('preview/aod-preview.png',aod_preview)
        z.writestr('s5studio-test.json',json.dumps(info,ensure_ascii=False,indent=2))
    inspected=inspect_mwz(target)
    return {**info,'filename':target.name,'zipSha256':inspected['sha256'],'zipCrc':inspected['zipCrc']}


def build(p: Project, compiler: Path, destination: Path, progress=lambda _: None, *, template_path: Path | None=None) -> Path:
    started=time.perf_counter();stages=[];notify=progress
    def progress(message):
        stages.append({'stage':message,'elapsedSeconds':round(time.perf_counter()-started,3)})
        notify(message)
    progress('Preparazione del progetto e controllo del compilatore…')
    from .template_package import resolve_template, template_profile, template_identity, apply_template
    template_path=resolve_template(template_path)
    template_info=template_profile(template_path)
    errors=p.validate()+layout_errors(p)
    for index in range(len(p.variants)):
        resolved=p.variant_project(index)
        errors+=resolved.validate()+layout_errors(resolved)
    if errors:
        raise ValueError("\n".join(errors))
    if not any(e.visible and not e.aod and e.kind in {"clock","analog"} for e in p.elements):
        raise ValueError("Aggiungi almeno un componente Ora o Lancette.")
    if p.aod_enabled and not any(e.visible and e.aod and e.kind in {"clock","analog"} for e in p.elements):
        raise ValueError("L'AOD attivo richiede un componente Ora o Lancette.")
    tool=compiler_probe(compiler)
    destination=Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    stamp=time.strftime("%Y%m%d-%H%M%S")
    label=re.sub(r"[^a-zA-Z0-9_-]+","_",p.name).strip("_") or "quadrante"
    final=destination/f"{label}-{p.face_id}-{stamp}"
    suffix=1
    while final.exists():
        final=destination/f"{label}-{p.face_id}-{stamp}-{suffix}"
        suffix+=1
    # All work stays under the selected build directory; the compiler has no adb
    # executable beside it. It cannot push to an emulator or attached watch.
    with tempfile.TemporaryDirectory(prefix=".s5-build-",dir=destination) as temp:
        work=Path(temp)
        source=generate_fprj(p,work/"source")
        p.save(work/'source/studio.s5faceproj')
        reproduction={'schemaVersion':1,'files':{f.relative_to(work/'source').as_posix():sha256(f.read_bytes())
                       for f in (work/'source').rglob('*') if f.is_file() and f.suffix in ('.fprj','.png','.s5faceproj')}}
        (work/'source/studio-export.json').write_text(json.dumps(reproduction,indent=2),encoding='utf8')
        runtime=work/"runtime"
        runtime.mkdir()
        exe=runtime/"Compiler.exe"
        shutil.copy2(compiler,exe)
        db=Path(compiler).parent/"DeviceInfo.db"
        if db.exists():
            shutil.copy2(db,runtime/db.name)
        output=work/"compiled"
        output.mkdir()
        progress("Compilazione EasyFace per MiWatchS5…")
        try:
            env=dict(os.environ)
            # The compiler's optional ADB deployment must not find a global adb.
            # .NET and embedded dependencies do not require the user's PATH.
            env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
            result=subprocess.run([str(exe),"-b",str(source.project_path),str(output),"quadrante.face","167210065"],
                                  cwd=runtime,stdin=subprocess.DEVNULL,capture_output=True,timeout=90,
                                  env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except subprocess.TimeoutExpired as exc:
            log=(exc.stdout or b"")+(exc.stderr or b"")
            failure=destination/f"errore-{p.face_id}-{stamp}.log"
            failure.write_bytes(log)
            raise ValueError(f"Il compilatore ha superato 90 secondi. Log: {failure}") from exc
        log=result.stdout.decode("utf-8",errors="replace")+result.stderr.decode("utf-8",errors="replace")
        raw=output/"quadrante.face"
        if result.returncode != 0 or not raw.is_file() or "No Errors" not in log or "Watch: MiWatchS5" not in log:
            failure=destination/f"errore-{p.face_id}-{stamp}.log"
            failure.write_text(log,encoding="utf-8")
            raise ValueError(f"Compilazione fallita. Log: {failure}\n{log[-1800:]}")
        original=raw.read_bytes()
        progress('Compilazione principale completata; preparazione delle risorse…')
        if original[40:49]!=b'167210065' or original[49]!=0:
            raise ValueError('Campo ID del compilatore diverso dal valore predefinito verificato.')
        data=template_identity(original,p.face_id)
        inspection=inspect_binary(data)
        # AOD uses a second directory, whose layout is validated separately below.
        got=[w["source"] for screen in inspection["screens"] for w in screen["widgets"]]
        if inspection['screenCount'] != max(1,len(p.variants))+(1 if p.aod_enabled else 0):
            raise ValueError("Il compilatore non ha mantenuto il numero di schermate richiesto.")
        if sorted(got)!=sorted(source.expected_sources):
            raise ValueError(f"Binding nativi inattesi. Attesi {source.expected_sources}, ottenuti {got}.")
        from .native_graph import factory,preview_factory,compose
        def compile_extra(path,name):
            nonlocal log
            extra=subprocess.run([str(exe),'-b',str(path),str(output),name,'167210065'],
                                 cwd=runtime,env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=120,
                                 creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            log+='\n'+name+'\n'+(extra.stdout+extra.stderr).decode('utf-8',errors='replace')
            if extra.returncode or not (output/name).is_file() or b'No Errors' not in extra.stdout+extra.stderr:
                raise ValueError('Compilazione risorse fallita:\n'+log[-1800:])
            raw=(output/name).read_bytes();inspect_binary(raw)
            return raw
        options,option_keys=factory(p,work,compile_extra,progress)
        native_previews,native_aod_preview=preview_factory(p,work,compile_extra,progress)
        with zipfile.ZipFile(template_path) as z:reference=z.read('resource.bin')
        data,generated_metadata=compose(data,p,reference,work/'source',native_previews,options,option_keys,aod_preview=native_aod_preview)
        inspection=inspect_binary(data)
        from .lua_runtime import interaction_report
        interaction=interaction_report(p,data,generated_metadata['resources/manifest.xml'])
        from .motion import native_motion_report
        seconds_motion=native_motion_report(data)
        generated_metadata['build-report.json']=json.dumps({'applicationVersion':'1.7.2',
            'binarySha256':inspection['sha256'],'interactive':interaction,
            'secondsMotion':seconds_motion,
            'hardwareVerified':False},ensure_ascii=False,indent=2).encode('utf8')
        progress("Controllo binario, risorse e ID…")
        bundle=work/"delivery"
        bundle.mkdir()
        (bundle/"resource.bin").write_bytes(data)
        (bundle/f"{label}.face").write_bytes(data)
        shutil.copytree(work/"source",bundle/"sorgenti-easyface")
        first=p.variant_project(0) if p.variants else p
        (bundle/"preview.png").write_bytes(png_bytes(render(first)))
        if p.aod_enabled:
            (bundle/"aod-preview.png").write_bytes(png_bytes(render(first,aod=True)))
        p.save(bundle/f"{label}.s5faceproj",png_bytes(render(first)))
        (bundle/"compiler.log").write_text(log,encoding="utf-8")
        previews=[png_bytes(render(p.variant_project(i))) for i in range(max(1,len(p.variants)))]
        from .semantic_package import package
        progress('Creazione ZIP e validazione del pacchetto finale…')
        packaged=package(template_path,data,previews[0],bundle/f'{label}_TEMPLATE.zip',
                         png_bytes(render(first,aod=True)) if p.aod_enabled else None,previews,p,generated_metadata)
        packaged['filename']=f'{label}_TEMPLATE.zip'
        packaged['output']=str(final/packaged['filename'])
        report={"schemaVersion":1,"applicationVersion":"1.7.2","interactive":interaction,"secondsMotion":seconds_motion,"project":p.metadata(),"compiler":tool,
                "binary":inspection,"compilerOriginalSha256":sha256(original),
                "idAssignment":{"method":"ID del progetto nel campo ASCII; descrizione, manifest, editor e UID rigenerati coerentemente.","original":"167210065","projectRequested":p.face_id,"assigned":p.face_id},
                "assets":{k:sha256(v) for k,v in p.assets.items()},
                "status":"compiled-semantically-checked-not-hardware-tested",
                "localMwz":{"available":True,"kind":"template-surgery","hardwareVerified":False,"reason":"Record protetti preservati; risorse e metadati rigenerati. Coerenza semantica verificata; firma Xiaomi non attestata."},
                "templatePackage":packaged,
                'editable':{'variantCount':max(1,len(p.variants)),'slotCount':len(p.complications),
                            'nativeSlotInstances':inspection['nativeSlots'],'aodPerVariant':p.aod_enabled,
                            'independentLayers':all(v.get('independent') for v in p.variants),
                            'styles':[{'name':v['name'],'layerCount':len(p.variant_project(i).ordered_layers(False)),
                                       'slotCount':len(p.variant_project(i).complications)} for i,v in enumerate(p.variants)],
                            'options':p.complications,'hardwareVerified':False,
                            'complicationGraphics':'Gruppi originali Studio: cornice, cifre native, etichetta, unità, anteprima e sorgente per ogni opzione.'},
                "remaining":["Provare il ZIP modificato nell’uploader locale: le installazioni precedenti non certificano questo nuovo payload.",
                             "Dati reali, fallback quando assenti, AOD, sleep/wake e consumo sul firmware dell'utente."],
                "warnings":packaged['warnings']+["I valori delle anteprime sono simulati. Non vengono usati come sorgenti dei widget nativi.",
                            "Ogni nuovo progetto ha un ID proprio per ridurre le collisioni con il template e le sue anteprime memorizzate.",
                            "Il file .info di EasyFace contiene valori costanti incongruenti ed è stato escluso.",
                            "Il messaggio ADB nel log non è prova di trasferimento: ADB è escluso dall'ambiente di build."]}
        (bundle/"build-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        (bundle/"LEGGIMI.txt").write_text(TRANSFER_GUIDE,encoding="utf-8")
        # Publish with the destination's inherited ACLs. Moving a directory out of
        # Python 3.13's private Windows temp directory retains restrictive ACLs.
        progress('Salvataggio del ZIP verificato nella cartella scelta…')
        publish_started=time.perf_counter()
        shutil.copytree(bundle,final)
        published=time.perf_counter()
        progress('Pulizia dei file temporanei…')
        cleanup_started=time.perf_counter()
    ready=time.perf_counter()
    report['exportTiming']={'totalReadySeconds':round(ready-started,3),
                          'fileReadySeconds':round(published-started,3),
                          'publishSeconds':round(published-publish_started,3),
                          'cleanupSeconds':round(ready-cleanup_started,3),
                          'stages':stages}
    (final/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    progress(f'Compilazione completata in {ready-started:.1f} s. ZIP verificato pronto.')
    return final


def inspect_mwz(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        members=archive_members(z)
        required={"resource.bin","description.xml","preview/preview.png"}
        missing=required-set(members)
        if missing:
            raise ValueError("Pacchetto incompleto: mancano "+", ".join(sorted(missing)))
        description=ET.fromstring(z.read("description.xml"))
        if description.tag != "watch":
            raise ValueError("Metadati watch non riconosciuti.")
        metadata={e.tag:e.text for e in description}
        if metadata.get("size") != "480x480" or metadata.get("deviceType") != "P62":
            raise ValueError("Il pacchetto non dichiara il profilo S5 P62 480 × 480.")
        capabilities=json.loads(z.read("capability.json")) if 'capability.json' in members else None
        if capabilities is not None and (not isinstance(capabilities,list) or not capabilities or any(not isinstance(c,dict) or not {"name","type","value"}<=set(c) for c in capabilities)):
            raise ValueError("capability.json non ha la struttura attesa.")
        with Image.open(BytesIO(z.read("preview/preview.png"))) as im:
            im.load()
            if im.format != "PNG" or im.size!=(480,480):
                raise ValueError("Preview non valida per S5.")
        binary=z.read("resource.bin")
        if len(binary)<104 or binary[:4] != MAGIC:
            raise ValueError("Payload del pacchetto non riconosciuto.")
        binary_id=binary[40:104].split(b"\0",1)[0].decode("ascii")
        if metadata.get("pkgName")!=binary_id:
            raise ValueError("ID del binario e dei metadati differenti.")
        if "resources/manifest.xml" in members:
            m=ET.fromstring(z.read("resources/manifest.xml"))
            if m.get("id")!=binary_id or m.get("width")!="480" or m.get("height")!="480":
                raise ValueError("Geometria o ID del manifest incoerenti.")
        cap_region=next((c["value"] for c in (capabilities or []) if c["name"]=="region"),None)
        warnings=[]
        if capabilities is None:
            warnings.append('capability.json assente: verifica delle capacità impossibile. Solo prova locale con controllo disattivato; compatibilità firmware non attestata.')
        if cap_region and metadata.get("deviceRegion") not in cap_region:
            warnings.append(f"Regione metadati: {metadata.get('deviceRegion')}; capacità: {cap_region}. Conservare entrambe, semantica da verificare.")
        if "hashCode" in members:
            hashes=z.read("hashCode").decode().split(',')
            if len(hashes)!=3 or any(not re.fullmatch(r'[a-fA-F0-9]{64}',h) for h in hashes):
                raise ValueError("hashCode non ha la struttura del campione.")
            warnings.append("hashCode presente: algoritmo non decodificato, autenticità non attestata.")
        if "uidmap.map" in members:
            warnings.append("uidmap.map presente: usare validate-template per controllare la coerenza dei riferimenti Studio.")
        return {"path":str(path),"sha256":sha256(Path(path).read_bytes()),"zipCrc":"passed","entries":len(members),
                "metadata":metadata,"capabilities":capabilities,"capabilityCheckAvailable":capabilities is not None,"binaryId":binary_id,
                "warnings":warnings,"hardwareVerified":False,
                "status":"Struttura controllata; firma, capacità effettive e installazione non verificate."}


TRANSFER_GUIDE = """S5 STUDIO 1.7.2 — OMBRE TRA LE LANCETTE

Apri il progetto nella 1.7.2 e genera un nuovo ZIP quando necessario.
Crono Pro si abilita nelle proprietà della lancetta grande dei secondi.
Senza flag rimane il Crono separato 1.0, già collaudato sul S5.
Piccole: scegli Ore Crono, Minuti Crono e Decimi crono - Start/Stop/Reset.
Decimi di secondo - continui gira indipendentemente dai tap.
Nascondere le lancette grandi non disattiva il flag Crono Pro.
Il flag richiesto dai decimi crono deve appartenere allo stesso stile.

Sequenza Pro: primo tap rientro allo zero, secondo tap Avvio,
terzo tap Stop lettura, quarto tap Reset/rientro all'ora corrente.
Conteggio sempre a scatti: secondi interi e decimi interi.
Il flag Movimento Fluido non cambia il conteggio Pro.
I rientri del gruppo sono sempre orari, fluidi, simultanei, durata 720 ms (velocita ridotta di un altro terzo rispetto alla 1.3).
Stili: ogni variante ha i propri livelli, immagini, lancette e complicazioni.
Scegli lo stile nel pannello Livelli e proprieta: le modifiche restano locali.
Il salvataggio usa schema 3: conserva una copia del progetto precedente.
AOD: cancella i rientri, sospende timer/animazioni e usa la schermata
AOD del progetto. Secondi e tutte le App Lua sono esclusi dall'AOD.

Il test reale 1.2 e superato, rientri orari e stili indipendenti inclusi.
La 1.7 aggiunge Genera ombre in Set lancette, anche per i set piccoli.
La 1.7.1 corregge il falso blocco dei decimi crono con livello grande nascosto.
La 1.7.2 ordina ombra ore, ore, ombra minuti, minuti, ombra secondi, secondi.
Le ombre delle lancette superiori si vedono anche su quelle inferiori.
Attiva Mostra ombre sul livello e genera nuovamente lo ZIP.
Salva il set e riapplica Usa modello per aggiornare il quadrante.
Conserva le ombre importate e i default 50% e 15 px.
Il giorno del mese simulato e 15. I progetti mantengono i valori salvati.
Per i set personali di lancette PNG: apri Set lancette, scegli
un nome, importa ore/minuti/secondi e clicca le grafiche per impostare i pivot.
Salva il set, poi selezionalo dal menu delle ore per applicare il gruppo.
Le PNG vengono incorporate nel progetto e nel quadrante compilato.
Sono mantenute rotazione e arco per testi, immagini e forme.
Le trasformazioni sono incorporate nelle PNG, con ritaglio a 480 px.
Per le forme scegli Rettangolare o Circolare nelle proprietà.
I nomi cinesi del catalogo lancette sono visualizzati in inglese.
La geometria delle anteprime Pro rimane coerente con lo ZIP.
Mantiene rientri da 720 ms e anteprime statiche _preview. Il runtime usa il clock
monotono quando disponibile; il fallback usa la fase LVGL e os.time
per le sospensioni, con precisione di un secondo durante il sonno.
Non è il cronometro dell'app di sistema. Cambio VM/quadrante resetta.
Installa lo ZIP senza estrarlo; la mod locale può non mostrare preview
oppure richiedere di disattivare Verify capability test, come già noto.
Dopo 65 s verifica minuti 1, secondi circa 5, poi Stop e Reset.
"""
