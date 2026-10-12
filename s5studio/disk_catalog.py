"""Editable discs: native rotating pointers and original calendar image sequences.

Use the hand catalog's content-addressed PNG storage and shadow recipe. Catalog
edits never alter source watchfaces or assets already embedded in a project.
"""
from copy import deepcopy
import uuid
from .hand_sets import HandSetCatalog, SHADOW_OPTIONS
from .moon_disk import SOURCE,REFERENCE_DATE,calibration_errors

CATEGORIES={'celestial':'Sole, luna e stelle','compass':'Bussole',
            'mechanical':'Meccanismi','dial':'Quadranti e ghiere','custom':'Personali'}


def empty_disk():
    return {'id':'','name':'','category':'custom','mode':'rotation','source':'timeHour',
            'valueStart':0,'valueRange':24,'angleStart':0,'angleRange':360,
            'moonReferenceDate':REFERENCE_DATE,'moonDayOffset':0,
            'small':True,'hands':{},'generateShadows':False,'shadowOptions':deepcopy(SHADOW_OPTIONS)}


class DiskCatalog(HandSetCatalog):
    def stage(self,path):
        item=super().stage(path)
        item['pivot']=[n//2 for n in item['size']]
        return item

    def draft(self,identity):
        return {**empty_disk(),**deepcopy(next(s for s in self.sets() if s['id']==identity))}

    def validate_record(self,record):
        from .model import SOURCES
        name=record.get('name','').strip()
        if not name or len(name)>80 or any(ord(c)<32 for c in name):
            raise ValueError('Inserisci un nome del disco da 1 a 80 caratteri.')
        if record.get('category') not in CATEGORIES or record.get('mode') not in ('rotation','values'):
            raise ValueError('Categoria o modalità del disco non valida.')
        if record.get('source') not in SOURCES and record.get('source')!=SOURCE:raise ValueError('Sorgente del disco non supportata.')
        if record.get('source')==SOURCE:
            errors=calibration_errors(record.get('moonReferenceDate',REFERENCE_DATE),record.get('moonDayOffset',0))
            if errors:raise ValueError('\n'.join(errors))
            if record['mode']!='rotation' or record['valueStart']!=0 or record['valueRange']!=59 or record['angleRange'] not in (-360,360):
                raise ValueError('Disco lunare: modalità rotante, valori 0/59 e rotazione ±360°.')
        for key,lo,hi in [('valueStart',0,65535),('valueRange',1,65535),('angleStart',-360,360),('angleRange',-720,720)]:
            if type(record.get(key)) is not int or not lo<=record[key]<=hi:
                raise ValueError('Calibrazione disco non valida: '+key)
        hands=record.get('hands',{})
        if not hands or len(hands)>120:raise ValueError('Importa almeno una PNG (massimo 120 immagini).')
        if record['mode']=='rotation' and set(hands)!={'disk'}:
            raise ValueError('Un disco rotante richiede una sola PNG. Per una sequenza scegli Immagini per valore.')
        for key,item in hands.items():
            if record['mode']=='values' and (not str(key).isdigit() or int(key)>65535):
                raise ValueError('Ogni immagine della sequenza richiede un valore numerico da 0 a 65535.')
            self.validate_item(item)
            if item.get('shadow'):self.validate_item(item['shadow'])
        if record['mode']=='values' and len({(tuple(i['size']),tuple(i['pivot'])) for i in hands.values()})!=1:
            raise ValueError('Le immagini di una sequenza devono avere le stesse dimensioni e lo stesso pivot.')
        if record['mode']=='values':
            shadows=[i['shadow'] for i in hands.values() if i.get('shadow')]
            if shadows and (len(shadows)!=len(hands) or len({(tuple(s['size']),tuple(s['pivot']),tuple(s['offset'])) for s in shadows})!=1):
                raise ValueError('Le ombre di una sequenza devono coprire tutte le immagini e condividere dimensioni, pivot e spostamento. Puoi usare Genera ombre.')
        return name

    def save(self,draft):
        record=self.refresh_generated({**empty_disk(),**deepcopy(draft)})
        name=self.validate_record(record);identity=record['id']
        records=self.sets()
        if identity and not any(s['id']==identity for s in records):raise ValueError('Disco non trovato.')
        if any(s['id']!=identity and s['name'].casefold()==name.casefold() for s in records):
            raise ValueError('Esiste già un disco con questo nome.')
        record={k:record[k] for k in empty_disk()}
        record.update(id=identity or 'disk-'+uuid.uuid4().hex,name=name)
        # Public drafts contain data URLs; only persist the verified PNG metadata.
        for item in record['hands'].values():
            item.pop('preview',None)
            if item.get('shadow'):item['shadow'].pop('preview',None)
        original=next((s for s in records if s['id']==identity),{})
        if original.get('origin'):record['origin']=deepcopy(original['origin'])
        local=self._read(self.path)
        self._write([s for s in local['sets'] if s['id']!=identity]+[record])
        return record

    def summaries(self):
        bundled={s['id'] for s in self._read(self.bundled_root/'catalog.json')['sets']} if self.bundled_root else set()
        local={s['id'] for s in self._read(self.path)['sets']}
        return [{**{k:s[k] for k in ('id','name','category','mode','source')},
                 'frames':len(s['hands']),'bundled':s['id'] in bundled,
                 'modified':s['id'] in bundled and s['id'] in local} for s in self.sets()]

    def deleted_bundled(self):
        """Bundled discs hidden locally remain available for explicit restoration."""
        hidden=set(self._read(self.path).get('hidden',[]))
        records=self._read(self.bundled_root/'catalog.json')['sets'] if self.bundled_root else []
        return [{'id':s['id'],'name':s['name']} for s in records if s['id'] in hidden]

    def changes(self,project,identity):
        record=self.draft(identity);self.validate_record(record)
        def embed(item):
            raw=self.bitmap_path(item).read_bytes();key='assets/'+item['sourceSha256'][:24]+'.png'
            project.assets[key]=raw;return key
        item=next(iter(record['hands'].values()));shadow=item.get('shadow')
        changes={'disk_preset':identity,'disk_mode':record['mode'],'source':record['source'],
                 'moon_reference_date':record['moonReferenceDate'],'moon_day_offset':record['moonDayOffset'],
                 'asset':embed(item),'value_start':record['valueStart'],'value_range':record['valueRange'],
                 'angle_start':record['angleStart'],'angle_range':record['angleRange'],
                 'second_anchor_x':item['pivot'][0],'second_anchor_y':item['pivot'][1],
                 'second_shadow_asset':embed(shadow) if shadow else '',
                 'second_shadow_anchor_x':shadow['pivot'][0] if shadow else -1,
                 'second_shadow_anchor_y':shadow['pivot'][1] if shadow else -1,
                 'second_shadow_offset_x':shadow['offset'][0] if shadow else 0,
                 'second_shadow_offset_y':shadow['offset'][1] if shadow else 0,
                 'show_shadows':bool(shadow),'pointer_end_pivot':False,'tint':False,
                 'value_assets':{},'disk_shadow_assets':{}}
        if record['mode']=='values':
            changes['value_assets']={k:embed(i) for k,i in record['hands'].items()}
            changes['disk_shadow_assets']={k:embed(i['shadow']) for k,i in record['hands'].items() if i.get('shadow')}
        return changes


def selected_frame(e,values):
    value=values.get(e.source)
    keys=sorted(e.value_assets,key=int)
    if value is None:return keys[0]
    return next((key for key in reversed(keys) if int(key)<=int(value)),keys[0])


def native_frames(project,e):
    """Bake frame shadows with one common canvas; calendars stay native and live."""
    from .render import element_image
    frames={key:element_image(project,e,{e.source:int(key)},viewport=(480,480),origin=(e.x,e.y)) for key in e.value_assets}
    boxes=[im.getbbox() for im in frames.values() if im.getbbox()]
    if not boxes:raise ValueError('La sequenza del disco è completamente trasparente.')
    box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    return {key:im.crop(box) for key,im in frames.items()},box[:2]
