-- Daily 59-tooth moon disc. Independent of all chrono clocks and tap states.
local lvgl = require("lvgl")
local dataman = require("dataman")
local M = {views={}, active=true}

local function leap(y) return y%4==0 and (y%100~=0 or y%400==0) end
local function ordinal(y,m,d)
    if type(y)~="number" or type(m)~="number" or type(d)~="number" or
       y~=math.floor(y) or m~=math.floor(m) or d~=math.floor(d) or
       y<1900 or y>2399 or m<1 or m>12 or d<1 then return nil end
    local lengths={31,leap(y) and 29 or 28,31,30,31,30,31,31,30,31,30,31}
    if d>lengths[m] then return nil end
    local prior=y-1
    local result=365*prior+math.floor(prior/4)-math.floor(prior/100)+math.floor(prior/400)+d
    for month=1,m-1 do result=result+lengths[month] end
    return result
end
M.ordinal=ordinal

local function local_day()
    if not os or type(os.date)~="function" then return nil end
    local ok,t=pcall(os.date,"*t")
    if ok and type(t)=="table" then return ordinal(t.year,t.month,t.day) end
    return nil
end

function M.draw(v,day,force)
    if not M.active or v.deleted or not v.visible or not day then return end
    local value=(day-v.reference+v.config.offset)%59
    if not force and v.last==value then return end
    v.last=value
    for _,hand in ipairs(v.hands) do hand:set {value=value} end
end

local function pending_day(v)
    return ordinal(v.calendar.year,v.calendar.month,v.calendar.day)
end

local function stop(v)
    if v.timer then v.timer:pause() end
    v.settleRevision=nil
end

local function queue(v)
    if v.deleted or not v.visible or not M.active then return end
    local pending=pending_day(v)
    local day=not pending and local_day() or nil
    if day then stop(v);M.draw(v,day);return end
    -- AOD is a frozen pose: no periodic timer or animated rotation.
    if v.config.aod then
        if v.last==nil then M.draw(v,pending_day(v)) end
        return
    end
    if not pending then return end
    if not v.timer then
        -- Coalesce independently delivered Y/M/D notifications. This timer is
        -- paused in steady state; it runs briefly ONLY after a calendar event.
        v.timer=lvgl.Timer {period=200,cb=function()
            if v.deleted or not v.visible or not M.active then stop(v);return end
            if v.settleRevision~=v.revision then v.settleRevision=v.revision;return end
            stop(v);M.draw(v,pending_day(v))
        end}
    end
    v.timer:resume()
end

local function activate(v)
    if v.deleted or not v.visible then return end
    local pending=pending_day(v)
    local day=not pending and local_day() or nil
    if day then stop(v);M.draw(v,day,true)
    elseif v.config.aod then M.draw(v,pending,true)
    else v.last=nil;queue(v) end
end

function M.bind(root,hands,config)
    for i=#M.views,1,-1 do if M.views[i].deleted then table.remove(M.views,i) end end
    local v={root=root,hands=hands,config=config,reference=ordinal(config.reference[1],config.reference[2],config.reference[3]),
             calendar={},revision=0,visible=true}
    if not v.reference then error("Invalid moon reference date") end
    M.views[#M.views+1]=v
    activate(v)
    for _,channel in ipairs({"year","month","day"}) do
        local field=channel
        dataman.subscribe("date"..field:sub(1,1):upper()..field:sub(2),root,function(_,raw)
            if v.deleted or type(raw)~="number" then return end
            local value=raw/256
            if value~=math.floor(value) or value==v.calendar[field] then return end
            v.calendar[field]=value;v.revision=v.revision+1
            if not v.nativeReady and pending_day(v) then
                v.nativeReady=true
                if v.config.aod then M.draw(v,pending_day(v),true);return end
            end
            -- AOD holds its initial pose until a screen/page activation.
            if v.config.aod and v.last~=nil then return end
            queue(v)
        end)
    end
    if lvgl.EVENT.DELETE then root:onevent(lvgl.EVENT.DELETE,function()
        v.deleted=true;stop(v)
        if v.timer and type(v.timer.delete)=="function" then v.timer:delete() end
        v.hands={};v.root=nil
    end) end
    if not M.lifecycle then
        M.lifecycle=true
        local previous=ScreenStateChangedCB
        ScreenStateChangedCB=function(pre,now,reason)
            if previous then previous(pre,now,reason) end
            for _,view in ipairs(M.views) do
                if not view.deleted then
                    view.visible=(now=="ON" and not view.config.aod) or (now=="AOD" and view.config.aod)
                    if view.visible then view.root:clear_flag(lvgl.FLAG.HIDDEN);activate(view)
                    else view.root:add_flag(lvgl.FLAG.HIDDEN);stop(view) end
                end
            end
        end
        local pause,resume=pageOnPause,pageOnResume
        pageOnPause=function()
            if pause then pause() end
            M.active=false
            for _,view in ipairs(M.views) do stop(view) end
        end
        pageOnResume=function()
            if resume then resume() end
            M.active=true
            for _,view in ipairs(M.views) do activate(view) end
        end
    end
    return v
end
return M
