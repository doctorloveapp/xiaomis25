"""Generate a repeatable, user-reviewable analog + styles + slots test build."""
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.model import template
from s5studio.native import build,sha256
from s5studio.render import png_bytes,render
from s5studio.template_package import validate_template_output

p=template('Analogico');p.name='S5 Analogico Varianti'
p.elements=[e for e in p.elements if e.aod or e.kind=='analog']
p.variants=[{'id':f'stile_{i+1}','name':name,'accent':color,'background':'','imageAsset':'','overrides':{}}
            for i,(name,color) in enumerate([('Menta','#6ce5c1'),('Blu','#5f87ff'),('Oro','#e8bb65'),('Viola','#d992fc'),('Bianco','#ffffff')])]
options=['none','calories','steps','spo2','sleep','movement']
p.complications=[{'id':'right','name':'Destra','x':269,'y':160,'options':options,'default':'steps'},
                 {'id':'left','name':'Sinistra','x':53,'y':160,'options':options,'default':'calories'}]
project=ROOT/'projects/Analogico_varianti_complicazioni.s5faceproj';p.save(project,png_bytes(render(p.variant_project())))
folder=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',ROOT/'test_upload',print)
report=json.loads((folder/'build-report.json').read_text(encoding='utf-8'))
package=folder/report['templatePackage']['filename']
alias=ROOT/'S5_Analogico_Varianti_TEMPLATE.zip';shutil.copyfile(package,alias)
validation=validate_template_output(ROOT/'quadrante_funzionante.zip',alias)
validation.update(project=str(project),buildDirectory=str(folder),testPackage=str(alias),variants=5,complicationSlots=2,
                  hardwareTested=False,uiVersion='0.4.0')
(ROOT/'docs/editable-first-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(alias,sha256(alias.read_bytes()))
