"""Create local release archives for personal use, with user-derived preset assets but without the toolchain."""
from pathlib import Path
import hashlib,json,zipfile

root=Path(__file__).resolve().parents[1]
output=root/'deliverables'
output.mkdir(exist_ok=True)
source_roots=['s5studio','scripts','tests','licenses','projects','docs','data/hardware-tests','data/hand-presets','data/weather-presets']
source_files=['main.py','.gitignore','README.md','LICENSE','THIRD_PARTY_NOTICES.md','requirements.txt',
              'requirements-dev.txt','pytest.ini','Avvia_S5_Studio.cmd',
              'Piano_tecnico_Xiaomi_Watch_S5.md','tools/download-toolchain.ps1','tools/toolchain.json','data/template-defaults.json','data/watchface-library.json']
source_files += ['frontend/index.html','frontend/app.js','frontend/editor-controls.js','frontend/studio.css','frontend/tailwind.css','frontend/input.css','frontend/package.json','frontend/package-lock.json']
files=[root/f for f in source_files]
for folder in source_roots:
    files += [p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.tmp'}]
for title,include_exe in [('S5Studio-0.8-sorgenti.zip',False),('S5Studio-0.8-Windows-portabile.zip',True)]:
    with zipfile.ZipFile(output/title,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(files)):
            z.write(p,p.relative_to(root).as_posix())
        if include_exe:
            z.write(root/'S5Studio-0.8.exe','S5Studio-0.8.exe')
    with zipfile.ZipFile(output/title) as z:
        assert z.testzip() is None
        assert not any('Compiler.exe' in n or 'S5_Custom_digital_original.mwz' in n for n in z.namelist())
manifest={'version':'0.8.0','hardwareVerified':False,'priorDigitalBuildHardwareSuccessReported':True,'analog05HardwareSuccessReported':True,'analog05Evidence':'data/hardware-tests/analogico-05-superato.json','templateRequired':'quadrante_funzionante.zip (file locale fornito dall’utente, non incluso negli archivi)',
          'analog04HardwareTestFailed':True,'sourcesObserved':58,'handPresets':595,'smallHandPresets':108,'modelsWithShadows':407,'uniqueMotherBitmaps':526,'userDerivedAssets':'Librerie personali dai quadranti forniti: diritti dei rispettivi autori, non una licenza di redistribuzione.',
          'validationReport':'docs/validation-editor-0.8.json','executableValidation':'docs/executable-build-0.8.json','pytestPassed':65,'date':'2026-10-07',
          'artifacts':{p.name:{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [root/'S5Studio-0.8.exe',root/'S5_Studio_Lancette_0.8_TEMPLATE.zip',output/'S5Studio-0.8-sorgenti.zip',output/'S5Studio-0.8-Windows-portabile.zip']}}
(output/'manifest-0.8.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
