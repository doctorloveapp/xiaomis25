"""Five real mother hand sets, paired shadows and endpoint-based subdials."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from s5studio.model import Project
from s5studio.hand_presets import preset_changes
from s5studio.watchface_library import library
from s5studio.render import render,png_bytes

p=Project.load(ROOT/'projects/S5_Studio_Ritaglio_0.7.s5faceproj')
p.name='S5 Studio Lancette';p.face_id='708008001'
hands=library()['hands'];analog=next(e for e in p.elements if e.kind=='analog' and not e.aod)
analog.x=analog.y=0;analog.width=analog.height=480;analog.show_ticks=False
choices=[];seen=set()
for item in hands:
    if item['name']=='Suit and tie' and item['hand']=='hour' and item['shadow'] and not item['aod'] and item['sourceSha256'] not in seen:
        choices.append(item);seen.add(item['sourceSha256'])
for item in hands:
    if len(choices)>=5:break
    if item['hand']=='hour' and not item['small'] and item['shadow'] and not item['aod'] and len(item['setMembers'])==3 and item['sourceSha256'] not in seen:
        choices.append(item);seen.add(item['sourceSha256'])
assert len(choices)>=5
for h in ('hour','minute','second'):setattr(analog,h+'_color','')
for k,v in preset_changes(p,analog,ROOT,choices[0],'hour',hands).items():setattr(analog,k,v)
for i,variant in enumerate(p.variants):
    variant['name']=f'Set {i+1}';variant['overrides']={analog.id:preset_changes(p,analog,ROOT,choices[i],'hour',hands)}
small=[m for m in hands if m['small'] and m['shadow'] and not m['aod']]
for i,e in enumerate(e for e in p.elements if e.kind=='pointer'):
    e.second_color='';e.pointer_end_pivot=True
    for k,v in preset_changes(p,e,ROOT,small[i*3],'second',hands).items():setattr(e,k,v)
path=ROOT/'projects/S5_Studio_Lancette_0.8.s5faceproj'
p.save(path,png_bytes(render(p.variant_project(0))))
for i in range(5):
    (ROOT/f'docs/screenshots/S5-Studio-Lancette-0.8-{i+1}.png').write_bytes(png_bytes(render(p.variant_project(i))))
print(path)
