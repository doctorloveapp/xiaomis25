"""The distribution may include Bulova, but no other personal documents."""
import hashlib
import json
from types import SimpleNamespace
import pytest
from scripts import verify_bundle


def archive(monkeypatch,tmp_path,extra=None):
    example='resources/examples/Bulova.s5faceproj'
    payloads={example:b'example'}
    if extra:payloads[extra]=b'not authorized'
    manifest={'applicationVersion':'2.8','exampleProjects':[example],
              'files':{name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}}
    payloads['runtime-manifest.json']=json.dumps(manifest).encode()
    monkeypatch.setattr(verify_bundle,'CArchiveReader',lambda _:SimpleNamespace(toc=dict.fromkeys(payloads),extract=payloads.__getitem__))
    exe=tmp_path/'S5Studio-2.8.exe';exe.write_bytes(b'unit fixture')
    return exe


def test_only_authorized_bulova_example_is_accepted(monkeypatch,tmp_path):
    report=verify_bundle.verify(archive(monkeypatch,tmp_path))
    assert report['bundledExampleProjects']==['resources/examples/Bulova.s5faceproj']
    assert not report['personalPreferencesIncluded'] and not report['executableLaunched']


@pytest.mark.parametrize('extra',[
    'projects/Secret.s5faceproj','other/Private.s5faceproj','resources/examples/NASA.s5faceproj',
    'resources/Private.fprj','data/settings.json','profile/dialog-paths.json','cache/recovery-web.s5faceproj'])
def test_personal_projects_preferences_and_recovery_are_rejected(monkeypatch,tmp_path,extra):
    with pytest.raises(ValueError):verify_bundle.verify(archive(monkeypatch,tmp_path,extra))
