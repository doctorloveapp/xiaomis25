"""Prove the one-file EXE works without adjacent project resources.

The only watchface builds are a temporary integration fixture and its source
comparison. No new demo project or watchface ZIP is delivered.
"""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import shutil
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PyInstaller.archive.readers import CArchiveReader
from s5studio.model import Project,Element,SOURCES
from s5studio.compass_catalog import preset_changes as compass_changes
from s5studio.hand_presets import preset_changes
from s5studio.watchface_library import library,read_tables
from s5studio.render import hand_edit_changes,hand_image
from s5studio.native import build


def verify():
    original=ROOT/'S5Studio-0.9.exe';archive=CArchiveReader(str(original))
    manifest=json.loads((ROOT/'docs/runtime-manifest-0.9.json').read_text(encoding='utf8'))
    toc={k.replace('\\','/'):k for k in archive.toc}
    for name,digest in manifest['files'].items():
        assert name in toc,'Embedded resource missing: '+name
        assert hashlib.sha256(archive.extract(toc[name])).hexdigest()==digest,name
    assert not any(n.startswith(('projects/','quadranti/','data/recovery','data/hardware-tests')) for n in toc)
    assert not any(n.lower().endswith(('adb.exe','easyface_en.exe')) for n in toc)
    report={'status':'passed','applicationVersion':'0.9','embeddedFilesVerified':len(manifest['files']),
            'exeSize':original.stat().st_size,'exeSha256':hashlib.sha256(original.read_bytes()).hexdigest(),
            'hardwareTested':False,'hardwareEvidence':'NASA 0.8 passed according to user; see nasa-migration-0.9.json',
            'standaloneFolderInitiallyContainsOnlyExe':True,'watchfaceArtifactsAreTemporary':True}
    # The final executable is copied away from the repository. cwd and PATH
    # contain no repository resources; recovery is isolated from real user data.
    temp_base=(ROOT/'build').resolve();temp_base.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='standalone-09-',dir=temp_base) as folder:
        isolated=Path(folder).resolve();assert isolated.is_relative_to(temp_base)
        executable=isolated/original.name;shutil.copyfile(original,executable)
        assert [p.name for p in isolated.iterdir()]==[executable.name]
        environment=dict(__import__('os').environ)
        environment['LOCALAPPDATA']=str(isolated/'local-user-data')
        environment['PATH']=str(Path(environment.get('WINDIR','C:/Windows'))/'System32')
        def run(*args):
            result=subprocess.run([str(executable),*map(str,args)],cwd=isolated,env=environment,
                                  capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:
                error=isolated/'local-user-data/S5Studio/cli-error.log'
                detail=error.read_text(encoding='utf8') if error.is_file() else result.stderr.decode('utf8',errors='replace')
                raise RuntimeError(str(args)+'\n'+detail)
        run('runtime-info','--report',isolated/'runtime-check.json')
        runtime=json.loads((isolated/'runtime-check.json').read_text(encoding='utf8'))
        assert runtime['status']=='passed' and runtime['frozen'] and runtime['compasses']==10 and runtime['hands']==595
        report['runtimeCheck']=runtime
        run('self-test','--report',isolated/'self-test.json')
        assert json.loads((isolated/'self-test.json').read_text())['status']=='passed'
        screenshot=isolated/'ui.png';run('ui-smoke','--screenshot',screenshot)
        ui=json.loads(screenshot.with_suffix('.json').read_text(encoding='utf8'))
        assert ui['status']=='passed'
        required={'header-Version-0.9','source-pixel-pivot-click','imported-clock-length-control-changes-bitmap',
                  'imported-clock-thickness-control-changes-bitmap','zoomed-drag-native-pixels',
                  'source-help-on-hover','compass-uses-real-sensor-counterrotation','compass-heading-simulation'}
        assert required<=set(ui['checks'])
        report['uiChecks']=ui['checks'];report['uiCheckCount']=len(ui['checks'])
        for name in ['ui.png','ui.json']:
            target=ROOT/'docs/screenshots'/('executable-0.9'+Path(name).suffix);shutil.copyfile(isolated/name,target)
        # Minimal pointer/compass regression fixture: normal + AOD, two styles.
        p=Project(name='Fixture temporanea',face_id='709009001',aod_enabled=True)
        p.variants.append({'id':'blue','name':'Blu','accent':'#719dff','background':'','imageAsset':'','overrides':{}})
        compass=Element(kind='compass',name='Bussola',x=170,y=160,width=140,height=140)
        c=next(c for c in library()['compasses'] if c['name']=='Ferrari' and c['kind']=='Rosa completa')
        for k,v in compass_changes(p,ROOT,c).items():setattr(compass,k,v)
        hands=Element(kind='analog',name='Lancette',x=60,y=60,width=360,height=360,show_ticks=False,second_hand=True)
        h=next(h for h in library()['hands'] if h['name']=='Suit and tie' and h['hand']=='hour' and h['shadow'] and not h['aod'])
        for k,v in preset_changes(p,hands,ROOT,h,'hour',library()['hands']).items():setattr(hands,k,v)
        for k,v in hand_edit_changes(hands,{'hour_length':35,'hour_width':12,'minute_length':44,'minute_width':8},p).items():setattr(hands,k,v)
        small=Element(kind='pointer',name='Lancetta piccola',x=180,y=280,width=100,height=100,source='batteryPercent',value_range=100)
        h=next(h for h in library()['hands'] if h['small'] and h['shadow'] and not h['aod'])
        for k,v in preset_changes(p,small,ROOT,h,'second',library()['hands']).items():setattr(small,k,v)
        for k,v in hand_edit_changes(small,{'second_anchor_x':h['pivot'][0],'second_anchor_y':max(0,h['pivot'][1]-2),'second_width':6},p).items():setattr(small,k,v)
        aod=replace(compass,id='a0d000000009',aod=True,x=180,y=180,width=120,height=120)
        p.elements=[hands,small,compass,aod,Element(kind='clock',name='Ora AOD',aod=True,x=100,y=350,width=280,height=60,size=40)]
        p.variants[1]['overrides']={compass.id:{'width':120,'height':120}}
        project_path=isolated/'fixture.s5faceproj';p.save(project_path)
        run('build',project_path,'--output',isolated/'compiled')  # No compiler/template option.
        frozen_report=next((isolated/'compiled').glob('*/build-report.json'))
        frozen=json.loads(frozen_report.read_text(encoding='utf8'))
        assert frozen['templatePackage']['status']=='passed' and frozen['binary']['screenCount']==4
        source_output=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',isolated/'source-comparison')
        frozen_binary=(frozen_report.parent/'resource.bin').read_bytes()
        assert frozen_binary==(source_output/'resource.bin').read_bytes()
        pointer_code=bytes.fromhex(SOURCES['systemSensorCompass'][1]);centres=[]
        for screen in range(frozen_binary[28]):
            tables=read_tables(frozen_binary,screen)
            pointer=next((uid,b) for uid,_,b in tables[7] if b[:2]==pointer_code)
            uid,descriptor=pointer
            assert struct.unpack_from('<II',descriptor,12)==(0,360<<8)
            assert struct.unpack_from('<hh',descriptor,24)==(0,-3600)
            layout=next(b for _,_,b in tables[0] if struct.unpack_from('<I',b)[0]==uid)
            centre=tuple(a+b for a,b in zip(struct.unpack_from('<hh',layout,4),struct.unpack_from('<HH',descriptor,20)))
            expected=(240,230) if screen==0 else (240,240) if screen%2 else (230,220)
            assert centre==expected,(screen,centre,expected)
            centres.append({'screen':screen,'centre':centre,'source':pointer_code.hex().upper(),'angleRange':-360})
        report.update(nativeCompassChecks=centres,compiledFixtureBinarySha256=hashlib.sha256(frozen_binary).hexdigest(),
                      frozenAndSourceBinaryIdentical=True,templateValidator='passed',standaloneCompilerWorks=True,
                      standaloneExternalCompilerOrTemplateUsed=False)
        # Invalid input must return a readable error, never a PyInstaller modal
        # which hangs automation or a user invoking the windowed EXE as CLI.
        invalid=p.copy();invalid.elements=[e for e in invalid.elements if not (e.aod and e.kind=='clock')]
        bad_path=isolated/'invalid-aod.s5faceproj';invalid.save(bad_path)
        failed=subprocess.run([str(executable),'build',str(bad_path),'--output',str(isolated/'invalid-output')],
                              cwd=isolated,env=environment,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        error=isolated/'local-user-data/S5Studio/cli-error.log'
        message=failed.stderr.decode('utf8',errors='replace')+(error.read_text(encoding='utf8') if error.is_file() else '')
        assert failed.returncode==1 and "L'AOD attivo richiede" in message
        report['cliErrorsAreReadableAndNonInteractive']=True
    target=ROOT/'docs/executable-build-0.9.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('uiChecks','runtimeCheck')},ensure_ascii=False,indent=2))


if __name__=='__main__':verify()
