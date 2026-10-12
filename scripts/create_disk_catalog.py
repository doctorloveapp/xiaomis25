"""Recover reusable discs and complete native image sequences from all 39 faces."""
from pathlib import Path
from collections import Counter
from io import BytesIO
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageChops
from s5studio.watchface_library import resource_path
from s5studio.disk_catalog import DiskCatalog,empty_disk


def create():
    corpus=json.loads((ROOT/'docs/library-analysis/catalog.json').read_text(encoding='utf8'))
    library=json.loads((ROOT/'data/watchface-library.json').read_text(encoding='utf8'))
    catalog=DiskCatalog(ROOT/'resources/disks');records=[];seen={};coverage=[]
    def read(base,src):
        with Image.open(resource_path(base,src)) as im:return im.convert('RGBA')
    def circular(im):
        w,h=im.size;alpha=im.getchannel('A');box=alpha.getbbox()
        if not box or min(w,h)<45 or max(w,h)>380 or not .85<=w/h<=1.18:return False
        if (box[2]-box[0])<w*.8 or (box[3]-box[1])<h*.8:return False
        mask=Image.new('L',(w,h));ImageDraw.Draw(mask).ellipse((0,0,w-1,h-1),fill=255)
        outside=ImageChops.subtract(alpha,mask)
        return sum(outside.getdata())<sum(alpha.getdata())*.08
    def add(name,category,source,images,origin,*,mode='rotation',calibration=None):
        signature=json.dumps([mode,source,[(k,hashlib.sha256(im.tobytes()+str(im.size).encode()).hexdigest()) for k,im in images.items()]],sort_keys=True)
        if signature in seen:
            seen[signature]['origin']['alsoFrom'].append(origin);return
        record={**empty_disk(),'id':'disc-'+hashlib.sha256(signature.encode()).hexdigest()[:24],
                'name':name[:80],'category':category,'mode':mode,'source':source,
                'origin':{**origin,'alsoFrom':[]}}
        if calibration:record.update(calibration)
        if mode=='values':record['angleRange']=0
        for key,im in images.items():
            record['hands'][key]=catalog._store_image(im,name+'_'+key+'.png',[im.width//2,im.height//2],[0,0])
        catalog.validate_record(record);records.append(record);seen[signature]=record
    for face in corpus['watchfaces']:
        base=ROOT/face['base'];nodes={n.get('name'):n for n in face['resources']};before=len(records);scanned=0;missing=[]
        # Image arrays retain the original source and explicit values. A lunar
        # phase is not incorrectly replaced with a 24-hour rotating bitmap.
        for n in face['resources']:
            if n['tag']!='DataItemImageValues':continue
            array=nodes.get(n.get('ref','').lstrip('@'),{});entries=array.get('items',[])
            if not entries or n.get('source') not in library['sources']:continue
            try:images=[read(base,i['src']) for i in entries]
            except ValueError as exc:missing.append(str(exc));continue
            scanned+=len(images)
            celestial=n.get('source') in ('dateMoon','dateLunarDay','miscTimeSection')
            compass='指南针' in str(entries) or 'compass' in str(entries).lower()
            if not celestial and not all(circular(im) for im in images):continue
            if not all(im.size==images[0].size and max(im.size)<=480 for im in images):continue
            values=[str(i['value']) for i in n.get('items',[]) if str(i['value']).isdigit()] or [str(i) for i in range(len(images))]
            # Arrays can retain unused editor/default frames after their mapped
            # entries. Keep the explicit mapping; do not invent sensor values.
            if len(values)>len(images):raise ValueError('Mappa originale incoerente: '+face['folder']+'/'+n['name'])
            category='celestial' if celestial else 'compass' if compass else 'dial'
            label=('Lunar disc' if n.get('source')=='dateLunarDay' else 'Moon phases' if n.get('source')=='dateMoon' else 'Sun and sky' if celestial else 'Compass dial' if compass else 'Value disc')
            add(f"{label} · {face['folder']} · {n['name']}",category,n['source'],dict(zip(values,images)),
                {'face':face['folder'],'resource':n['name'],'originalSource':n['source'],'paths':[i['src'] for i in entries]},mode='values')
        pointer_images={n.get('ref','').lstrip('@') for n in face['resources'] if n['tag']=='DataItemPointer'}
        for n in face['resources']:
            if n['tag']=='SpriteGroup':
                for entry in n.get('items',[]):
                    array=nodes.get(entry.get('ref','').lstrip('@'),{});entries=array.get('items',[])
                    if not entries:continue
                    im=read(base,entries[0]['src'])
                    if not circular(im):continue
                    add(f"Mechanical rotor · {face['folder']} · {n['name']}",'mechanical','timeSecond',{'disk':im},
                        {'face':face['folder'],'resource':n['name'],'paths':[i['src'] for i in entries],
                         'note':'Recovered rotor graphic; rotation uses native seconds, not the original sprite animation.'},
                        calibration={'valueRange':60})
            if n['tag']!='Image' or n['name'] in pointer_images or any(k in n.get('src','').lower() for k in ('_preview/','_widget/','preview')):continue
            try:im=read(base,n['src']);scanned+=1
            except ValueError as exc:missing.append(str(exc));continue
            if not circular(im):continue
            add(f"Dial disc · {face['folder']} · {n['name']}",'dial','timeHour',{'disk':im},
                {'face':face['folder'],'resource':n['name'],'paths':[n['src']],
                 'note':'Static original graphic; default rotation is one turn per 24 hours.'})
        coverage.append({'face':face['folder'],'imagesScanned':scanned,'newDiscs':len(records)-before,'missingNonDiskResources':missing})
    # Include every existing compass, including the complete assembled roses
    # and the small north needles; do not change the original compass catalog.
    for p in library['compasses']:
        with Image.open(ROOT/p['assetPath']) as im:im=im.convert('RGBA')
        add(f"Compass · {p['label']}",'compass','systemSensorCompass',{'disk':im},
            {'face':p['face'],'resource':p['resource'],'paths':[p['assetPath']]},
            calibration={'valueRange':360,'angleRange':-360})
    # Retain centered rings natively bound to seconds in the original corpus.
    for p in library['hands']:
        with Image.open(ROOT/p['assetPath']) as im:im=im.convert('RGBA')
        if min(im.size)<400 or p['pivot']!=[v//2 for v in im.size]:continue
        box=im.getchannel('A').getbbox()
        if not box or min(box[2]-box[0],box[3]-box[1])<400:continue
        face=next(f for f in corpus['watchfaces'] if f['folder']==p['face'])
        n=next(n for n in face['resources'] if n.get('name')==p['resource'])
        add(f"Rotating ring · {p['face']} · {p['resource']}",'dial',p['source'],{'disk':im},
            {'face':p['face'],'resource':p['resource'],'paths':[p['path']]},
            calibration={k:int(float(n[k[0].lower()+k[1:]])) for k in ('valueStart','valueRange','angleStart','angleRange')})
    # Preserve verified graphics explicitly supplied by the user after recovery.
    for record in catalog._read(catalog.path)['sets']:
        if record.get('origin',{}).get('kind')=='user-import':
            catalog.validate_record(record);records.append(record)
    catalog._write(records)
    report={'status':'passed','watchfacesScanned':len(coverage),'discs':len(records),
            'categories':dict(Counter(r['category'] for r in records)),
            'modes':dict(Counter(r['mode'] for r in records)),
            'images':sum(len(r['hands']) for r in records),'coverage':coverage,
            'records':[{'id':r['id'],'name':r['name'],'mode':r['mode'],'source':r['source'],'images':len(r['hands']),'origin':r['origin']} for r in records]}
    (ROOT/'docs/library-analysis/discs-2.5.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','records')},indent=2));return report

if __name__=='__main__':create()
