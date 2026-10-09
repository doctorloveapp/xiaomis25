"""Shadows must darken lower hands, with identical native and Lua stacking."""
from dataclasses import replace
from pathlib import Path
import hashlib
import os
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw
import pytest
from s5studio.model import Element, Project
from s5studio.render import render, png_bytes, hand_image, hand_shadow_offset
from s5studio.native import generate_fprj, inspect_binary
from s5studio.native_graph import collect_nodes
from s5studio.watchface_library import read_tables
from test_motion_interaction import lua_runtime

ROOT = Path(__file__).resolve().parents[1]
ATTRS = ('HourHand_ImageName', 'MinuteHand_Image', 'SecondHand_Image')
ORDER = ['hour_shadow', 'hour', 'minute_shadow', 'minute', 'second_shadow', 'second']


def overlapping_hands(pro=False):
    project = Project(background='#e0e0e0')
    main = Element(kind='analog', x=60, y=60, width=360, height=360,
                   second_hand=True, chrono_pro=pro, show_ticks=False,
                   smooth_seconds=True)
    project.elements = [main]
    for role, left, right, colour, offset in (
        ('hour', 3, 36, (255, 255, 255, 255), 3),
        ('minute', 14, 25, (255, 0, 0, 255), 5),
        ('second', 19, 20, (0, 255, 0, 255), 3),
    ):
        for shadow in (False, True):
            bitmap = Image.new('RGBA', (40, 200))
            ImageDraw.Draw(bitmap).rectangle((left, 0, right, 179), fill=(0, 0, 0, 128) if shadow else colour)
            raw = png_bytes(bitmap)
            asset = 'assets/' + hashlib.sha256(raw).hexdigest()[:24] + '.png'
            project.assets[asset] = raw
            prefix = role + ('_shadow' if shadow else '')
            setattr(main, prefix + '_asset', asset)
            setattr(main, prefix + '_anchor_x', 20)
            setattr(main, prefix + '_anchor_y', 180)
        setattr(main, role + '_shadow_offset_x', offset)
    return project, main


@pytest.mark.parametrize('pro', [False, True])
def test_upper_shadows_darken_lower_hands_in_preview_and_style_thumbnail(tmp_path, pro):
    project, main = overlapping_hands(pro)
    image = render(project, {'hour': 0, 'minute': 0, 'second': 0}, circular=False)
    assert image.getpixel((242, 120))[:3] == (127, 0, 0)  # Seconds shadow on minutes.
    assert image.getpixel((248, 120))[:3] == (127, 127, 127)  # Minutes shadow on hours.
    assert image.getpixel((240, 120))[:3] == (0, 255, 0)  # Seconds remain on top.
    main.show_shadows = False
    unshaded = render(project, {'hour': 0, 'minute': 0, 'second': 0}, circular=False)
    assert unshaded.getpixel((242, 120))[:3] == (255, 0, 0)
    assert unshaded.getpixel((248, 120))[:3] == (255, 255, 255)
    main.show_shadows = True
    project.add_variant()
    for index in range(2):
        assert png_bytes(render(project.variant_project(index), {'hour': 0, 'minute': 0, 'second': 0}, circular=False)) == png_bytes(image)
    generate_fprj(project, tmp_path)
    with Image.open(tmp_path / 'images/thumbnail_quadrante.png') as thumbnail:
        expected = render(project.variant_project(0), circular=False).convert('RGB')
        assert thumbnail.tobytes() == expected.tobytes()


@pytest.mark.parametrize('shadows', [False, True])
def test_native_fprj_interleaves_each_shadow_and_hand_and_excludes_aod_seconds(tmp_path, shadows):
    project, main = overlapping_hands()
    main.show_shadows = shadows
    project.aod_enabled = True
    project.elements.append(replace(main, id='aodhands', aod=True, chrono_pro=False))
    source = generate_fprj(project, tmp_path)
    for path, roles in ((source.project_path, ORDER), (tmp_path / 'AOD/quadrante.fprj', ORDER[:-2])):
        widgets = [w for w in ET.parse(path).iter('Widget') if w.get('Shape') == '27']
        names = [next(w.get(a) for a in ATTRS if w.get(a)) for w in widgets]
        expected = [r for r in roles if shadows or not r.endswith('_shadow')]
        assert len(names) == len(expected)
        assert all(name.endswith('_' + role + '.png') for name, role in zip(names, expected))
        assert all(sum(bool(w.get(a)) for a in ATTRS) == 1 for w in widgets)
        assert all('_smooth[40]' not in w.get('Name') for w in widgets if not w.get('SecondHand_Image'))


def test_actual_pro_scene_creates_interleaved_pointer_children(tmp_path):
    project, main = overlapping_hands(pro=True)
    source = generate_fprj(project, tmp_path)
    lua, _ = lua_runtime()
    lua.execute('package.preload.dataman=function()return {subscribe=function()end}end')
    core = lua.execute((ROOT / 's5studio/lua/studio_core_pro.lua').read_text(encoding='utf8'))
    lua.globals().PRO = core
    lua.execute('package.loaded.studio_core_pro=PRO')
    scene = source.project_path.parent / ('app/lua/studio_v0_scene.lua')
    lua.execute(scene.read_text(encoding='utf8'))
    views = [v for _, v in core.views.items()]
    children = [v for _, v in views[0].root.children.items()]
    assert [Path(v.src).name for v in children] == ['v0_' + main.id + '_' + role + '.png' for role in ORDER]
    assert all(len(v.hands) == 2 for v in views)
    assert [v.source for v in views] == ['studioTimeHour', 'studioTimeMinute', 'studioIntegratedSecond']


def test_real_compiler_preserves_stack_centres_sources_and_periods(tmp_path):
    """A temporary binary only: no demo ZIP or packaged Studio executable."""
    project, main = overlapping_hands()
    project.aod_enabled = True
    aod = replace(main, id='aodhands', aod=True, chrono_pro=False)
    project.elements.append(aod)
    source = generate_fprj(project, tmp_path / 'source')
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    for name in ('Compiler.exe', 'DeviceInfo.db'):
        shutil.copy2(ROOT / 'tools/easyface-4.23' / name, runtime / name)
    output = tmp_path / 'compiled'
    output.mkdir()
    env = dict(os.environ)
    env['PATH'] = str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'System32')
    result = subprocess.run([str(runtime / 'Compiler.exe'), '-b', str(source.project_path), str(output), 'stack.face', '167210065'],
                            cwd=runtime, env=env, capture_output=True, stdin=subprocess.DEVNULL, timeout=30,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0 and b'No Errors' in result.stdout + result.stderr
    data = (output / 'stack.face').read_bytes()
    assert inspect_binary(data)['screenCount'] == 2
    for screen, element, roles, path in (
        (0, main, ORDER, source.project_path),
        (1, aod, ORDER[:-2], tmp_path / 'source/AOD/quadrante.fprj'),
    ):
        tables = read_tables(data, screen)
        descriptors = {uid: b for uid, _, b in tables[7]}
        nodes = collect_nodes(data, screen, path)
        pointers = [(uid, b, descriptors[uid]) for _, _, b in tables[0]
                    if (uid := struct.unpack_from('<I', b)[0]) in descriptors]
        assert len(pointers) == len(roles)
        for (uid, layout, descriptor), role in zip(pointers, roles):
            hand, _, shadow = role.partition('_')
            expected_source = {'hour': '0811', 'minute': '1011', 'second': '1811'}[hand]
            assert descriptor[:2].hex() == expected_source
            assert struct.unpack_from('<H', descriptor, 6)[0] == (40 if hand == 'second' else 1000)
            bitmap, pivot = hand_image(element, hand, project, shadow=bool(shadow))
            assert struct.unpack_from('<HH', descriptor, 20) == pivot
            dx, dy = hand_shadow_offset(element, hand, project) if shadow else (0, 0)
            x, y = struct.unpack_from('<hh', layout, 4)
            assert (x + pivot[0], y + pivot[1]) == (240 + dx, 240 + dy)
            image_uid = struct.unpack_from('<I', descriptor, 8)[0]
            assert nodes[image_uid]['bitmap'] == png_bytes(bitmap)
