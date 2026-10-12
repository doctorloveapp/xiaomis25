-- Original Crono-Pro runtime. The separate 1.0 runtime remains unchanged.
local existing = rawget(_G, "S5StudioChronoPro120")
if existing then return existing end
local lvgl = require("lvgl")
local base = require("studio_core")
local civilClock = require("studio_civil_clock")
local M = {state="rest", elapsed=0, started=0, views={}, active=true,
    screenOn=true, pendingTap=false, civil={hour=0,minute=0,second=0},
    civilReady=false, transitionMs=720, engineTick=0, lastPhase=0}
_G.S5StudioChronoPro120 = M

local function isPost(view)
    return view.source=="studioChronoCentisecond" or view.source=="studioChronoMillisecond"
end

function M:postValue(view)
    local value=math.floor((self.elapsed%1000)/(view.source=="studioChronoCentisecond" and 10 or 1))
    if view.postReadout=="digit" then value=value%10 end
    if view.bounded then value=math.max(view.valueStart,math.min(view.valueStart+view.valueRange,value)) end
    return value
end

local function wall()
    if not os or type(os.time)~="function" then return nil end
    local ok,v=pcall(os.time)
    return ok and type(v)=="number" and v*1000 or nil
end

function M:clock()
    if self.engineClock then return self.engineTick end
    local raw=base.clock()
    if not raw then return nil end
    -- Unwrap a 32-bit LVGL tick; never mix clock origins during a measure.
    if base.clockMode=="lvgl-monotonic" then
        self.wrapOffset=self.wrapOffset or 0
        if self.lastRaw and raw<self.lastRaw and self.lastRaw-raw>2147483648 then
            self.wrapOffset=self.wrapOffset+4294967296
        end
        self.lastRaw=raw
        raw=raw+self.wrapOffset
    end
    return raw
end

function M:write(view,value)
    if view.bounded and not view.transitioning then
        value=math.max(view.valueStart,math.min(view.valueStart+view.valueRange,value))
    end
    if math.abs(view.angleRange)>=360 then
        value=view.valueStart+(value-view.valueStart)%view.valueRange
    end
    -- Integer high-resolution domains also work with firmware setters that
    -- truncate Lua fractions. One hour/minute returning to zero must sweep.
    local scale=view.scale or 1
    local rendered=math.floor(value*scale+0.5)
    view.last=rendered/scale
    if view.transitionAngle then
        rendered=math.floor(((view.angleStart or 0)+(value-view.valueStart)*view.angleRange/view.valueRange)%360*10+0.5)%3600
    end
    if view.rendered==rendered then return end
    view.rendered=rendered
    for _,hand in ipairs(view.hands) do hand:set {value=rendered} end
end

function M:value(now)
    if self.state=="running" and now then
        self.elapsed=math.max(self.elapsed,now-self.started)
    end
    return self.elapsed
end

function M:refresh(now)
    -- Consume the current clock in the animation callback that published it.
    -- Gate by elapsed-time buckets, not by a second, drifting polling timer.
    if not self.active or not self.screenOn or not now then return end
    local bucket
    if self.state=="running" then
        local elapsed=math.max(self.elapsed,now-self.started)
        local period=self.hasDeciseconds and (self.smoothDeciseconds and 40 or 100) or 1000
        bucket=math.floor(elapsed/period)
    elseif self.state=="rest" and self.main and self.main.smooth and not self.main.onlyChrono then
        bucket=math.floor(now/40)
    else return end
    if self.frameState==self.state and self.frameBucket==bucket then return end
    self.frameState=self.state;self.frameBucket=bucket
    self:update(now)
end

function M:civilSecond(now)
    local value=self.civil.second
    if self.main and self.main.smooth and self.civilTick and now then
        value=value+math.min(1,math.max(0,(now-self.civilTick)/1000))
    end
    return value%60
end

function M:target(view,elapsed,now)
    if view.source=="studioIntegratedSecond" then
        if view.onlyChrono then return view.valueStart end
        return self:civilSecond(now)
    end
    return view.valueStart
end

function M:update(now)
    if not self.active then return end
    local elapsed=self:value(now)
    for _,view in ipairs(self.views) do
        local source=view.source
        if source=="studioTimeHour" then
            self:write(view,self.civil.hour%12+self.civil.minute/60+(view.smooth and self.civil.second/3600 or 0))
        elseif source=="studioTimeMinute" then
            self:write(view,self.civil.minute+(view.smooth and self.civil.second/60 or 0))
        elseif source=="studioIntegratedSecond" then
            if self.state=="rest" then
                if view.onlyChrono then self:write(view,view.valueStart)
                elseif self.civilReady then self:write(view,self:civilSecond(now)) end
            elseif self.state=="ready" then self:write(view,view.valueStart)
            elseif self.state=="running" or self.state=="reading" or self.state=="stopped" then
                self:write(view,math.floor(elapsed/1000)%60)
            end
        elseif isPost(view) then
            -- No high-frequency render loop: POST hands stay at their start
            -- throughout the measure and use the one frozen Stop timestamp.
            if not self.transition then
                self:write(view,self.state=="stopped" and self:postValue(view) or view.valueStart)
            end
        elseif source~="studioDecisecond" and not self.transition then
            local value=0
            if self.state=="running" or self.state=="reading" or self.state=="stopped" then
                if source=="studioChronoDecisecond" then
                    local fraction=(elapsed%1000)/1000
                    if not view.smooth then fraction=math.floor((elapsed%1000)/100)/10 end
                    value=fraction*view.valueRange
                else
                    local divisor=source=="studioChronoHour" and 3600000 or
                        (source=="studioChronoMinute" and 60000 or 1000)
                    value=math.floor(elapsed/divisor)%view.range
                end
            end
            self:write(view,view.valueStart+value)
        end
    end
end

function M:schedulers()
    if self.runTimer then self.runTimer:pause() end
    if self.restTimer then self.restTimer:pause() end
    local ticking=self.active and self.screenOn
    if ticking and not self.frameDriven and self.state=="running" and self.runTimer then self.runTimer:resume() end
    if ticking and not self.frameDriven and self.state=="rest" and self.main and self.main.smooth and not self.main.onlyChrono and self.restTimer then self.restTimer:resume() end
    if self.clockAnimation then
        local run=ticking and (self.state=="running" or
            self.state=="arming" or self.state=="resetting" or
            self.state=="rest" and self.main and self.main.smooth and not self.main.onlyChrono) or false
        if run~=self.clockRunning then
            if run then self.lastPhase=nil;self.frameState=nil;self.frameBucket=nil end
            self.clockRunning=run;self.clockAnimation:set {run=run}
        end
    end
end

function M:finishTransition()
    local action=self.transition and self.transition.action
    self.transition=nil
    if self.transitionAnimation then self.transitionAnimation:set {run=false} end
    for _,view in ipairs(self.views) do
        view.transitioning=nil
        if view.transitionAngle then
            local scale=view.scale or 1
            for _,hand in ipairs(view.hands) do hand:set {range={angleStart=(view.angleStart or 0)*10,
                angleRange=view.angleRange*10,valueStart=view.valueStart*scale,valueRange=view.valueRange*scale}} end
            view.transitionAngle=nil;view.rendered=nil
        end
    end
    if action=="arming" then self.state="ready"
    elseif action=="reading" then self.state="stopped"
    elseif action=="resetting" then self.state="rest";self.elapsed=0;self.started=0 end
    -- Final pose comes from the latest civil time, including a second rollover.
    self:update(self:clock());self:schedulers()
end

function M:progress(phase)
    if not self.active or not self.screenOn or not self.transition then return end
    local t=self.transition
    local frame=math.floor(phase*self.transitionMs/1000/40)
    if phase<1000 and frame==t.frame then return end
    t.frame=frame
    local fraction=math.max(0,math.min(1,phase/1000))
    local eased=1-(1-fraction)^2
    local now=self:clock()
    for _,entry in ipairs(t.entries) do
        local view=entry.view
        local destination=t.action=="reading" and self:postValue(view) or
            (t.action=="resetting" and self:target(view,0,now) or view.valueStart)
        local delta=destination-entry.start
        if view.bounded then
            -- Calibrated arcs never leave their printed scale. The signed
            -- range controls the measurement direction, including CCW.
            self:write(view,entry.start+delta*eased)
        elseif view.angleRange~=0 then
            local period=view.valueRange*360/math.abs(view.angleRange)
            local direction=view.angleRange>0 and 1 or -1
            if entry.destination then
                entry.destination=entry.destination+(destination-entry.destination+period/2)%period-period/2
                -- A live civil target may cross 59/0 or be corrected. It may
                -- advance to the next revolution, never reverse the sweep.
                while direction*(entry.destination-(entry.last or entry.start)) < -0.000001 do
                    entry.destination=entry.destination+direction*period
                end
            else entry.destination=entry.start+direction*(direction*delta%period) end
            delta=entry.destination-entry.start
            local candidate=entry.start+delta*eased
            if entry.last and direction*(candidate-entry.last)<0 then candidate=entry.last end
            entry.last=candidate;self:write(view,candidate)
        else
            self:write(view,entry.start+delta*eased)
        end
    end
    if phase>=1000 then self:finishTransition() end
end

function M:beginTransition(action)
    self.state=action
    local entries={}
    for _,view in ipairs(self.views) do
        if (action=="reading" and isPost(view)) or (action~="reading" and
            view.source~="studioTimeHour" and view.source~="studioTimeMinute" and view.source~="studioDecisecond") then
            entries[#entries+1]={view=view,start=view.last or view.valueStart}
            view.transitioning=true
            -- Partial/reversed dials still return physically clockwise. During
            -- the sweep use a full-circle angle domain, then restore the range.
            if not view.bounded and math.abs(view.angleRange)>0 and math.abs(view.angleRange)<360 then
                view.transitionAngle=true;view.rendered=nil
                for _,hand in ipairs(view.hands) do hand:set {range={angleStart=0,angleRange=3600,valueStart=0,valueRange=3600}} end
                self:write(view,view.last or view.valueStart)
            end
        end
    end
    self.transition={action=action,entries=entries,frame=-1}
    self:schedulers()
    self.transitionAnimation:set {start_value=0,end_value=1000,duration=self.transitionMs,run=true}
end

function M:tap()
    if not self.screenOn then return end
    if not self.active then if not self.ignorePausedTap then self.pendingTap=true end;return end
    if self.transition then return end
    local now=self:clock()
    if not now then return end
    if self.engineClock then
        if self.tapLocked then return end
        self.tapLocked=true;self.tapUnlockAnimation:set {start_value=0,end_value=1000,run=true}
    elseif self.lastTap and now-self.lastTap<150 then return end
    self.lastTap=now
    if self.state=="rest" then
        if not self.civilReady then return end
        self:beginTransition("arming")
    elseif self.state=="ready" then
        self.elapsed=0;self.started=now;self.state="running"
        self:update(now);self:schedulers()
    elseif self.state=="running" then
        self.elapsed=self:value(now);self.state="stopped"
        local post=false
        for _,view in ipairs(self.views) do if isPost(view) then post=true end end
        if post then
            self.state="reading";self:update(now);self:beginTransition("reading")
        else self:update(now);self:schedulers() end
    elseif self.state=="stopped" then self:beginTransition("resetting") end
end

function M:screen(on,temporary)
    if not self.configured then return end
    if on and self.currentScene==false then return end
    if not temporary then
        self.screenOn=on
        if not on then self.pendingTap=false end
    end
    local resuming=on and not self.active
    self.active=on
    if not on then
        self.ignorePausedTap=temporary and self.transition~=nil
        self.transitionPaused=temporary and self.transition~=nil
        -- Repeated pause/resume callbacks while still in AOD must preserve the
        -- first suspension time, including pageOnResume before screen ON.
        if self.engineClock and not self.sleepWall then self.sleepWall=wall() end
        if not temporary and self.engineClock and not self.sleepWall and self.state=="running" then
            self.state="stopped" -- No usable sleep clock: do not invent elapsed time.
        end
        if self.tapUnlockAnimation then self.tapUnlockAnimation:set {run=false};self.tapLocked=false end
        if self.transitionAnimation then self.transitionAnimation:set {run=false} end
        -- Never let a hidden transition finish later and write stale poses.
        if self.transition and not temporary then self:finishTransition() end
    elseif self.engineClock then
        if self.sleepWall then
            local current=wall()
            if current then self.engineTick=self.engineTick+math.max(0,current-self.sleepWall) end
        end
        self.sleepWall=nil;self.lastPhase=nil
    end
    for _,view in ipairs(self.views) do
        if self.screenOn then view.root:clear_flag(lvgl.FLAG.HIDDEN)
        else view.root:add_flag(lvgl.FLAG.HIDDEN) end
        if view.animation then view.animation:set {run=on} end
    end
    if self.screenOn then self.root:clear_flag(lvgl.FLAG.HIDDEN)
    else self.root:add_flag(lvgl.FLAG.HIDDEN) end
    self:schedulers()
    if on then
        -- A resumed renderer may need its pose reasserted even when the data
        -- is unchanged (hours can stay identical for an hour). Keep the cache
        -- for normal frames and duplicate ON notifications.
        if resuming then for _,view in ipairs(self.views) do view.rendered=nil end end
        if self.transition and self.transitionPaused then
            for _,entry in ipairs(self.transition.entries) do
                entry.start=entry.view.last or entry.start;entry.destination=nil
            end
            self.transition.frame=-1
            self.transitionAnimation:set {start_value=0,end_value=1000,run=true}
        end
        self.transitionPaused=false
        self:update(self:clock())
        if self.ignorePausedTap then self.pendingTap=false end
        self.ignorePausedTap=false
        if self.pendingTap then self.pendingTap=false;self:tap() end
    end
end

function M:leave()
    self:screen(false);self.currentScene=false
end

function M:configure(root,hasDeciseconds)
    if self.configured and self.root==root then return end
    if self.configured then
        self:screen(false)
        for _,v in ipairs(self.views) do if v.animation then v.animation:set {run=false} end end
        self.views={};self.main=nil;self.state="rest";self.elapsed=0;self.started=0
        self.civil={hour=0,minute=0,second=0};self.civilReady=false
        self.engineClock=false;self.engineTick=0;self.lastPhase=0;self.clockRunning=false
        self.clockAnimation=nil;self.lastTap=nil;self.tapLocked=false;self.sleepWall=nil
    end
    self.configured=true;self.root=root;self.active=true;self.screenOn=true
    self.hasDeciseconds=hasDeciseconds;self.smoothDeciseconds=false
    self.frameState=nil;self.frameBucket=nil
    self.currentScene=true
    -- Independent styles may mix classic and Pro in a shared host VM. Keep
    -- the unchanged classic runtime suspended while this Pro scene owns it.
    if not self.baseScreen then
        self.baseScreen=base.screen
        base.screen=function(controller,on,temporary)
            if M.currentScene then M.baseScreen(controller,false)
            else M.baseScreen(controller,on,temporary) end
        end
    end
    base:screen(false)
    local function animationRoot()
        local child=lvgl.Object(root,{x=0,y=0,w=1,h=1,bg_opa=0,border_width=0,pad_all=0})
        child:clear_flag(lvgl.FLAG.CLICKABLE);child:clear_flag(lvgl.FLAG.SCROLLABLE)
        return child
    end
    base.clock()
    if base.clockMode=="wall-second" or base.clockMode=="unavailable" then
        -- The already-supported LVGL animation exposes engine milliseconds.
        -- Sample its phase, never assume elapsed time from callback counts.
        -- Wall time covers sleep, with the original one-second precision there.
        self.engineClock=true;self.clockMode="lvgl-animation-phase"
    else self.clockMode=base.clockMode end
    self.frameDriven=self.engineClock or hasDeciseconds
    if self.frameDriven then
        self.clockAnimation=animationRoot():Anim {run=false,start_value=0,end_value=60000,
            duration=60000,repeat_count=-1,path="linear",
            exec_cb=function(_,phase)
                if not M.active or M.root~=root then return end
                if M.engineClock then
                    if M.lastPhase then M.engineTick=M.engineTick+(phase-M.lastPhase)%60000 end
                    M.lastPhase=phase
                end
                -- Direct clocks remain direct; animation phase is only a
                -- frame notification in that mode, never a new time origin.
                M:refresh(M:clock())
            end}
    end
    -- Slow/direct-clock scenes keep their existing timer path. These handles
    -- stay paused in frame-driven scenes; no independent 100 ms timer exists.
    self.runTimer=lvgl.Timer {period=1000,
        cb=function() if M.root==root then M:update(M:clock()) end end}
    self.restTimer=lvgl.Timer {period=40,cb=function() if M.root==root then M:update(M:clock()) end end}
    self.transitionAnimation=animationRoot():Anim {run=false,start_value=0,end_value=1000,
        duration=self.transitionMs,repeat_count=1,path="linear",
        exec_cb=function(_,phase) if M.root==root then M:progress(phase) end end}
    self.tapUnlockAnimation=animationRoot():Anim {run=false,start_value=0,end_value=1000,
        duration=150,repeat_count=1,path="linear",exec_cb=function(_,phase)
            if M.root==root and phase>=1000 then M.tapLocked=false;M.tapUnlockAnimation:set {run=false} end
        end}
    local dataman=require("dataman")
    local clock=civilClock.new(function(sample)
        if M.root~=root then return end
        M.civil=sample;M.civilReady=true;M.civilTick=M:clock()
        M:update(M:clock())
    end)
    for _,channel in ipairs({"hour","minute","second"}) do
        local key=channel
        dataman.subscribe("time"..key:sub(1,1):upper()..key:sub(2),root,function(_,value)
            if M.root~=root then return end
            clock:push(key,value)
        end)
    end
    if not self.lifecycle then
    self.lifecycle=true
    local previous=ScreenStateChangedCB
    ScreenStateChangedCB=function(pre,now,reason)
        if previous then previous(pre,now,reason) end
        M:screen(now=="ON")
    end
    local pause,resume=pageOnPause,pageOnResume
    pageOnPause=function() if pause then pause() end;M:screen(false,true) end
    pageOnResume=function() if resume then resume() end;M:screen(M.screenOn,true) end
    end
    if lvgl.EVENT.DELETE then
        root:onevent(lvgl.EVENT.DELETE,function()
            if M.root~=root then return end
            M.active=false;M.screenOn=false
            if M.runTimer then M.runTimer:pause() end
            if M.restTimer then M.restTimer:pause() end
            if M.clockAnimation then M.clockAnimation:set {run=false} end
            M.views={};M.state="rest";M.elapsed=0;M.started=0
            M.configured=false;M.main=nil;M.transition=nil;M.pendingTap=false;M.civilReady=false
            M.lastTap=nil;M.runTimer=nil;M.restTimer=nil;M.clockAnimation=nil
            M.clockRunning=false;M.transitionAnimation=nil;M.tapUnlockAnimation=nil
            M.engineClock=false;M.engineTick=0;M.lastPhase=0;M.civil={hour=0,minute=0,second=0}
            M.currentScene=false;_G.S5StudioChronoPro120=nil
        end)
    end
    self:schedulers()
    print("S5 Studio Crono-Pro clock: "..tostring(self.clockMode))
end

function M:add(view)
    self.views[#self.views+1]=view
    if view.source=="studioChronoDecisecond" and view.smooth then self.smoothDeciseconds=true end
    if view.source=="studioIntegratedSecond" then self.main=view end
    if view.source=="studioDecisecond" then
        local owner=self.root
        view.animation=view.root:Anim {run=self.active,start_value=0,end_value=1000,
            duration=1000,repeat_count=-1,path="linear",exec_cb=function(_,phase)
                if not M.active or M.root~=owner then return end
                local value=(phase%1000)/100
                if not view.smooth or M.state=="running" then value=math.floor(value) end
                M:write(view,view.valueStart+value/10*view.valueRange)
            end}
    end
    self:update(self:clock());self:schedulers()
end
return M
