"""Editable hand sets with bundled defaults and persistent local overrides."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import base64
import hashlib
import json
import math
import os
import re
import tempfile
import uuid

from PIL import Image,ImageFilter

ROLES=('hour','minute','second')
SHADOW_OPTIONS={'opacity':45,'blur':1.5,'offset':[2,3]}


def empty_draft():
    return {'id':'','name':'','small':False,'hands':{},'generateShadows':False,'shadowOptions':deepcopy(SHADOW_OPTIONS)}


class HandSetCatalog:
    def __init__(self,root,*,bundled_root=None,library_hands=(),resources=None):
        self.root=Path(root)
        self.path=self.root/'catalog.json'
        self.bundled_root=Path(bundled_root) if bundled_root else None
        self.resources=Path(resources) if resources else None
        from .builtin_hand_sets import group_library
        self.original_presets={p['id']:p for p in library_hands}
        self.builtin_sets=group_library(library_hands)
        self.builtin_by_id={s['id']:s for s in self.builtin_sets}

    @staticmethod
    def _read(path):
        if not path.exists():return {'schemaVersion':1,'sets':[]}
        data=json.loads(path.read_text(encoding='utf8'))
        if data.get('schemaVersion')!=1 or not isinstance(data.get('sets'),list):
            raise ValueError('Catalogo set lancette non valido.')
        return data

    def personal_sets(self):
        bundled=self._read(self.bundled_root/'catalog.json')['sets'] if self.bundled_root else []
        local=self._read(self.path)
        records={s['id']:s for s in bundled}
        records.update((s['id'],s) for s in local['sets'])
        return [s for k,s in records.items() if k not in local.get('hidden',[])]

    def sets(self):
        local=self._read(self.path);records={s['id']:s for s in self.builtin_sets}
        records.update((s['id'],s) for s in self.personal_sets())
        return [s for k,s in records.items() if k not in local.get('hidden',[])]

    def summaries(self):
        bundled_ids={s['id'] for s in self._read(self.bundled_root/'catalog.json')['sets']} if self.bundled_root else set()
        local_ids={s['id'] for s in self._read(self.path)['sets']}
        return [{'id':s['id'],'name':s['name'],'small':s['small'],'roles':list(s['hands']),
                 'builtin':s['id'] in self.builtin_by_id,'bundled':s['id'] in bundled_ids,
                 'modified':s['id'] in local_ids and (s['id'] in self.builtin_by_id or s['id'] in bundled_ids)} for s in self.sets()]

    def bitmap_path(self,item):
        digest=item.get('sourceSha256','')
        if not re.fullmatch('[a-f0-9]{64}',digest) or item.get('assetPath')!='assets/'+digest+'.png':
            raise ValueError('Percorso PNG del set non valido.')
        path=(self.root/item['assetPath']).resolve()
        if not path.is_relative_to((self.root/'assets').resolve()):raise ValueError('Percorso PNG non valido.')
        if not path.exists() and self.bundled_root:path=(self.bundled_root/item['assetPath']).resolve()
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('PNG del set alterata o incompleta.')
        return path

    def stage(self,path):
        """Normalize to RGBA without scaling/cropping; return source-pixel metadata."""
        with Image.open(path) as source:
            if source.format!='PNG':raise ValueError('Il set accetta soltanto file PNG.')
            if getattr(source,'n_frames',1)!=1:raise ValueError('Usa una PNG statica per la lancetta.')
            if not all(1<=n<=480 for n in source.size):raise ValueError('Ogni PNG deve misurare da 1 a 480 pixel per lato.')
            image=source.convert('RGBA')
        mask=image.getchannel('A');bounds=mask.getbbox()
        if not bounds:raise ValueError('La PNG è completamente trasparente.')
        row=mask.crop((bounds[0],bounds[3]-1,bounds[2],bounds[3])).getbbox()
        pivot=[bounds[0]+(row[0]+row[2]-1)//2,bounds[3]-1]
        return self._store_image(image,Path(path).name,pivot,[0,0])

    def _store_image(self,image,filename,pivot,offset):
        output=BytesIO();image.save(output,format='PNG');raw=output.getvalue()
        digest=hashlib.sha256(raw).hexdigest()
        relative='assets/'+digest+'.png';destination=self.root/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        # Immutable content-addressed assets also make interrupted drafts safe.
        if not destination.exists() or destination.read_bytes()!=raw:
            self._atomic_write(destination,raw)
        return {'assetPath':relative,'sourceSha256':digest,'size':list(image.size),'pivot':list(pivot),
                'filename':filename,'offset':list(offset)}

    def refresh_generated(self,draft):
        """Only generated shadows follow the recipe; imported shadows are untouched."""
        result={**empty_draft(),**deepcopy(draft)}
        if type(result['generateShadows']) is not bool:raise ValueError('Flag Genera ombre non valido.')
        options=result['shadowOptions']
        if not isinstance(options,dict) or set(options)!=set(SHADOW_OPTIONS):raise ValueError('Impostazioni ombra non valide.')
        if type(options['opacity']) is not int or not 1<=options['opacity']<=100:
            raise ValueError('Opacità ombra: scegli un valore da 1 a 100%.')
        if type(options['blur']) not in (int,float) or not math.isfinite(options['blur']) or not 0<=options['blur']<=4:
            raise ValueError('Sfocatura ombra: scegli un valore da 0 a 4 px.')
        if not isinstance(options['offset'],(list,tuple)) or len(options['offset'])!=2 or any(type(v) is not int or abs(v)>20 for v in options['offset']):
            raise ValueError('Spostamento ombra: scegli valori da −20 a 20 px.')
        options['offset']=list(options['offset'])
        for item in result['hands'].values():
            shadow=item.get('shadow')
            generated=bool(shadow and shadow.get('generated') is True)
            if not result['generateShadows']:
                if generated:item.pop('shadow')
                continue
            if shadow and not generated:continue
            self.validate_item(item)
            recipe={'engine':'alpha-black-gaussian-v1','sourceSha256':item['sourceSha256'],'pivot':list(item['pivot']),**deepcopy(options)}
            if generated and shadow.get('generatedFrom')==recipe:continue
            with Image.open(self.bitmap_path(item)) as source:
                source=source.convert('RGBA')
                padding=math.ceil(options['blur']*3)
                px=min(padding,(480-source.width)//2);py=min(padding,(480-source.height)//2)
                mask=Image.new('L',(source.width+2*px,source.height+2*py))
                mask.paste(source.getchannel('A'),(px,py))
            if options['blur']:mask=mask.filter(ImageFilter.GaussianBlur(options['blur']))
            mask=mask.point(lambda alpha:round(alpha*options['opacity']/100))
            image=Image.new('RGBA',mask.size);image.putalpha(mask)
            shadow=self._store_image(image,Path(item['filename']).stem+'_shadow_auto.png',
                                     [item['pivot'][0]+px,item['pivot'][1]+py],options['offset'])
            shadow.update(generated=True,generatedFrom=recipe)
            item['shadow']=shadow
        return result

    @staticmethod
    def _atomic_write(path,raw):
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,temporary=tempfile.mkstemp(prefix='.writing-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as output:output.write(raw)
            os.replace(temporary,path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def validate_item(self,item):
        with Image.open(self.bitmap_path(item)) as image:
            size=list(image.size)
        if size!=item.get('size') or not all(1<=n<=480 for n in size):raise ValueError('Dimensioni PNG del set non valide.')
        pivot=item.get('pivot',[])
        if len(pivot)!=2 or any(type(v) is not int or not 0<=v<size[i] for i,v in enumerate(pivot)):
            raise ValueError('Il pivot deve trovarsi dentro la PNG.')
        offset=item.get('offset',[0,0])
        if len(offset)!=2 or any(type(v) is not int or abs(v)>480 for v in offset):
            raise ValueError('Spostamento ombra non valido (da −480 a 480 px).')

    def preview(self,item):
        return {**item,'preview':'data:image/png;base64,'+base64.b64encode(self.bitmap_path(item).read_bytes()).decode()}

    def draft(self,identity):
        item={**empty_draft(),**deepcopy(next(s for s in self.sets() if s['id']==identity))}
        if identity in self.builtin_by_id and not any(s['id']==identity for s in self.personal_sets()):
            from .builtin_hand_sets import import_original
            item=import_original(self,item)
        return item

    def public_draft(self,draft):
        result=deepcopy(draft)
        for role,item in result['hands'].items():
            shadow=item.get('shadow')
            result['hands'][role]=self.preview(item)
            if shadow:result['hands'][role]['shadow']=self.preview(shadow)
        return result

    def save(self,draft):
        record=self.refresh_generated(draft);name=str(record.get('name','')).strip()
        if not name or len(name)>80 or any(ord(c)<32 for c in name):
            raise ValueError('Inserisci un nome del set da 1 a 80 caratteri.')
        if type(record.get('small')) is not bool:raise ValueError('Tipo del set non valido.')
        hands=record.get('hands',{})
        if not hands or set(hands)-set(ROLES):raise ValueError('Importa almeno una lancetta per il set.')
        identity=record.get('id','')
        if not record['small'] and set(hands)!=set(ROLES) and identity not in self.builtin_by_id:
            raise ValueError('Per un set principale importa le PNG di ore, minuti e secondi.')
        records=self.sets()
        if identity and not any(s['id']==identity for s in records):raise ValueError('Set da modificare non trovato.')
        if any(s['id']!=identity and s['name'].casefold()==name.casefold() for s in records):
            raise ValueError('Esiste già un set con questo nome: scegli un altro nome oppure modifica quel set.')
        clean={}
        for role,item in hands.items():
            self.validate_item(item)
            clean[role]={k:item[k] for k in ('assetPath','sourceSha256','size','pivot','filename','offset')}
            if item.get('shadow'):
                self.validate_item(item['shadow'])
                clean[role]['shadow']={k:item['shadow'][k] for k in ('assetPath','sourceSha256','size','pivot','filename','offset')}
                if item['shadow'].get('generated') is True:
                    clean[role]['shadow'].update(generated=True,generatedFrom=deepcopy(item['shadow']['generatedFrom']))
        record={'id':identity or 'custom-'+uuid.uuid4().hex,'name':name,'small':record['small'],'hands':clean,
                'generateShadows':record['generateShadows'],'shadowOptions':record['shadowOptions']}
        if identity in self.builtin_by_id:record['origin']=deepcopy(self.builtin_by_id[identity]['origin'])
        records=[s for s in self._read(self.path)['sets'] if s['id']!=identity]+[record]
        self._write(records)
        return record

    def _write(self,records,hidden=None):
        if hidden is None:hidden=self._read(self.path).get('hidden',[])
        raw=json.dumps({'schemaVersion':1,'sets':records,'hidden':hidden},ensure_ascii=False,indent=2).encode('utf8')
        self._atomic_write(self.path,raw)

    def delete(self,identity):
        records=self.sets()
        if not any(s['id']==identity for s in records):raise ValueError('Set non trovato.')
        if identity in self.builtin_by_id:raise ValueError('I set originali possono essere modificati o ripristinati.')
        local=self._read(self.path)
        self._write([s for s in local['sets'] if s['id']!=identity],list(dict.fromkeys(local.get('hidden',[])+[identity])))

    def restore(self,identity):
        bundled_ids={s['id'] for s in self._read(self.bundled_root/'catalog.json')['sets']} if self.bundled_root else set()
        if identity not in self.builtin_by_id and identity not in bundled_ids:raise ValueError('Set incorporato non trovato.')
        local=self._read(self.path)
        self._write([s for s in local['sets'] if s['id']!=identity],[k for k in local.get('hidden',[]) if k!=identity])

    def presets(self):
        result=[]
        personal=self.personal_sets();overrides={s['id'] for s in personal}
        hidden=self._read(self.path).get('hidden',[])
        for record in self.builtin_sets:
            if record['id'] in overrides or record['id'] in hidden:continue
            for identity in record['origin']['members'].values():
                result.append({**deepcopy(self.original_presets[identity]),'setId':record['id']})
        for record in personal:
            origin=self.builtin_by_id.get(record['id'],{}).get('origin',{}).get('members',{})
            members={role:origin.get(role,record['id']+'-'+role) for role in record['hands']}
            for role,item in record['hands'].items():
                self.validate_item(item)
                if item.get('shadow'):self.validate_item(item['shadow'])
                original=self.original_presets.get(members[role],{})
                result.append({**deepcopy(original),**deepcopy(item),'id':members[role],'name':record['name'],
                               'theme':original.get('theme','Bundled set' if self.bundled_root else 'Custom set'),
                               'author':original.get('author','Personal'),'variant':original.get('variant',''),
                               'hand':original.get('hand',role) if record['small'] else role,'small':record['small'],'aod':original.get('aod',False),
                               'shadow':deepcopy(item.get('shadow')),'setMembers':members,'custom':True,'setId':record['id']})
        return result
