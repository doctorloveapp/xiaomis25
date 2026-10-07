"""Native seconds timing and explicit, non-sensor Lua pointer bindings."""
SWEEP_FPS = 25
SWEEP_PERIOD_MS = 1000 // SWEEP_FPS
LUA_SOURCES = {
    'studioDecisecond': ('Decimi di secondo · un giro al secondo', 10),
    'studioChronoHour': ('Ore Crono', 12),
    'studioChronoMinute': ('Minuti Crono', 60),
    'studioChronoSecond': ('Secondi Crono', 60),
}
SECOND_SOURCES = {'second', 'timeSecond', 'timeSecondLow', 'timeSecondHigh', 'studioDecisecond', 'studioChronoSecond'}


def excluded_from_aod(e):
    return e.kind == 'pointer' and (e.source in SECOND_SOURCES or e.source in LUA_SOURCES)


def pointer_period(e, aod=False):
    return SWEEP_PERIOD_MS if not aod and e.smooth_seconds and e.source in ('second', 'timeSecond') else 1000


def lua_value(source, milliseconds, smooth=False):
    if source == 'studioDecisecond': return (milliseconds % 1000) / 100 if smooth else (milliseconds % 1000) // 100
    divisor = {'studioChronoHour': 3600000, 'studioChronoMinute': 60000, 'studioChronoSecond': 1000}[source]
    value = milliseconds / divisor
    return (value if smooth else int(value)) % LUA_SOURCES[source][1]


def native_motion_report(data):
    import struct
    from .native import inspect_binary
    from .watchface_library import read_tables
    from .model import SOURCES
    result=[]
    codes={bytes.fromhex(SOURCES[k][1]) for k in SECOND_SOURCES if k in SOURCES}
    for screen in inspect_binary(data)['screens']:
        for uid,_,b in read_tables(data,screen['index'])[7]:
            if b[3]>>4==3 and b[:2] in codes:
                period=struct.unpack_from('<H',b,6)[0]
                result.append({'screen':screen['index'],'aod':screen['aod'],'uid':f'{uid:08x}',
                               'sourceCode':b[:2].hex().upper(),'periodMs':period,'pointerFps':1000//period})
    return {'sweepFps':SWEEP_FPS,'periodMs':SWEEP_PERIOD_MS,'pointers':result,'aodSecondsExcluded':not any(p['aod'] for p in result)}
