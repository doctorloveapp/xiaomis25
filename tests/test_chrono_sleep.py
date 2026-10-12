"""AOD notification order must not discard hours from the animation clock."""
import pytest
import hashlib
from io import BytesIO
from PIL import Image
from test_chrono_post import post_project
from test_chrono_pro import pro_runtime, view
from test_chrono_performance import frame_start


def shared_hand_project():
    p = post_project()
    raw = BytesIO()
    Image.new('RGBA', (8, 42), (80, 150, 220, 255)).save(raw, 'PNG')
    data = raw.getvalue()
    key = 'assets/' + hashlib.sha256(data).hexdigest()[:24] + '.png'
    p.assets[key] = data
    for e in p.elements:
        if e.source in ('studioChronoHour', 'studioChronoMinute'):
            e.second_asset = key
            e.second_anchor_x = 4
            e.second_anchor_y = 38
            e.second_shadow_asset = key
            e.second_shadow_anchor_x = 4
            e.second_shadow_anchor_y = 38
            e.show_shadows = True
    return p


@pytest.mark.parametrize('smooth', [False, True])
@pytest.mark.parametrize('event_order', [
    'screen-only', 'resume-before-screen-on', 'repeated-aod',
    'pause-while-aod', 'resume-while-aod', 'repeated-on',
])
def test_one_hour_aod_preserves_start_across_lifecycle_notifications(tmp_path, smooth, event_order):
    p = post_project()
    next(e for e in p.elements if e.source == 'studioChronoDecisecond').smooth_seconds = smooth
    _, lua, core = pro_runtime(tmp_path, project=p, fallback=True)
    frame_start(lua, core, True)
    core.clockAnimation.exec_cb(core.root, 31456)
    assert core.elapsed == 31456
    lua.globals().ScreenStateChangedCB('ON', 'AOD', 0)
    baseline = core.sleepWall
    assert not core.active and not core.clockAnimation.run
    lua.globals().WALL += 1800
    if event_order == 'repeated-aod':
        lua.globals().ScreenStateChangedCB('AOD', 'AOD', 0)
    elif event_order == 'pause-while-aod':
        lua.globals().pageOnPause()
    elif event_order == 'resume-while-aod':
        lua.globals().pageOnResume()
    assert core.sleepWall == baseline
    lua.globals().WALL += 1800
    if event_order == 'resume-before-screen-on':
        lua.globals().pageOnResume()
        assert core.sleepWall == baseline and not core.active
    lua.globals().ScreenStateChangedCB('AOD', 'ON', 0)
    if event_order == 'repeated-on':
        lua.globals().ScreenStateChangedCB('ON', 'ON', 0)
        lua.globals().pageOnResume()
    assert core.active and core.state == 'running' and core.sleepWall is None
    assert core.elapsed == 3631456
    assert view(core, 'studioChronoHour').last == 1
    assert view(core, 'studioChronoHour').hands[1].value == 1000
    assert view(core, 'studioChronoMinute').last == 0
    assert view(core, 'studioIntegratedSecond').last == 31
    assert view(core, 'studioChronoDecisecond').last == pytest.approx(4.56 if smooth else 4)
    # Stop captures the restored clock once for all hands, including POST.
    core.tapUnlockAnimation.exec_cb(core.root, 1000)
    core.tap(core); assert core.state == 'reading'
    core.progress(core, 1000)
    assert core.state == 'stopped' and core.elapsed == 3631456
    assert view(core, 'studioChronoHour').last == 1
    assert view(core, 'studioChronoCentisecond').last == 45
    assert view(core, 'studioChronoMillisecond').last == 456
    core.tapUnlockAnimation.exec_cb(core.root, 1000)
    core.tap(core); assert core.state == 'resetting'
    core.progress(core, 1000)
    assert core.state == 'rest' and core.elapsed == 0
    assert view(core, 'studioChronoHour').last == 0


@pytest.mark.parametrize('fallback', [False, True])
@pytest.mark.parametrize('pause', ['aod', 'page'])
@pytest.mark.parametrize('stopped', [False, True])
def test_resume_reasserts_unchanged_hour_and_shadow_after_renderer_loses_pose(tmp_path, fallback, pause, stopped):
    _, lua, core = pro_runtime(tmp_path, project=shared_hand_project(), fallback=fallback)
    frame_start(lua, core, fallback)
    # The hour is already 1: a renderer reset must not leave it at zero until
    # the next whole hour. Minutes/seconds change sooner and can mask the issue.
    if fallback:
        core.engineTick = core.started + 3723456
    else:
        lua.globals().TICK = core.started + 3723456
    core.update(core, core.clock(core))
    if stopped:
        core.tapUnlockAnimation.exec_cb(core.root, 1000)
        core.tap(core)
        core.progress(core, 1000)
        assert core.state == 'stopped'
    hour = view(core, 'studioChronoHour')
    assert hour.last == 1
    assert len(hour.hands) == 2
    expected = {v.id: [h.value for _, h in v.hands.items()] for _, v in core.views.items()}
    if pause == 'aod':
        lua.globals().ScreenStateChangedCB('ON', 'AOD', 0)
    else:
        lua.globals().pageOnPause()
    # Fault injection in the mock renderer only; controller state stays intact.
    writes = {}
    for _, v in core.views.items():
        writes[v.id] = [h.writes for _, h in v.hands.items()]
        for _, h in v.hands.items():
            h.value = 0
    if pause == 'aod':
        lua.globals().ScreenStateChangedCB('AOD', 'ON', 0)
    else:
        lua.globals().pageOnResume()
    for _, v in core.views.items():
        assert [h.value for _, h in v.hands.items()] == expected[v.id]
        assert [h.writes for _, h in v.hands.items()] == [n + 1 for n in writes[v.id]]
    # Normal cache and duplicate-notification behaviour are still efficient.
    lua.globals().ScreenStateChangedCB('ON', 'ON', 0)
    lua.globals().pageOnResume()
    core.update(core, core.clock(core))
    for _, v in core.views.items():
        assert [h.writes for _, h in v.hands.items()] == [n + 1 for n in writes[v.id]]


@pytest.mark.parametrize('fallback', [False, True])
def test_shared_png_has_independent_hour_minute_pointers_and_rollovers(tmp_path, fallback):
    p, lua, core = pro_runtime(tmp_path, project=shared_hand_project(), fallback=fallback)
    frame_start(lua, core, fallback)
    hour = view(core, 'studioChronoHour')
    minute = view(core, 'studioChronoMinute')
    assert hour.id != minute.id
    assert len(hour.hands) == len(minute.hands) == 2
    for elapsed, hours, minutes in [
        (3599999, 0, 59), (3600000, 1, 0), (3660000, 1, 1),
        (7200000, 2, 0), (43199999, 11, 59), (43200000, 0, 0), (46800000, 1, 0),
    ]:
        if fallback:
            core.engineTick = core.started + elapsed
        else:
            lua.globals().TICK = core.started + elapsed
        core.update(core, core.clock(core))
        assert hour.last == hours and minute.last == minutes
        for v, value, angle in [(hour, hours, hours * 30), (minute, minutes, minutes * 6)]:
            for _, h in v.hands.items():
                assert h.value == value * 1000
                r = h.range
                assert (h.value - r.valueStart) * r.angleRange / r.valueRange / 10 == angle
    hour_png = (tmp_path / 'app/lua/gfx' / f'v0_{hour.id}.png').read_bytes()
    minute_png = (tmp_path / 'app/lua/gfx' / f'v0_{minute.id}.png').read_bytes()
    assert hour_png == minute_png
    original = {e.second_asset for e in p.elements if e.source in ('studioChronoHour', 'studioChronoMinute')}
    assert len(original) == 1
