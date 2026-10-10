"""Exercise notification order, including every intermediate Pointer write."""
from itertools import permutations
from pathlib import Path
import pytest
from test_motion_interaction import lua_runtime
from test_chrono_pro import pro_runtime,view

ROOT=Path(__file__).resolve().parents[1]
CASES=[((12,4,59),(12,5,0)),((12,59,59),(13,0,0)),((23,59,59),(0,0,0)),
       ((12,59,59),(13,0,1))]


def push(lua,key,value):
    lua.globals().DATA['time'+key.capitalize()](value*256)


def trace(lua):
    lua.execute('''
        local object=getmetatable(make(nil,{})).__index;local oldset=object.set
        function object:set(t)
            if t.value~=nil then self.history=self.history or {};table.insert(self.history,t.value) end
            oldset(self,t)
        end
    ''')


@pytest.mark.parametrize('engine',['hour','minute','pro'])
@pytest.mark.parametrize('before,after',CASES)
def test_rollovers_never_publish_mixed_counters_in_any_notification_order(tmp_path,engine,before,after):
    for index,order in enumerate(permutations(('hour','minute','second'))):
        if engine=='pro':
            _,lua,core=pro_runtime(tmp_path/str(index))
            for source in ('studioTimeHour','studioTimeMinute'):view(core,source).smooth=True
            hands=[view(core,s).hands[1] for s in ('studioTimeHour','studioTimeMinute')]
        else:
            lua,_=lua_runtime()
            lua.execute('''
                DATA={};package.preload.dataman=function() return {subscribe=function(name,obj,cb)
                    DATA[name]=function(value) cb(obj,value) end end} end
                LV.Timer=function() error('Civil clock must remain timer-free') end
            ''')
            module=lua.execute((ROOT/'s5studio/lua/studio_civil_hand.lua').read_text(encoding='utf8'))
            hands=[lua.globals().make(None,lua.table()),lua.globals().make(None,lua.table())]
            module.bind(lua.globals().make(None,lua.table()),lua.table_from(hands),engine)
        trace(lua)
        for key,value in zip(('hour','minute','second'),before):push(lua,key,value)
        initial=[h.value for h in hands]
        for h in hands:h.history=lua.table()
        expected=[]
        for role in (('hour','minute') if engine=='pro' else (engine,engine)):
            h,m,s=after
            if engine=='pro':expected.append(round(((h%12+m/60+s/3600) if role=='hour' else m+s/60)*1000))
            else:expected.append((h%12*3600 if role=='hour' else 0)+m*60+s)
        for key in order:
            push(lua,key,dict(zip(('hour','minute','second'),after))[key])
            # Duplicate/stale seconds before the next sample cannot release
            # upper counters. Pro's existing scheduler may run between events.
            if engine=='pro':core.update(core,lua.globals().TICK)
            for i,hand in enumerate(hands):
                assert hand.value in (initial[i],expected[i]),(engine,order,key,list(hand.history.values()))
        assert [h.value for h in hands]==expected
        for i,hand in enumerate(hands):
            assert list(hand.history.values())==([] if initial[i]==expected[i] else [expected[i]])
        # The next ordinary second advances from the coherent new minute/hour.
        push(lua,'second',after[2]+1)
        if engine!='pro':assert [h.value for h in hands]==[v+1 for v in expected]


def test_civil_clock_stages_upper_counters_and_preserves_sample_copies():
    lua,_=lua_runtime()
    lua.execute('SAMPLES={};CLOCK=CIVIL_CLOCK.new(function(t)table.insert(SAMPLES,t)end)')
    clock=lua.globals().CLOCK;samples=lua.globals().SAMPLES
    for key,value in zip(('hour','minute','second'),(12,4,59)):clock.push(clock,key,value*256)
    assert len(samples)==1
    clock.push(clock,'minute',5*256);clock.push(clock,'second',59*256)
    assert len(samples)==1 and samples[1].minute==4
    clock.push(clock,'second',0)
    assert len(samples)==2 and samples[2].minute==5 and samples[2].second==0
    assert samples[1].minute==4 and samples[1].second==59
    for value in (-1,float('nan'),float('inf'),60*256,'bad'):
        clock.push(clock,'second',value)
    assert len(samples)==2
    # A non-adjacent civil correction is accepted, rather than forced forward.
    for key,value in zip(('hour','minute','second'),(7,20,30)):clock.push(clock,key,value*256)
    assert len(samples)==3 and samples[3].hour==7 and samples[3].minute==20 and samples[3].second==30


def test_early_upper_counters_cannot_pair_with_an_old_queued_second():
    lua,_=lua_runtime()
    lua.execute('SAMPLES={};CLOCK=CIVIL_CLOCK.new(function(t)table.insert(SAMPLES,t)end)')
    clock=lua.globals().CLOCK;samples=lua.globals().SAMPLES
    for key,value in zip(('hour','minute','second'),(12,59,58)):clock.push(clock,key,value*256)
    clock.push(clock,'hour',13*256);clock.push(clock,'minute',0)
    clock.push(clock,'second',59*256)
    assert len(samples)==1 and samples[1].hour==12 and samples[1].minute==59
    clock.push(clock,'second',0)
    assert len(samples)==2 and samples[2].hour==13 and samples[2].minute==0 and samples[2].second==0


@pytest.mark.parametrize('role',['hour','minute'])
def test_waiting_rollover_in_aod_updates_only_after_resume(role):
    lua,_=lua_runtime()
    lua.execute('''
        DATA={};package.preload.dataman=function()return {subscribe=function(name,obj,cb)
            DATA[name]=function(value)cb(obj,value)end end}end
        LV.Timer=function()error('No civil timer')end
    ''')
    module=lua.execute((ROOT/'s5studio/lua/studio_civil_hand.lua').read_text(encoding='utf8'))
    hand=lua.globals().make(None,lua.table());root=lua.globals().make(None,lua.table())
    module.bind(root,lua.table_from([hand]),role);trace(lua)
    for key,value in zip(('hour','minute','second'),(23,59,59)):push(lua,key,value)
    before=hand.value;hand.history=lua.table()
    push(lua,'second',0);assert hand.value==before
    lua.globals().ScreenStateChangedCB('ON','AOD',0)
    push(lua,'hour',0);push(lua,'minute',0)
    assert hand.value==before and len(hand.history)==0
    lua.globals().ScreenStateChangedCB('AOD','ON',0)
    assert hand.value==0 and list(hand.history.values())==[0]
