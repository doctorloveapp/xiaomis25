"""Verify the actual packaged app, its UI and its watchface build output."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
exe=ROOT/'S5Studio-0.5.exe'
def run(*args,timeout=240):
    result=subprocess.run([str(exe),*map(str,args)],cwd=ROOT,capture_output=True,
                          timeout=timeout,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:
        raise RuntimeError(f'EXE failed ({result.returncode}): {args}\n'+result.stderr.decode('utf8',errors='replace')[-2000:])

run('self-test','--report',ROOT/'docs/executable-self-test-0.5.json')
assert json.loads((ROOT/'docs/executable-self-test-0.5.json').read_text())['status']=='passed'
run('ui-smoke','--screenshot',ROOT/'docs/screenshots/executable-0.5.png')
ui=json.loads((ROOT/'docs/screenshots/executable-0.5.json').read_text())
assert ui['status']=='passed' and '58-unique-sources-plus-none' in ui['checks']

output=ROOT/'build/executable-0.5'
run('build',ROOT/'projects/S5_Analogico_Libero_0.5.s5faceproj','--compiler',
    ROOT/'tools/easyface-4.23/Compiler.exe','--output',output)
reports=list(output.glob('*/build-report.json'))
latest=max(reports,key=lambda p:p.stat().st_mtime)
report=json.loads(latest.read_text(encoding='utf8'))
source=json.loads((ROOT/'docs/S5-Analogico-Libero-0.5-build-report.json').read_text(encoding='utf8'))
assert report['binary']['sha256']==source['binary']['sha256'],'The packaged app must emit the same native payload as the source app.'
assert report['templatePackage']['status']=='passed'
assert report['binary']['nativeSlots']==25 and report['binary']['screenCount']==10

# Exercise the executable's raised archive limit against the full 5×58 source build.
stress=max((ROOT/'build/stress-0.5').glob('*/*_TEMPLATE.zip'),key=lambda p:p.stat().st_mtime)
run('validate-template',ROOT/'quadrante_funzionante.zip',stress,'--report',ROOT/'docs/executable-stress-validation-0.5.json')
assert json.loads((ROOT/'docs/executable-stress-validation-0.5.json').read_text(encoding='utf8'))['status']=='passed'
summary={'status':'passed','executable':exe.name,'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
         'ui':ui['checks'],'sourceAndExecutableBinaryIdentical':True,'binarySha256':report['binary']['sha256'],
         'screenCount':10,'simultaneousSlots':5,'nativeSlotInstances':25,
         'all58SourcesPerSlotValidation':'passed','hardwareTested':False,'buildReport':str(latest)}
(ROOT/'docs/executable-build-0.5.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
print(json.dumps(summary,indent=2))
