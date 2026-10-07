"""Check the packaged application using CLI commands without opening a user session."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.template_package import validate_template_output

exe=ROOT/'S5Studio-0.4.exe'
self_report=ROOT/'docs/executable-self-test-0.4.json'
screenshot=ROOT/'docs/screenshots/executable-0.4.png'
destination=ROOT/'build/executable-0.4-test'
commands=[
    ['self-test','--report',str(self_report)],
    ['ui-smoke','--screenshot',str(screenshot)],
    ['template-info','--report',str(ROOT/'docs/template-build-profile.json')],
    ['build',str(ROOT/'projects/Analogico_varianti_complicazioni.s5faceproj'),'--compiler',str(ROOT/'tools/easyface-4.23/Compiler.exe'),'--output',str(destination)],
]
for args in commands:
    subprocess.run([str(exe),*args],cwd=ROOT,check=True,timeout=120)
assert json.loads(self_report.read_text())['status']=='passed'
assert screenshot.exists() and screenshot.stat().st_size>1000
folders=sorted(destination.iterdir(),key=lambda p:p.stat().st_mtime)
report=json.loads((folders[-1]/'build-report.json').read_text(encoding='utf-8'))
package=folders[-1]/report['templatePackage']['filename']
checked=validate_template_output(ROOT/'quadrante_funzionante.zip',package)
assert checked['binary']['faceId']=='120917386745' and checked['binary']['screenCount']==10 and checked['binary']['nativeSlots']==10
(ROOT/'docs/executable-build-test-0.4.json').write_text(json.dumps({'status':'passed','package':checked,'build':str(folders[-1])},ensure_ascii=False,indent=2),encoding='utf-8')
print('EXE 0.4: self-test, WebEngine/Tailwind, default e cinque analogici con slot compilati; nuova prova hardware necessaria.')
