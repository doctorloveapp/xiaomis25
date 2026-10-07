from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from s5studio.model import template, Element
from s5studio.render import render,png_bytes
from s5studio.native import build,inspect_mwz

root=Path(__file__).resolve().parents[1]
examples=root/'projects'
examples.mkdir(exist_ok=True)
for name,id in [('Digitale','562800101'),('Analogico','562800102'),('Salute','562800103')]:
    p=template(name)
    p.face_id=id
    p.save(examples/f'{name}.s5faceproj',png_bytes(render(p)))
    build(p,root/'tools/easyface-4.23/Compiler.exe',root/'dist',print)
p=template()
p.face_id='562800104'
p.name='S5 Digitale AOD'
p.aod_enabled=True
p.elements.extend([Element(kind='clock',name='Ora AOD',aod=True,x=95,y=190,width=290,height=75,size=64),
                   Element(kind='date',name='Data AOD',aod=True,x=166,y=282,width=148,height=34,size=26,color='#808080')])
p.save(examples/'Digitale_AOD.s5faceproj',png_bytes(render(p)))
build(p,root/'tools/easyface-4.23/Compiler.exe',root/'dist',print)
(root/'docs/reference-package-report.json').write_text(json.dumps(inspect_mwz(root/'S5_Custom_digital_original.mwz'),ensure_ascii=False,indent=2),encoding='utf-8')
toolchain={'version':'EasyFace 4.23','source':'https://github.com/m0tral/EasyFace/releases/tag/v4.23',
           'releaseArchiveSha256':hashlib.sha256((root/'tools/EasyFace_Gen2_CompilerV423.zip').read_bytes()).hexdigest(),
           'compilerSha256':hashlib.sha256((root/'tools/easyface-4.23/Compiler.exe').read_bytes()).hexdigest(),
           'target':562,'compilerModel':'MiWatchS5','hardwareVerified':False}
(root/'tools/toolchain.json').write_text(json.dumps(toolchain,indent=2),encoding='utf-8')
print('4 progetti e 4 build reali pronti; campione originale preservato.')
