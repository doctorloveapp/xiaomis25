"""Demonstrate oversized design images without oversized watch assets."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from s5studio.model import Project
from s5studio.render import render,png_bytes

p=Project.load(ROOT/'projects/S5_Studio_Crono_0.6.s5faceproj')
p.name='S5 Studio Ritaglio';p.face_id='707007001'
image=next(e for e in p.elements if e.kind=='image' and not e.aod)
image.name='Immagine 720 px (ritaglio 480)'
image.width=image.height=720;image.x=image.y=-120
path=ROOT/'projects/S5_Studio_Ritaglio_0.7.s5faceproj'
p.save(path,png_bytes(render(p.variant_project(0))))
(ROOT/'docs/screenshots/S5-Studio-Ritaglio-0.7.png').write_bytes(png_bytes(render(p.variant_project(0))))
print(path)
