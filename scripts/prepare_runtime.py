"""Stage this user's complete offline runtime, excluding projects and recovery."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.native import compiler_probe
from s5studio.template_package import resolve_template


def prepare():
    library_path=ROOT/'data/watchface-library.json'
    if not library_path.is_file():raise ValueError('Libreria personale assente: esegui scripts/create_watchface_library.py con il corpus quadranti disponibile.')
    library=json.loads(library_path.read_text(encoding='utf8'))
    if len(library.get('hands',[]))!=595 or not library.get('compasses') or library.get('errors'):
        raise ValueError('Catalogo incompleto: rigenera la libreria e il catalogo bussole prima di confezionare.')
    compiler_probe(ROOT/'tools/easyface-4.23/Compiler.exe')
    template=resolve_template()
    files={}
    def add(name,digest=None):
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Risorsa mancante o fuori dal progetto: '+str(name))
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest and digest!=actual:raise ValueError('Hash risorsa alterato: '+str(name))
        files[path.relative_to(ROOT).as_posix()]=actual
    add(library_path.relative_to(ROOT))
    for item in library['hands']:
        add(item['assetPath'],item['sourceSha256'])
        if item['shadow']:add(item['shadow']['assetPath'],item['shadow']['sourceSha256'])
    for item in library['compasses']:add(item['assetPath'],item['sourceSha256'])
    for item in library['weatherIcons'].values():add(item['path'],item['sha256'])
    for name in ['Compiler.exe','DeviceInfo.db']:add('tools/easyface-4.23/'+name)
    add('tools/toolchain.json');add(template.relative_to(ROOT));add('THIRD_PARTY_NOTICES.md');add('LICENSE')
    for name in ['index.html','app.js','editor-controls.js','editor-precision.js','editor-multi.js','studio.css','tailwind.css']:add('frontend/'+name)
    add('s5studio/lua/studio_core.lua');add('s5studio/lua/studio_core_pro.lua')
    for path in (ROOT/'licenses').rglob('*'):
        if path.is_file():add(path.relative_to(ROOT))
    target=(ROOT/'build/runtime-1.3').resolve()
    assert target.parent==(ROOT/'build').resolve() and target.is_relative_to(ROOT)
    if target.exists():
        if not (target/'runtime-manifest.json').is_file():raise ValueError('Cartella runtime preesistente non riconosciuta; nessun file viene eliminato.')
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for name in files:
        output=target/name;output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,output)
    report={'applicationVersion':'1.3','scope':'personal-offline-runtime-from-user-provided-corpus',
            'hands':len(library['hands']),'compasses':len(library['compasses']),
            'sources':len(library['sources']),'weatherIcons':len(library['weatherIcons']),
            'compilerFramework':'.NET Framework 4.7.2 or later','files':files,
            'excluded':['projects','recovery','hardware-test-projects','original-watchface-corpus','ADB','EasyFace editor']}
    (target/'runtime-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    (ROOT/'docs/runtime-manifest-1.3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'directory':str(target),'files':len(files),'hands':report['hands'],'compasses':report['compasses']},indent=2))
    return target


if __name__=='__main__':prepare()
