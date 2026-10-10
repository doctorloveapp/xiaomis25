-- Civil hands follow dataman seconds, not a timer or the chronograph clock.
local lvgl = require("lvgl")
local dataman = require("dataman")
local civilClock = require("studio_civil_clock")
local M = {}

function M.bind(root, hands, role)
    local state = {time={}, active=true, screenOn=true, disposed=false}
    local function update()
        local t=state.time
        if not state.active or state.disposed or t.minute==nil or t.second==nil then return end
        if role=="hour" and t.hour==nil then return end
        -- Scaled integer domains preserve sub-minute positions on firmware
        -- setters that truncate fractions: 43200/hours and 3600/minutes.
        local value=(t.minute%60)*60+t.second%60
        if role=="hour" then value=(t.hour%12)*3600+value end
        if state.last==value then return end
        state.last=value
        for _,hand in ipairs(hands) do hand:set {value=value} end
    end
    local clock=civilClock.new(function(sample)
        state.time=sample
        update()
    end)
    for _,channel in ipairs({"hour","minute","second"}) do
        local key=channel
        dataman.subscribe("time"..key:sub(1,1):upper()..key:sub(2),root,function(_,value)
            if state.disposed then return end
            clock:push(key,value)
        end)
    end
    local previous=ScreenStateChangedCB
    ScreenStateChangedCB=function(pre,now,reason)
        if previous then previous(pre,now,reason) end
        state.screenOn=now=="ON";state.active=state.screenOn
        update()
    end
    local pause,resume=pageOnPause,pageOnResume
    pageOnPause=function() if pause then pause() end;state.active=false end
    pageOnResume=function() if resume then resume() end;state.active=state.screenOn;update() end
    if lvgl.EVENT.DELETE then
        root:onevent(lvgl.EVENT.DELETE,function() state.disposed=true;state.active=false end)
    end
    return state
end
return M
