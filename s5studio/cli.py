"""Automation entry point for reproducible build and package inspection."""
from pathlib import Path
import argparse
import json
import sys

from .model import Project, template
from .render import render, png_bytes, layout_errors
from .native import build, inspect_mwz, inspect_binary
from .paths import default_compiler


def run(argv):
    # Windows redirected stdout defaults to a legacy code page. ZIP metadata
    # includes Chinese/Unicode names; CLI JSON must remain printable as UTF-8.
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='backslashreplace')
    parser=argparse.ArgumentParser(prog='S5Studio',description='Editor e compilatore di quadranti Xiaomi Watch S5')
    sub=parser.add_subparsers(dest='command',required=True)
    check=sub.add_parser('inspect',help='Controlla un MWZ o binario')
    check.add_argument('path',type=Path)
    comp=sub.add_parser('build',help='Compila un progetto S5 Studio')
    comp.add_argument('project',type=Path)
    comp.add_argument('--compiler',type=Path,default=default_compiler())
    comp.add_argument('--output',type=Path,default=Path('dist'))
    comp.add_argument('--template',type=Path,help='Template ZIP; predefinito: quadrante_funzionante.zip verificato')
    surgery=sub.add_parser('apply-template',help='Compila FPRJ/progetto Studio, rigenera i metadati e preserva i record protetti del template ZIP')
    surgery.add_argument('project',type=Path)
    surgery.add_argument('template',type=Path)
    surgery.add_argument('output_dir',type=Path)
    surgery.add_argument('--compiler',type=Path)
    validator=sub.add_parser('validate-template',help='Verifica firma strutturale e file preservati di un ZIP esportato')
    validator.add_argument('template',type=Path)
    validator.add_argument('output',type=Path)
    validator.add_argument('--report',type=Path)
    info=sub.add_parser('template-info',help='Controlla il template predefinito e mostra tutti i default ricavati dal ZIP')
    info.add_argument('--report',type=Path)
    picture=sub.add_parser('render',help='Genera una preview PNG')
    picture.add_argument('project',type=Path)
    picture.add_argument('output',type=Path)
    picture.add_argument('--aod',action='store_true')
    picture.add_argument('--variant',type=int,default=0,help='Indice stile da 0 a 4 (AOD comune: stile 0)')
    selftest=sub.add_parser('self-test',help='Prova i modelli incorporati senza usare hardware o compilatore')
    selftest.add_argument('--report',type=Path)
    runtime=sub.add_parser('runtime-info',help='Verifica tutte le risorse incorporate dell’eseguibile personale')
    runtime.add_argument('--report',type=Path)
    sub.add_parser('legacy-ui',help='Apri il precedente editor Qt')
    gui=sub.add_parser('ui-smoke',help='Prova Qt fuori schermo e salva una schermata')
    gui.add_argument('--screenshot',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.command=='runtime-info':
        from .paths import resource_root
        import hashlib
        root=resource_root();manifest=json.loads((root/'runtime-manifest.json').read_text(encoding='utf8'))
        for name,digest in manifest['files'].items():
            path=(root/name).resolve()
            if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('Risorsa incorporata mancante o alterata: '+name)
        result={k:v for k,v in manifest.items() if k!='files'}
        result.update(status='passed',checkedFiles=len(manifest['files']),frozen=bool(getattr(sys,'frozen',False)))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        return 0
    if args.command=='legacy-ui':
        from .ui import launch
        return launch()
    if args.command=='inspect':
        result=inspect_mwz(args.path) if args.path.suffix.lower() in {'.mwz','.zip'} else inspect_binary(args.path.read_bytes())
        print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.command=='build':
        print(build(Project.load(args.project),args.compiler.resolve(),args.output,print,template_path=args.template))
    elif args.command=='apply-template':
        from .template_package import compile_and_apply_template,resolve_template
        compiler=args.compiler or default_compiler()
        print(compile_and_apply_template(args.project,args.template,args.output_dir,compiler.resolve()))
    elif args.command=='validate-template':
        from .template_package import validate_template_output
        result=validate_template_output(args.template,args.output)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    elif args.command=='template-info':
        from .template_package import resolve_template,template_profile,default_project_values
        result={'profile':template_profile(resolve_template()),'defaults':default_project_values()}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    elif args.command=='render':
        project=Project.load(args.project)
        if not 0<=args.variant<len(project.variants):raise ValueError('Indice variante fuori dai limiti.')
        args.output.write_bytes(png_bytes(render(project.variant_project(0 if args.aod else args.variant),aod=args.aod)))
        print(args.output)
    elif args.command=='ui-smoke':
        from .web_smoke import smoke
        smoke(args.screenshot)
    else:
        for name in ('Digitale','Analogico','Salute'):
            p=template(name)
            if p.validate() or layout_errors(p):
                raise ValueError(f'Modello non valido: {name}')
            assert render(p).size==(480,480)
        print('S5 Studio self-test: OK (3 modelli; nessuna prova hardware).')
        if args.report:
            args.report.write_text(json.dumps({'application':'S5 Studio','templates':3,'status':'passed','hardwareTested':False}),encoding='utf-8')
    return 0
