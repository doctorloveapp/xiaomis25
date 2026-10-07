from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from io import BytesIO
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import secrets
import zipfile

from PIL import Image, ImageOps

MAX_ARCHIVE = 128 * 1024 * 1024
MAX_IMAGE_PIXELS = 32_000_000
MAX_DESIGN_IMAGE_SIZE = 4096
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
PROFILE = {"id": "xiaomi-s5-46", "model": "M2530W1", "width": 480, "height": 480,
           "compilerTarget": 562, "firmware": "3.221.024", "mod": "V3.52.0i",
           "hardwareVerified": False}
SOURCES = {
    "hour": ("Ore", "0811", 2), "minute": ("Minuti", "1011", 2),
    "second": ("Secondi", "1811", 2), "day": ("Giorno", "1812", 2),
    "month": ("Mese", "1012", 2), "batteryPercent": ("Batteria", "0841", 3),
    "heartRate": ("Pulsazioni", "0822", 3), "steps": ("Passi", "0821", 5),
    "calories": ("Calorie", "0823", 4),
}
from .watchface_library import library
for _key,_item in library()['sources'].items():
    SOURCES[_key]=(_item['label'],_item['code'],5 if _key in ('healthStepCount','healthStepTarget') else 4 if _key in ('dateYear','healthCalorieValue','healthCalorieTarget','systemSensorFusionAltitude','systemSensorAtmosphericPressure') else 3)
SOURCES.update({key:(label,SOURCES[source][1],SOURCES[source][2]) for key,label,source in (
    ('spo2','SpO₂','healthOxygenSpO2'),('sleep','Sonno','healthSleepDuration'),('movement','Movimento','healthExerciseDuration')) if source in SOURCES})
HAND_ASSET_FIELDS=tuple(h+k for h in ('hour','minute','second') for k in ('_asset','_shadow_asset'))
ASSET_FIELDS=('asset','font_asset',*HAND_ASSET_FIELDS)
VARIANT_PROPERTIES={'x','y','width','height','size','color','text','asset','visible','font_asset','bold','fit','opacity','tint','hour_length','minute_length','second_length','hour_width','minute_width','second_width','show_ticks','second_hand','smooth_seconds','show_shadows','pointer_end_pivot','compass_preset'} | {h+k for h in ('hour','minute','second') for k in ('_asset','_anchor_x','_anchor_y','_color','_preset','_shadow_asset','_shadow_anchor_x','_shadow_anchor_y','_shadow_offset_x','_shadow_offset_y','_length_adjusted','_width_adjusted','_pivot_reference_x','_pivot_reference_y')}
MAX_SLOTS=16  # Studio guardrail, not a declared firmware limit.

def valid_design_geometry(kind,x,y,width,height):
    if any(type(v) is not int for v in (x,y,width,height)):return False
    if kind=='image':
        return (-MAX_DESIGN_IMAGE_SIZE<=x<=MAX_DESIGN_IMAGE_SIZE and
                -MAX_DESIGN_IMAGE_SIZE<=y<=MAX_DESIGN_IMAGE_SIZE and
                1<=width<=MAX_DESIGN_IMAGE_SIZE and 1<=height<=MAX_DESIGN_IMAGE_SIZE)
    return 0<=x<=479 and 0<=y<=479 and 1<=width<=480 and 1<=height<=480


def normalized_slot(slot):
    # Keep the appearance of saved 0.5 projects; new slots explicitly opt into
    # value-only graphics in the editor.
    return {'width':110,'height':84,'size':26,'decimals':-1,'digits':0,'unit':'','color':'#6ce5c1','background':'#101c2d','frame':'rounded','showLabel':True,'showUnit':True,'weatherMode':'icon','visible':True,'locked':False,'opacity':255,'align':'center',**slot}


def identifier() -> str:
    return secrets.token_hex(6)


def archive_members(z: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    result = {}
    size = 0
    for item in z.infolist():
        raw_name=item.orig_filename
        p = PurePosixPath(raw_name)
        if (p.is_absolute() or ".." in p.parts or "\\" in raw_name or
                ":" in raw_name or "\x00" in raw_name):
            raise ValueError("L'archivio contiene un percorso non sicuro.")
        if item.filename in result:
            raise ValueError("L'archivio contiene nomi duplicati.")
        if item.flag_bits & 1:
            raise ValueError("Gli archivi cifrati non sono supportati.")
        size += item.file_size
        if size > MAX_ARCHIVE or len(result) >= 100000:
            raise ValueError("Archivio troppo grande (limite 128 MB / 100000 voci).")
        result[item.filename] = item
    if z.testzip() is not None:
        raise ValueError("Archivio danneggiato: controllo CRC fallito.")
    return result


@dataclass
class Element:
    kind: str = "text"
    name: str = "Testo"
    id: str = field(default_factory=identifier)
    x: int = 150
    y: int = 100
    width: int = 180
    height: int = 50
    color: str = "#ffffff"
    size: int = 36
    text: str = "S5 STUDIO"
    source: str = "batteryPercent"
    digits: int = 3
    decimals: int = 0
    leading_zero: bool = False
    align: str = "center"
    asset: str = ""
    font_asset: str = ""
    bold: bool = True
    fit: str = "cover"
    opacity: int = 255
    tint: bool = False
    visible: bool = True
    locked: bool = False
    aod: bool = False
    show_ticks: bool = True
    second_hand: bool = False
    smooth_seconds: bool = False
    hour_length: int = 28
    minute_length: int = 40
    second_length: int = 44
    hour_width: int = 8
    minute_width: int = 5
    second_width: int = 2
    # Existing projects retain their exact imported geometry until a control
    # is edited. Each axis can then be adjusted independently.
    hour_length_adjusted: bool = False
    minute_length_adjusted: bool = False
    second_length_adjusted: bool = False
    hour_width_adjusted: bool = False
    minute_width_adjusted: bool = False
    second_width_adjusted: bool = False
    hour_pivot_reference_x: int = -1
    hour_pivot_reference_y: int = -1
    minute_pivot_reference_x: int = -1
    minute_pivot_reference_y: int = -1
    second_pivot_reference_x: int = -1
    second_pivot_reference_y: int = -1
    compass_preset: str = ''
    hour_color: str = ''
    minute_color: str = ''
    second_color: str = ''
    hour_asset: str = ''
    minute_asset: str = ''
    second_asset: str = ''
    hour_anchor_x: int = -1
    hour_anchor_y: int = -1
    minute_anchor_x: int = -1
    minute_anchor_y: int = -1
    second_anchor_x: int = -1
    second_anchor_y: int = -1
    show_shadows: bool = True
    pointer_end_pivot: bool = True
    hour_preset: str = ''
    minute_preset: str = ''
    second_preset: str = ''
    hour_shadow_asset: str = ''
    minute_shadow_asset: str = ''
    second_shadow_asset: str = ''
    hour_shadow_anchor_x: int = -1
    hour_shadow_anchor_y: int = -1
    minute_shadow_anchor_x: int = -1
    minute_shadow_anchor_y: int = -1
    second_shadow_anchor_x: int = -1
    second_shadow_anchor_y: int = -1
    hour_shadow_offset_x: int = 0
    hour_shadow_offset_y: int = 0
    minute_shadow_offset_x: int = 0
    minute_shadow_offset_y: int = 0
    second_shadow_offset_x: int = 0
    second_shadow_offset_y: int = 0
    value_assets: dict = field(default_factory=dict)
    value_start: int = 0
    value_range: int = 60
    angle_start: int = 0
    angle_range: int = 360

    @classmethod
    def from_dict(cls, data):
        known = cls.__dataclass_fields__
        unknown = set(data) - set(known)
        if unknown:
            raise ValueError(f"Proprietà del componente non supportate: {', '.join(sorted(unknown))}")
        return cls(**data)


@dataclass
class Project:
    name: str = "Il mio S5"
    author: str = ""
    face_id: str = field(default_factory=lambda: str(500_000_000 + secrets.randbelow(400_000_000)))
    version: str = "1.0.0"
    background: str = "#080f1b"
    aod_enabled: bool = False
    schema_version: int = 2
    profile: dict = field(default_factory=lambda: deepcopy(PROFILE))
    elements: list[Element] = field(default_factory=list)
    assets: dict[str, bytes] = field(default_factory=dict, repr=False)
    variants: list[dict] = field(default_factory=lambda:[{'id':'base','name':'Originale','accent':'#6ce5c1','background':'','imageAsset':'','overrides':{}}])
    complications: list[dict] = field(default_factory=list)
    layer_order: list[str] = field(default_factory=list)

    def copy(self):
        return deepcopy(self)

    def metadata(self):
        return {"schemaVersion": self.schema_version, "name": self.name, "author": self.author,
                "faceId": self.face_id, "version": self.version, "background": self.background,
                "aodEnabled": self.aod_enabled, "deviceProfile": self.profile,
                "elements": [asdict(el) for el in self.elements],"variants":deepcopy(self.variants),"complications":deepcopy(self.complications),"layerOrder":list(self.layer_order)}

    def ordered_layers(self,aod=False):
        """Back to front, including editable slots; preserve legacy placement."""
        all_layers={e.id:e for e in self.elements}
        all_layers.update({s['id']:normalized_slot(s) for s in self.complications})
        if self.layer_order:
            ids=list(self.layer_order)+[key for key in all_layers if key not in self.layer_order]
        else:
            ids=[];inserted=False
            for e in self.elements:
                full_background=e.kind=='image' and e.x==e.y==0 and e.width==e.height==480
                if not inserted and not e.aod and e.visible and not full_background:
                    ids.extend(s['id'] for s in self.complications);inserted=True
                ids.append(e.id)
            if not inserted:ids.extend(s['id'] for s in self.complications)
        return [all_layers[key] for key in ids if key in all_layers and
                (all_layers[key].aod if isinstance(all_layers[key],Element) else False)==aod]

    def sync_layer_order(self):
        valid={e.id for e in self.elements}|{s['id'] for s in self.complications}
        if self.layer_order:self.layer_order=[key for key in self.layer_order if key in valid]
        order=[e.id if isinstance(e,Element) else e['id'] for mode in (False,True) for e in self.ordered_layers(mode)]
        self.layer_order=order

    def variant_project(self,index=0):
        p=self.copy()
        v=self.variants[index] if self.variants else {}
        p.variants=[]
        p.background=v.get('background') or self.background
        for e in p.elements:
            if e.color.lower()=='#6ce5c1':e.color=v.get('accent','#6ce5c1')
            for k,value in v.get('overrides',{}).get(e.id,{}).items():setattr(e,k,value)
        p.complications=[normalized_slot(s) for s in p.complications]
        for s in p.complications:
            if s['color'].lower()=='#6ce5c1':s['color']=v.get('accent','#6ce5c1')
        if v.get('imageAsset'):
            background=Element(kind='image',name='Sfondo variante',asset=v['imageAsset'],x=0,y=0,width=480,height=480)
            p.elements.insert(0,background)
            if p.layer_order:p.layer_order.insert(0,background.id)
        return p

    def add_image(self, path: Path, *, background=False, aod=False) -> Element:
        with Image.open(path) as im:
            im.load()
            im = ImageOps.exif_transpose(im).convert("RGBA")
            if im.width * im.height > MAX_IMAGE_PIXELS:
                raise ValueError("Immagine troppo grande.")
            # Preserve the aspect ratio; retain enough pixels for positioning/cropping.
            im.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            out = BytesIO()
            im.save(out, "PNG")
        data = out.getvalue()
        key = "assets/" + hashlib.sha256(data).hexdigest()[:24] + ".png"
        self.assets[key] = data
        el = Element(kind="image", name="Sfondo" if background else path.stem, asset=key,
                     x=0 if background else 160, y=0 if background else 160,
                     width=480 if background else max(1,round(160*im.width/max(im.size))), height=480 if background else max(1,round(160*im.height/max(im.size))),
                     aod=aod, locked=background)
        if background:
            self.elements = [e for e in self.elements if not (e.kind == "image" and e.name == "Sfondo" and e.aod == aod)]
            self.elements.insert(0, el)
        else:
            self.elements.append(el)
        return el

    def add_font(self, path: Path) -> str:
        data = path.read_bytes()
        if len(data) > 20 * 1024 * 1024 or path.suffix.lower() not in {".ttf", ".otf"}:
            raise ValueError("Seleziona un font TTF/OTF fino a 20 MB.")
        key = "assets/" + hashlib.sha256(data).hexdigest()[:24] + path.suffix.lower()
        from PIL import ImageFont
        ImageFont.truetype(BytesIO(data), 24)
        self.assets[key] = data
        return key

    def save(self, path: Path, preview: bytes | None = None):
        errors = self.validate()
        if errors:
            raise ValueError("\n".join(errors))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        referenced = {key for e in self.elements for key in (*[getattr(e,k) for k in ASSET_FIELDS],*e.value_assets.values()) if key}
        referenced.update(v.get('imageAsset') for v in self.variants if v.get('imageAsset'))
        for v in self.variants:
            for change in v.get('overrides',{}).values():referenced.update(change[k] for k in ASSET_FIELDS if change.get(k))
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("project.json", json.dumps(self.metadata(), ensure_ascii=False, indent=2))
                for key in sorted(referenced):
                    z.writestr(key, self.assets[key])
                if preview:
                    z.writestr("preview.png", preview)
            tmp.replace(path)
        finally:
            if tmp.exists():
                tmp.unlink()

    @classmethod
    def load(cls, path: Path):
        with zipfile.ZipFile(path) as z:
            members = archive_members(z)
            if "project.json" not in members:
                raise ValueError("Questo file non è un progetto S5 Studio.")
            d = json.loads(z.read("project.json"))
            if d.get("schemaVersion") not in (1,2):
                raise ValueError("Versione del progetto non supportata: aggiorna S5 Studio.")
            p = cls(name=d["name"], author=d.get("author", ""), face_id=d["faceId"],
                    version=d.get("version", "1.0.0"), background=d["background"],
                    aod_enabled=d.get("aodEnabled", False), profile=d["deviceProfile"],
                    elements=[Element.from_dict(e) for e in d["elements"]])
            p.variants=d.get('variants') or p.variants
            p.complications=d.get('complications',[])
            p.layer_order=d.get('layerOrder',[])
            p.assets = {name: z.read(name) for name in members if name.startswith("assets/") and not members[name].is_dir()}
        errors = p.validate()
        if errors:
            raise ValueError("\n".join(errors))
        return p

    def validate(self) -> list[str]:
        errors = []
        if len(self.variants)>5:errors.append('Massimo cinque varianti grafiche.')
        variant_ids=set();variant_names=set()
        for v in self.variants:
            if not isinstance(v,dict) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,30}',str(v.get('id',''))) or v.get('id') in variant_ids:
                errors.append('ID variante non valido o duplicato.');continue
            variant_ids.add(v['id'])
            if not isinstance(v.get('name'),str) or not v['name'].strip() or len(v['name'].encode('utf-8'))>63:errors.append('Nome variante non valido.')
            elif v['name'].casefold() in variant_names:errors.append('Ogni stile deve avere un nome differente.')
            else:variant_names.add(v['name'].casefold())
            for color in ('accent','background'):
                if v.get(color) and not re.fullmatch(r'#[a-fA-F0-9]{6}',v[color]):errors.append('Colore variante non valido.')
            if v.get('imageAsset') and v['imageAsset'] not in self.assets:errors.append('Sfondo variante mancante.')
            for eid,changes in v.get('overrides',{}).items():
                element=next((e for e in self.elements if e.id==eid),None)
                if element is None or set(changes)-VARIANT_PROPERTIES:errors.append('Proprietà variante non valide.')
                elif not valid_design_geometry(element.kind,*(changes.get(k,getattr(element,k)) for k in ('x','y','width','height'))):
                    errors.append(f'{element.name}: posizione o dimensioni dello stile fuori dai limiti.')
        if len(self.complications)>MAX_SLOTS:errors.append(f'Massimo {MAX_SLOTS} slot nel progetto Studio.')
        slot_ids=set()
        for slot in self.complications:
            if not isinstance(slot,dict) or not slot.get('options') or set(slot['options'])-({'none'}|set(SOURCES)):
                errors.append('Opzioni della complicazione non valide.');continue
            slot=normalized_slot(slot)
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,30}',str(slot.get('id',''))) or slot['id'] in slot_ids:errors.append('ID slot non valido o duplicato.')
            slot_ids.add(slot.get('id'))
            if len(set(slot['options']))!=len(slot['options']) or slot.get('default') not in slot['options']:errors.append('Default/opzioni complicazione non validi.')
            if len(slot['options'])>64:errors.append('Massimo 64 opzioni per slot.')
            if any(type(slot.get(k)) is not int for k in ('x','y','width','height','size')) or not 16<=slot['width']<=480 or not 16<=slot['height']<=480 or not 0<=slot['x']<=480-slot['width'] or not 0<=slot['y']<=480-slot['height'] or not 8<=slot['size']<=160:errors.append('Geometria/font della complicazione non validi.')
            if slot['frame'] not in ('rounded','circle','none') or any(not re.fullmatch(r'#[a-fA-F0-9]{6}',slot[k]) for k in ('color','background')):errors.append('Stile complicazione non valido.')
            if slot['showLabel'] and slot['height']<64:errors.append('Complicazione: usa almeno 64 px di altezza per etichetta, numero e unità.')
            if slot['showUnit'] and slot['height']<36:errors.append('Complicazione: usa almeno 36 px di altezza per valore e unità.')
            if type(slot['decimals']) is not int or not -1<=slot['decimals']<=3 or type(slot['digits']) is not int or not 0<=slot['digits']<=6 or not isinstance(slot['unit'],str) or len(slot['unit'])>12:errors.append('Formato numerico della complicazione non valido.')
            if slot['weatherMode'] not in ('value','icon') or slot['align'] not in ('left','center','right') or type(slot['opacity']) is not int or not 0<=slot['opacity']<=255 or any(type(slot[k]) is not bool for k in ('showLabel','showUnit','visible','locked')):errors.append('Proprietà del livello complicazione non valide.')
        layer_ids={e.id for e in self.elements}|slot_ids
        if slot_ids&{e.id for e in self.elements}:errors.append('ID livello e complicazione duplicato.')
        if not isinstance(self.layer_order,list) or any(not isinstance(key,str) or key not in layer_ids for key in self.layer_order) or len(set(self.layer_order))!=len(self.layer_order):errors.append('Ordine dei livelli non valido.')
        if self.profile.get("id") != PROFILE["id"] or any(self.profile.get(k) != PROFILE[k] for k in ("width", "height", "compilerTarget", "model")):
            errors.append("Il profilo deve essere Xiaomi Watch S5 46 mm, 480 × 480, target 562.")
        if not isinstance(self.face_id, str) or not re.fullmatch(r"[1-9][0-9]{8,11}", self.face_id) or self.face_id == "167210065":
            errors.append("ID richiesto: 9–12 cifre, diverso dal valore predefinito EasyFace. Il pacchetto esportato usa questo ID.")
        if not isinstance(self.name, str) or not self.name.strip() or len(self.name.encode("utf-8")) > 60:
            errors.append("Il nome deve contenere da 1 a 60 byte UTF-8.")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", self.background):
            errors.append("Colore sfondo non valido.")
        if len(self.elements) > 100:
            errors.append("Limite di 100 componenti superato.")
        ids = set()
        for el in self.elements:
            label = str(el.name)
            if not re.fullmatch(r"[a-f0-9]{12}", str(el.id)) or el.id in ids:
                errors.append(f"{label}: ID componente non valido o duplicato.")
            ids.add(el.id)
            if el.kind not in {"image", "image_values", "text", "number", "clock", "date", "analog", "pointer", "compass", "rect", "circle"}:
                errors.append(f"{label}: tipo non supportato ({el.kind}).")
            from .motion import LUA_SOURCES
            if el.source not in SOURCES and not (el.kind == 'pointer' and el.source in LUA_SOURCES):
                errors.append(f"{label}: sorgente dati non supportata.")
            if type(el.smooth_seconds) is not bool: errors.append(f'{label}: Movimento Fluido deve essere un flag.')
            if any(type(v) is not int for v in (el.x, el.y, el.width, el.height, el.size, el.digits, el.opacity)):
                errors.append(f"{label}: geometria o stile non validi.")
                continue
            if not valid_design_geometry(el.kind,el.x,el.y,el.width,el.height):
                errors.append(f"{label}: posizione o dimensioni fuori dai limiti del canvas.")
            if not (8 <= el.size <= 160 and 1 <= el.digits <= 6 and 0 <= el.opacity <= 255):
                errors.append(f"{label}: font, numero di cifre o opacità fuori dai limiti.")
            if type(el.decimals) is not int or not 0<=el.decimals<=3 or el.decimals and el.digits<el.decimals+2:errors.append(f'{label}: numero di cifre insufficiente per i decimali.')
            if el.align not in {"left", "center", "right"} or el.fit not in {"cover", "contain", "stretch"}:
                errors.append(f"{label}: allineamento o adattamento non validi.")
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", el.color):
                errors.append(f"{label}: colore non valido.")
            if len(el.text) > 200:
                errors.append(f"{label}: testo troppo lungo.")
            for key in (getattr(el,k) for k in ASSET_FIELDS):
                if key and (not re.fullmatch(r"assets/[a-f0-9]{24}\.(png|ttf|otf)", key) or key not in self.assets):
                    errors.append(f"{label}: risorsa mancante o percorso non valido.")
            if el.kind == "image" and not el.asset:
                errors.append(f"{label}: immagine mancante.")
            if el.kind=='image_values' and (not el.value_assets or any(not re.fullmatch(r'-?\d+',str(k)) or v not in self.assets for k,v in el.value_assets.items())):errors.append(f'{label}: immagini/valori della lista non validi.')
            if el.kind=='pointer' and (any(type(getattr(el,k)) is not int for k in ('value_start','value_range','angle_start','angle_range')) or not 0<=el.value_start<=65535 or not 1<=el.value_range<=65535 or not -360<=el.angle_start<=360 or not -720<=el.angle_range<=720):errors.append(f'{label}: intervallo della lancetta piccola non valido.')
            if el.kind=='compass' and (el.source!='systemSensorCompass' or not el.asset or (el.value_start,el.value_range,el.angle_start,el.angle_range)!=(0,360,0,-360)):
                errors.append(f'{label}: la bussola richiede una grafica e il sensore bussola con rotazione −360°.')
            if el.kind in ('analog','pointer'):
                if any(type(getattr(el,k)) is not bool for k in ('show_shadows','pointer_end_pivot')):errors.append(f'{label}: opzioni ombre/perno non valide.')
                for hand in ('hour','minute','second'):
                    hand_color=getattr(el,hand+'_color')
                    if hand_color and not re.fullmatch(r'#[0-9a-fA-F]{6}',hand_color):errors.append(f'{label}: colore lancetta non valido.')
                    if type(getattr(el,hand+'_length')) is not int or not 1<=getattr(el,hand+'_length')<=100:errors.append(f'{label}: lunghezza lancetta non valida (1–100%).')
                    if type(getattr(el,hand+'_width')) is not int or not 1<=getattr(el,hand+'_width')<=100:errors.append(f'{label}: larghezza lancetta non valida (1–100 px).')
                    if any(type(getattr(el,hand+k)) is not bool for k in ('_length_adjusted','_width_adjusted')):errors.append(f'{label}: regolazione lancetta non valida.')
                    if any(type(getattr(el,hand+'_pivot_reference_'+a)) is not int or not -1<=getattr(el,hand+'_pivot_reference_'+a)<480 for a in ('x','y')):errors.append(f'{label}: riferimento pivot non valido.')
                    for suffix in ('','_shadow'):
                        asset=getattr(el,hand+suffix+'_asset')
                        anchors=[getattr(el,hand+suffix+'_anchor_'+axis) for axis in ('x','y')]
                        if any(type(v) is not int or not -1<=v<480 for v in anchors):errors.append(f'{label}: pivot lancetta non valido.')
                        if asset and asset in self.assets:
                            with Image.open(BytesIO(self.assets[asset])) as image:
                                if image.width>480 or image.height>480:errors.append(f'{label}: immagine lancetta troppo grande (massimo 480×480).')
                    if any(type(getattr(el,hand+'_shadow_offset_'+axis)) is not int or abs(getattr(el,hand+'_shadow_offset_'+axis))>480 for axis in ('x','y')):errors.append(f'{label}: offset ombra non valido.')
        return errors


def template(name="Digitale") -> Project:
    p = Project(name=f"S5 {name}")
    from .template_package import default_project_values
    defaults=default_project_values()
    if defaults:
        p.name='S5 '+name
        p.author='S5 Studio'
        p.version=defaults['version']
        p.background=defaults['background']
        p.profile['templateDefaults']=deepcopy(defaults)
    if name == "Analogico":
        p.elements = [Element(kind="analog", name="Lancette", x=60, y=60, width=360, height=360, color="#6ce5c1",second_hand=True),
                      Element(kind="date", name="Data", x=170, y=320, width=140, height=42, size=26),
                      Element(kind="text", name="Firma", x=150, y=100, width=180, height=30, text="S5 STUDIO", size=18, color="#8a9aac")]
    else:
        p.elements = [Element(kind="text", name="Firma", x=130, y=80, width=220, height=32, text="S5 STUDIO", size=20, color="#6ce5c1"),
                      Element(kind="clock", name="Ora", x=57, y=144, width=366, height=108, size=90, leading_zero=True),
                      Element(kind="date", name="Data", x=158, y=258, width=164, height=40, size=30, color="#a5b5c8"),
                      Element(kind="text", name="Etichetta batteria", x=150, y=326, width=180, height=26, text="BATTERIA  %", size=17, color="#6ce5c1"),
                      Element(kind="number", name="Batteria", source="batteryPercent", x=186, y=356, width=108, height=42, size=30)]
        if name == "Salute":
            p.elements = p.elements[:3]
            for x, label, source, digits in [(85,"BPM","heartRate",3), (245,"PASSI","steps",5)]:
                p.elements += [Element(kind="text", name=label, text=label, x=x, y=328, width=150, height=25, size=16, color="#6ce5c1"),
                               Element(kind="number", name=SOURCES[source][0], source=source, digits=digits, x=x, y=360, width=150, height=42, size=28)]
    if defaults and defaults['aodEnabled']:
        p.aod_enabled=True
        p.elements += [Element(kind='analog',name='Lancette AOD',aod=True,x=80,y=80,width=320,height=320,color='#808080') if name=='Analogico' else Element(kind='clock',name='Ora AOD',aod=True,x=95,y=190,width=290,height=75,size=64),
                       Element(kind='date',name='Data AOD',aod=True,x=166,y=282,width=148,height=34,size=26,color='#808080')]
    return p
