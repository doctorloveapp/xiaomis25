"""Check embedded file hashes without launching or isolating the executable."""
import argparse
import hashlib
import json
from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader


def verify(executable):
    archive=CArchiveReader(str(executable))
    entries={name.replace('\\','/'):name for name in archive.toc}
    manifest=json.loads(archive.extract(entries['runtime-manifest.json']))
    for name,digest in manifest['files'].items():
        if name not in entries or hashlib.sha256(archive.extract(entries[name])).hexdigest()!=digest:
            raise ValueError('Risorsa incorporata mancante o alterata: '+name)
    if any(n.startswith(('projects/','quadranti/','data/recovery','data/hardware-tests')) or
           n.lower().endswith(('adb.exe','easyface_en.exe')) for n in entries):
        raise ValueError('Risorsa personale o tool di deployment incluso per errore.')
    return {'status':'passed','applicationVersion':manifest['applicationVersion'],
            'embeddedFilesVerified':len(manifest['files']),
            'exeSize':executable.stat().st_size,'exeSha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'executableLaunched':False,'isolatedEnvironmentTested':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path);parser.add_argument('--report',type=Path)
    args=parser.parse_args();result=verify(args.executable)
    if args.report:args.report.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
