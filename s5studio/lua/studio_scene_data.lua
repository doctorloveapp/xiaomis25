-- Real calendar/sensor sources inside the shared chrono scene, in layer order.
-- These views never enter the chrono controller or its Start/Stop/Reset group.
local lvgl = require("lvgl")
local dataman = require("dataman")
local M = {views={}, active=true, screenOn=true}

local function valid(raw)
    return type(raw)=="number" and raw==raw and math.abs(raw)<math.huge and
        raw~=2147483647 and raw~=4294967295 and raw~=-2147483648 and raw~=2147483648
end

local function start_sweep(v)
    if not v.animation then return end
    -- The S5-tested one-shot contract uses repeat_count=1. Toggle run so a
    -- new second restarts an in-flight animation rather than reusing its pose.
    v.animation:set {run=false}
    if v.value~=nil and M.active and M.screenOn then
        v.animation:set {start_value=0,end_value=1000,duration=1000,run=true}
    end
end

function M.draw(v,phase)
    if v.deleted or not M.active or not M.screenOn then return end
    local value=v.value
    if v.config.choices then
        local item=value and v.config.choices[value]
        if v.last==value and v.drawn then return end
        v.last=value;v.drawn=true
        if item then
            v.image:set {x=item.x,y=item.y,src=SCRIPT_PATH..item.src}
            v.image:clear_flag(lvgl.FLAG.HIDDEN)
        else v.image:add_flag(lvgl.FLAG.HIDDEN) end
    elseif value then
        if v.config.smooth then value=(value+math.min(1000,math.max(0,phase or 0))/1000)%60 end
        local rendered=math.floor(value*v.config.scale+0.5)
        if v.last==rendered then return end
        v.last=rendered
        for _,hand in ipairs(v.hands) do hand:set {value=rendered} end
    end
end

local function activate(v)
    if v.deleted then return end
    if M.screenOn then v.root:clear_flag(lvgl.FLAG.HIDDEN) else v.root:add_flag(lvgl.FLAG.HIDDEN) end
    if not M.active or not M.screenOn then
        if v.animation then v.animation:set {run=false} end
        return
    end
    v.last=nil;v.drawn=false;M.draw(v)
    start_sweep(v)
end

local function bind(v)
    for i=#M.views,1,-1 do if M.views[i].deleted then table.remove(M.views,i) end end
    M.views[#M.views+1]=v
    if v.config.smooth then
        -- One bounded sweep per real second notification; no polling timer.
        -- Match the dedicated animation carrier used by the tested Pro engine.
        local carrier=lvgl.Object(v.root,{x=0,y=0,w=1,h=1,bg_opa=0,border_width=0,pad_all=0})
        carrier:clear_flag(lvgl.FLAG.SCROLLABLE);carrier:clear_flag(lvgl.FLAG.CLICKABLE)
        v.animation=carrier:Anim {start_value=0,end_value=1000,duration=1000,
            repeat_count=1,path="linear",run=false,exec_cb=function(_,phase) M.draw(v,phase) end}
    end
    dataman.subscribe(v.config.source,v.root,function(_,raw)
        if v.deleted then return end
        local value=valid(raw) and raw/256 or nil
        -- Civil channels can carry Q8 fractional bits. These small hands use
        -- whole hours/minutes/seconds, just like studio_civil_clock. Rounding
        -- 14.x to 15 must never advance the 24-hour hand before the hour turns.
        local source=v.config.source
        if value and (source=="timeHour" or source=="timeMinute" or source=="timeSecond") then
            local limit=source=="timeHour" and 24 or 60
            value=value>=0 and value<limit and math.floor(value) or nil
        end
        if value==v.value then return end
        v.value=value;M.draw(v)
        start_sweep(v)
    end)
    if lvgl.EVENT.DELETE then v.root:onevent(lvgl.EVENT.DELETE,function()
        v.deleted=true
        if v.animation then v.animation:set {run=false} end
        v.hands={}
    end) end
    if not M.lifecycle then
        M.lifecycle=true
        local previous=ScreenStateChangedCB
        ScreenStateChangedCB=function(pre,now,reason)
            if previous then previous(pre,now,reason) end
            M.screenOn=now=="ON"
            for _,view in ipairs(M.views) do activate(view) end
        end
        local pause,resume=pageOnPause,pageOnResume
        pageOnPause=function()
            if pause then pause() end
            M.active=false;for _,view in ipairs(M.views) do activate(view) end
        end
        pageOnResume=function()
            if resume then resume() end
            M.active=true;for _,view in ipairs(M.views) do activate(view) end
        end
    end
    activate(v)
    return v
end

function M.pointer(root,hands,config)
    return bind {root=root,hands=hands,config=config}
end

function M.images(scene,config)
    local root=lvgl.Object(scene,{x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})
    root:clear_flag(lvgl.FLAG.SCROLLABLE);root:clear_flag(lvgl.FLAG.CLICKABLE)
    local _,first=next(config.choices)
    if not first then return end
    local img=root:Image {x=first.x,y=first.y,src=SCRIPT_PATH..first.src}
    img:clear_flag(lvgl.FLAG.CLICKABLE);img:add_flag(lvgl.FLAG.HIDDEN)
    return bind {root=root,image=img,config=config}
end

return M
