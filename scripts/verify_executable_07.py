"""Verify the shipped executable, its embedded frontend and both build paths."""
from pathlib import Path
from io import BytesIO
import hashlib,json,struct,subprocess,sys,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PyInstaller.archive.readers import CArchiveReader
from PIL import Image
from s5studio.model import Project
from s5studio.render import canvas_image
from s5studio.watchface_library import read_tables

exe=ROOT/'S5Studio-0.7.exe'
def run(*args,timeout=240):
    result=subprocess.run([str(exe),*map(str,args)],cwd=ROOT,capture_output=True,
                          timeout=timeout,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise RuntimeError(f'EXE failed ({result.returncode}): {args}\n'+result.stderr.decode('utf8',errors='replace')[-2000:])

# Check the final packaged CSS/JS, including data files changed during development.
archive=CArchiveReader(str(exe));embedded={}
for name in ['index.html','app.js','editor-controls.js','studio.css','tailwind.css']:
    member=next(k for k in archive.toc if k.replace('\\','/')=='frontend/'+name)
    raw=archive.extract(member);assert raw==(ROOT/'frontend'/name).read_bytes()
    embedded[name]=hashlib.sha256(raw).hexdigest()

run('self-test','--report',ROOT/'docs/executable-self-test-0.7.json')
assert json.loads((ROOT/'docs/executable-self-test-0.7.json').read_text())['status']=='passed'
run('ui-smoke','--screenshot',ROOT/'docs/screenshots/executable-0.7.png')
ui=json.loads((ROOT/'docs/screenshots/executable-0.7.json').read_text())
assert ui['status']=='passed'
required={'empty-hand-preview-has-no-image-src','hand-hover-shows-both-previews-without-commit',
          'image-scale-beyond-480','oversized-image-negative-canvas-drag','arrow-keys-accumulate-one-pixel',
          'shift-arrows-ten-pixels','arrows-preserve-input-editing','arrow-keys-move-complication-and-small-pointer'}
assert required<=set(ui['checks'])

output=ROOT/'build/executable-0.7'
run('build',ROOT/'projects/S5_Studio_Ritaglio_0.7.s5faceproj','--compiler',
    ROOT/'tools/easyface-4.23/Compiler.exe','--output',output/'framing')
latest=max((output/'framing').glob('*/build-report.json'),key=lambda p:p.stat().st_mtime)
report=json.loads(latest.read_text(encoding='utf8'))
source=json.loads((ROOT/'docs/S5-Studio-Ritaglio-0.7-build-report.json').read_text(encoding='utf8'))
assert report['binary']['sha256']==source['binary']['sha256']
assert report['templatePackage']['status']=='passed'
assert report['binary']['nativeSlots']==25 and report['binary']['screenCount']==10
assert (latest.parent/'LEGGIMI.txt').read_text(encoding='utf8').startswith('S5 STUDIO 0.7')
p=Project.load(next(latest.parent.glob('*.s5faceproj')))
e=next(e for e in p.elements if e.kind=='image' and not e.aod)
assert (e.x,e.y,e.width,e.height)==(-120,-120,720,720)
original=Project.load(ROOT/'projects/S5_Studio_Ritaglio_0.7.s5faceproj')
assert p.assets[e.asset]==original.assets[e.asset]
expected,x,y=canvas_image(p,e)
fprj=ET.parse(latest.parent/'sorgenti-easyface/quadrante.fprj').getroot()
widget=next(w for w in fprj.find('Screen').findall('Widget') if w.get('Bitmap') and w.get('Name','').endswith(e.id))
with Image.open(latest.parent/'sorgenti-easyface/images'/widget.get('Bitmap')) as im:
    assert im.convert('RGBA').tobytes()==expected.tobytes()
bitmap_count=0
data=(latest.parent/'resource.bin').read_bytes()
for screen in range(data[28]):
    tables=read_tables(data,screen)
    for uid,_,payload in tables[2]+tables[3]:
        w,h=struct.unpack_from('<HH',payload,4)
        assert 1<=w<=480 and 1<=h<=480
        bitmap_count+=1
with zipfile.ZipFile(next(latest.parent.glob('*_TEMPLATE.zip'))) as z:
    manifest=ET.fromstring(z.read('resources/manifest.xml'))
    assert all(0<=int(n.get('x'))<480 and 0<=int(n.get('y'))<480 for n in manifest.iter('Layout'))

# Existing in-bounds designs must retain the previously verified native payload.
run('build',ROOT/'projects/S5_Studio_Crono_0.6.s5faceproj','--compiler',
    ROOT/'tools/easyface-4.23/Compiler.exe','--output',output/'regression-0.6')
reg=max((output/'regression-0.6').glob('*/build-report.json'),key=lambda p:p.stat().st_mtime)
regression=json.loads(reg.read_text(encoding='utf8'))
prior=json.loads((ROOT/'docs/S5-Studio-Crono-0.6-build-report.json').read_text(encoding='utf8'))
assert regression['binary']['sha256']==prior['binary']['sha256']
stress=max((ROOT/'build/stress-0.5').glob('*/*_TEMPLATE.zip'),key=lambda p:p.stat().st_mtime)
run('validate-template',ROOT/'quadrante_funzionante.zip',stress,'--report',ROOT/'docs/executable-stress-validation-0.7.json')
assert json.loads((ROOT/'docs/executable-stress-validation-0.7.json').read_text(encoding='utf8'))['status']=='passed'
summary={'status':'passed','date':'2026-10-07','executable':exe.name,
         'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'embeddedFrontendIdentical':embedded,
         'ui':ui['checks'],'sourceAndExecutableBinaryIdentical':True,'binarySha256':report['binary']['sha256'],
         'imageGeometryPreserved':[-120,-120,720,720],'visibleExportWindow':[480,480],
         'compiledBitmapCountWithin480':bitmap_count,'originalImportedAssetPreserved':True,
         'prior06BinaryUnchanged':True,'prior06BinarySha256':regression['binary']['sha256'],
         'screenCount':10,'simultaneousSlots':5,'nativeSlotInstances':25,
         'all58SourcesPerSlotValidation':'passed','hardwareTested':False,'buildReport':str(latest)}
(ROOT/'docs/executable-build-0.7.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
