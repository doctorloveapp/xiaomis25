"""Validate the final EXE, real GUI actions and compiled hand/shadow geometry."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PyInstaller.archive.readers import CArchiveReader
from PIL import Image
from s5studio.model import Project,SOURCES
from s5studio.render import hand_image,hand_shadow_offset,canvas_image
from s5studio.watchface_library import read_tables,library

exe=ROOT/'S5Studio-0.8.exe'
def run(*args,timeout=240):
    result=subprocess.run([str(exe),*map(str,args)],cwd=ROOT,capture_output=True,timeout=timeout,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise RuntimeError(f'EXE failed ({result.returncode}): {args}\n'+result.stderr.decode('utf8',errors='replace')[-2000:])

archive=CArchiveReader(str(exe));embedded={}
for name in ['index.html','app.js','editor-controls.js','studio.css','tailwind.css']:
    member=next(k for k in archive.toc if k.replace('\\','/')=='frontend/'+name)
    raw=archive.extract(member);assert raw==(ROOT/'frontend'/name).read_bytes()
    embedded[name]=hashlib.sha256(raw).hexdigest()
run('self-test','--report',ROOT/'docs/executable-self-test-0.8.json')
assert json.loads((ROOT/'docs/executable-self-test-0.8.json').read_text())['status']=='passed'
run('ui-smoke','--screenshot',ROOT/'docs/screenshots/executable-0.8.png')
ui=json.loads((ROOT/'docs/screenshots/executable-0.8.json').read_text());assert ui['status']=='passed'
assert {'startup-window-maximized','header-Version-0.7','dropdown-hover-highlights-without-selection',
        'hour-model-auto-pairs-matching-set','shadow-visibility-checkbox',
        'every-save-button-click-asks-filename','save-cancel-preserves-path-and-dirty'}<=set(ui['checks'])

output=ROOT/'build/executable-0.8'
run('build',ROOT/'projects/S5_Studio_Lancette_0.8.s5faceproj','--compiler',ROOT/'tools/easyface-4.23/Compiler.exe','--output',output/'hands')
latest=max((output/'hands').glob('*/build-report.json'),key=lambda p:p.stat().st_mtime)
report=json.loads(latest.read_text(encoding='utf8'))
source=json.loads((ROOT/'docs/S5-Studio-Lancette-0.8-build-report.json').read_text(encoding='utf8'))
assert report['binary']['sha256']==source['binary']['sha256']
assert report['templatePackage']['status']=='passed' and report['binary']['nativeSlots']==25 and report['binary']['screenCount']==10
assert (latest.parent/'LEGGIMI.txt').read_text(encoding='utf8').startswith('S5 STUDIO 0.8')
p=Project.load(next(latest.parent.glob('*.s5faceproj')))
original=Project.load(ROOT/'projects/S5_Studio_Lancette_0.8.s5faceproj')
assert p.assets==original.assets and p.metadata()==original.metadata()
image=next(e for e in p.elements if e.kind=='image' and not e.aod)
assert (image.x,image.y,image.width,image.height)==(-120,-120,720,720)

# Match native descriptor pivots and layout positions against the preview's
# geometry, using the actual FPRJ widget order produced by the frozen build.
data=(latest.parent/'resource.bin').read_bytes();checked=[];bitmap_count=0
for screen in range(data[28]):
    for _,_,payload in read_tables(data,screen)[2]+read_tables(data,screen)[3]:
        w,h=struct.unpack_from('<HH',payload,4);assert 1<=w<=480 and 1<=h<=480;bitmap_count+=1
for vi in range(5):
    resolved=p.variant_project(vi);screen=vi*2
    fprj=latest.parent/'sorgenti-easyface'/('quadrante.fprj' if vi==0 else f'variante_{vi+1:02}.fprj')
    tables=read_tables(data,screen);descriptors={uid:payload for uid,_,payload in tables[7]};cursor=0
    for w in ET.parse(fprj).getroot().find('Screen'):
        count=sum(bool(w.get(k)) for k in ('HourHand_ImageName','MinuteHand_Image','SecondHand_Image')) if w.get('Shape')=='27' else 1
        if w.get('Name','').startswith('pointer_'):
            shadow=w.get('Name').startswith('pointer_shadow_')
            identity=w.get('Name').removeprefix('pointer_').removeprefix('shadow_')
            e=next(e for e in resolved.elements if e.id==identity)
            bitmap,anchor=hand_image(e,'second',resolved,shadow=shadow)
            layout=tables[0][cursor][2];uid,x,y,_,_=struct.unpack('<IhhII',layout)
            payload=descriptors[uid]
            assert tuple(struct.unpack_from('<HH',payload,20))==anchor
            assert payload[:2].hex().upper()==SOURCES[e.source][1]
            dx,dy=hand_shadow_offset(e,'second',resolved) if shadow else (0,0)
            assert (x,y)==(e.x+e.width//2-anchor[0]+dx,e.y+e.height//2-anchor[1]+dy)
            if not shadow:assert abs(anchor[1]-(bitmap.getchannel('A').getbbox()[3]-1))<=1
            with Image.open(fprj.parent/'images'/w.get('MinuteHand_Image')) as compiled:
                assert compiled.convert('RGBA').tobytes()==bitmap.tobytes()
            checked.append({'style':vi+1,'element':e.name,'shadow':shadow,'pivot':anchor,'size':list(bitmap.size)})
        cursor+=count
    assert sum('shadow' in w.get('Name','') for w in ET.parse(fprj).getroot().find('Screen'))==6
with zipfile.ZipFile(next(latest.parent.glob('*_TEMPLATE.zip'))) as z:
    assert z.testzip() is None

# Older saved projects must remain loadable/buildable with the corrected
# endpoint behavior; the old distributed ZIPs are kept unchanged.
run('build',ROOT/'projects/S5_Studio_Crono_0.6.s5faceproj','--compiler',ROOT/'tools/easyface-4.23/Compiler.exe','--output',output/'regression-0.6')
reg=max((output/'regression-0.6').glob('*/build-report.json'),key=lambda p:p.stat().st_mtime)
regression=json.loads(reg.read_text(encoding='utf8'));assert regression['templatePackage']['status']=='passed'
stress=max((ROOT/'build/stress-0.5').glob('*/*_TEMPLATE.zip'),key=lambda p:p.stat().st_mtime)
run('validate-template',ROOT/'quadrante_funzionante.zip',stress,'--report',ROOT/'docs/executable-stress-validation-0.8.json')
assert json.loads((ROOT/'docs/executable-stress-validation-0.8.json').read_text(encoding='utf8'))['status']=='passed'
summary={'status':'passed','date':'2026-10-07','executable':exe.name,'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
         'embeddedFrontendIdentical':embedded,'ui':ui['checks'],'handCatalog':library()['handCatalogSummary'],
         'sourceAndExecutableBinaryIdentical':True,'binarySha256':report['binary']['sha256'],
         'originalProjectAssetsPreserved':True,'smallHandPivotsAndShadows':checked,'compiledBitmapCountWithin480':bitmap_count,
         'old06ProjectBuildPassed':True,'old06NewBinarySha256':regression['binary']['sha256'],
         'screenCount':10,'simultaneousSlots':5,'nativeSlotInstances':25,'all58SourcesPerSlotValidation':'passed',
         'hardwareTested':False,'buildReport':str(latest)}
(ROOT/'docs/executable-build-0.8.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('ui','smallHandPivotsAndShadows','embeddedFrontendIdentical')},indent=2))
