"""Prepare a minimal, real-compiled S5 uploader test without touching user projects."""
from pathlib import Path
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.model import template
from s5studio.render import render,png_bytes
from s5studio.native import build
from s5studio.template_package import validate_template_output,resolve_template,default_project_values

p=template('Digitale')
project=ROOT/'projects/Primo_test_template.s5faceproj'
p.save(project,png_bytes(render(p)))
folder=build(p,ROOT/'tools/easyface-4.23/Compiler.exe',ROOT/'test_upload',print)
package=next(folder.glob('*_TEMPLATE.zip'))
target=ROOT/'S5_Primo_Test_TEMPLATE.zip'
shutil.copy2(package,target)
report=validate_template_output(resolve_template(),target)
(ROOT/'docs/local-test-package-0.3.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'data/template-defaults.json').write_text(json.dumps(default_project_values(),ensure_ascii=False,indent=2),encoding='utf-8')
print(target)
