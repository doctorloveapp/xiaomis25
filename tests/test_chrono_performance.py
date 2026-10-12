"""Run the exported Lua through frame callbacks, including the S5 clock fallback."""
from dataclasses import replace
import xml.etree.ElementTree as ET
import pytest
from s5studio.chrono_pro import ProPreview
from s5studio.native import generate_fprj
from test_chrono_pro import pro_project, pro_runtime, start, view
from test_chrono_post import post_project


def frame_start(lua, core, fallback):
    if not fallback:
        start(lua, core)
        return
    core.tap(core)
    core.clockAnimation.exec_cb(core.root, 0)
    core.clockAnimation.exec_cb(core.root, 720)
    core.progress(core, 1000)
    core.tapUnlockAnimation.exec_cb(core.root, 1000)
    core.tap(core)
    core.clockAnimation.exec_cb(core.root, 0)
    assert core.state == 'running'


@pytest.mark.parametrize('fallback', [False, True])
@pytest.mark.parametrize('smooth', [False, True])
def test_clock_callback_updates_all_decisecond_positions_without_polling(tmp_path, fallback, smooth):
    p = pro_project()
    next(e for e in p.elements if e.source == 'studioChronoDecisecond').smooth_seconds = smooth
    _, lua, core = pro_runtime(tmp_path, project=p, fallback=fallback)
    frame_start(lua, core, fallback)
    assert core.runTimer.paused and core.restTimer.paused
    small = view(core, 'studioChronoDecisecond')
    main = view(core, 'studioIntegratedSecond')
    # Anchor the first frame; later frames must use clock time, not their count.
    core.clockAnimation.exec_cb(core.root, 0)
    initial = small.hands[1].writes
    main_initial = main.hands[1].writes
    values = []
    for elapsed in range(40, 1001, 40):
        lua.globals().TICK = core.started + elapsed
        # Direct mode must ignore animation phase as a clock origin.
        phase = elapsed if fallback else elapsed + 17000
        core.clockAnimation.exec_cb(core.root, phase)
        values.append(small.last)
        written = small.hands[1].writes
        core.clockAnimation.exec_cb(core.root, phase)
        assert small.hands[1].writes == written  # write-on-change / duplicate callback
    assert small.hands[1].writes - initial == (25 if smooth else 10)
    assert main.hands[1].writes - main_initial == 1
    if smooth:
        assert values[:3] == pytest.approx([.4, .8, 1.2])
    else:
        assert set(values) >= set(range(10))
    assert small.last == 0 and main.last == 1
    assert core.elapsed == 1000


def test_mixed_smooth_and_stepped_views_preview_stop_and_post_share_one_time(tmp_path):
    p = post_project()
    small = next(e for e in p.elements if e.source == 'studioChronoDecisecond')
    small.smooth_seconds = True
    stepped = replace(small, id='0123456789ab', smooth_seconds=False)
    p.elements.insert(p.elements.index(small) + 1, stepped)
    _, lua, core = pro_runtime(tmp_path, project=p)
    start(lua, core)
    preview = ProPreview()
    preview.tap(p, 0, 47); preview.values(p, 720, 47); preview.tap(p, 800, 47)
    for elapsed in (40, 80, 120, 456, 1000, 3661456):
        lua.globals().TICK = core.started + elapsed
        core.clockAnimation.exec_cb(core.root, elapsed % 60000)
        values = preview.values(p, 800 + elapsed, 47)
        for _, v in core.views.items():
            if v.source.startswith('studioTime'): continue
            assert v.last == pytest.approx(values[v.id], abs=.001)
    core.tap(core); preview.tap(p, 800 + 3661456, 47)
    assert core.state == 'reading' and core.elapsed == 3661456
    assert view(core, 'studioChronoDecisecond').last == pytest.approx(4.56)
    assert next(v for _, v in core.views.items() if v.id == stepped.id).last == 4
    core.progress(core, 1000)
    assert view(core, 'studioChronoCentisecond').last == 45
    assert view(core, 'studioChronoMillisecond').last == 456
    assert core.state == 'stopped' and not core.clockAnimation.run
    frozen = {v.id: v.last for _, v in core.views.items()}
    lua.globals().TICK += 5000
    core.clockAnimation.exec_cb(core.root, 5000)
    assert {v.id: v.last for _, v in core.views.items()} == frozen


@pytest.mark.parametrize('fallback', [False, True])
def test_smooth_callback_stops_immediately_in_aod_and_deleted_scene(tmp_path, fallback):
    p = pro_project()
    next(e for e in p.elements if e.source == 'studioChronoDecisecond').smooth_seconds = True
    _, lua, core = pro_runtime(tmp_path, project=p, fallback=fallback)
    frame_start(lua, core, fallback)
    old_animation = core.clockAnimation
    old_root = core.root
    lua.globals().ScreenStateChangedCB('ON', 'AOD', 0)
    assert not old_animation.run and core.runTimer.paused and core.restTimer.paused
    writes = {v.id: v.hands[1].writes for _, v in core.views.items()}
    old_animation.exec_cb(old_root, 59999)
    assert {v.id: v.hands[1].writes for _, v in core.views.items()} == writes
    lua.globals().ScreenStateChangedCB('AOD', 'ON', 0)
    assert core.clockAnimation.run and core.state == 'running'
    old_root.events[5]()
    assert not old_animation.run
    old_animation.exec_cb(old_root, 60000)
    assert not core.active and len(core.views) == 0


@pytest.mark.parametrize('pro', [False, True])
@pytest.mark.parametrize('ticks', [False, True])
def test_hidden_ticks_are_absent_from_native_and_pro_resources(tmp_path, pro, ticks):
    p = pro_project()
    main = next(e for e in p.elements if e.kind == 'analog')
    main.chrono_pro = pro; main.show_ticks = ticks
    for e in p.elements:
        if e.kind == 'analog': e.show_ticks = ticks
    if not pro:
        p.elements = [main]
    source = generate_fprj(p, tmp_path)
    files = list(tmp_path.rglob('*_ticks.png'))
    assert bool(files) == ticks
    code = (tmp_path/'app/lua/studio_v0_scene.lua').read_text(encoding='utf8') if pro else ''
    xml = ET.tostring(ET.parse(source.project_path).getroot()).decode()
    assert ('_ticks.png' in code + xml) == ticks
    if ticks:
        from PIL import Image
        assert all(Image.open(path).getchannel('A').getbbox() is not None for path in files)
    else:
        assert not any('_ticks' in w.get('Name', '') for w in ET.parse(source.project_path).iter('Widget'))
