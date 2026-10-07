-- Original S5 Studio runtime. Public API examples: m0tral/MiWatchLuaWatchfaces.
-- All pointers in a theme are registered by ONE entry point/VM.
-- No cross-widget globals or invented sensor IDs are needed.
local existing = rawget(_G, "S5StudioChrono100")
if existing then return existing end
local lvgl = require("lvgl")
local M = {state = "reset", elapsed = 0, started = 0, views = {}, active = true,
    screenOn = true, pendingTap = false}
_G.S5StudioChrono100 = M

local reader
local function proc_milliseconds()
    if not io or type(io.open) ~= "function" then return nil end
    local ok, f = pcall(io.open, "/proc/uptime", "r")
    if not ok or not f then return nil end
    local line = f:read("*l"); f:close()
    local seconds = line and tonumber(line:match("^%s*([%d%.]+)"))
    return seconds and math.floor(seconds * 1000) or nil
end
local function wall_milliseconds()
    if not os or type(os.time) ~= "function" then return nil end
    local ok, seconds = pcall(os.time)
    return ok and type(seconds) == "number" and seconds * 1000 or nil
end
local function milliseconds()
    -- Select once: mixing clock origins after a failure corrupts elapsed time.
    -- Prefer monotonic sources. os.time is used in public Xiaomi Lua examples;
    -- this fallback has SECOND precision and is sensitive to clock correction.
    if reader then return reader() end
    if type(lvgl.tick_get) == "function" then
        local ok, value = pcall(lvgl.tick_get)
        if ok and type(value) == "number" then
            reader, M.clockMode = lvgl.tick_get, "lvgl-monotonic"; return value
        end
    end
    local value = proc_milliseconds()
    if value then reader, M.clockMode = proc_milliseconds, "proc-monotonic"; return value end
    value = wall_milliseconds()
    if value then reader, M.clockMode = wall_milliseconds, "wall-second"; return value end
    M.clockMode = "unavailable"
    return nil
end
M.clock = milliseconds

function M:value(now)
    if self.state == "running" then
        self.elapsed = math.max(self.elapsed, now - self.started)
        return self.elapsed
    end
    return self.elapsed
end

function M:tap()
    if not self.active then
        -- Some hosts pause the Lua page during a touch. Retain one input until
        -- resume, but never queue a tap from AOD or a genuinely off screen.
        if self.screenOn then self.pendingTap = true end
        return
    end
    local now = self.clock()
    if not now then print("S5 Studio: no supported clock available; chrono disabled"); return end
    if self.state == "reset" then
        self.started, self.state = now, "running"
    elseif self.state == "running" then
        self.elapsed, self.state = self:value(now), "stopped"
    else
        self.elapsed, self.started, self.state = 0, 0, "reset"
    end
    self:update(now)
end

function M:update(now)
    if not self.active or not now then return end
    local elapsed = self:value(now)
    for _, view in ipairs(self.views) do
        -- Deciseconds have their own LVGL animation clock. Updating a chrono
        -- must never overwrite that phase, or require an exported tick_get API.
        if view.source ~= "studioDecisecond" then
            local divisor = view.source == "studioChronoHour" and 3600000 or
                (view.source == "studioChronoMinute" and 60000 or 1000)
            local value = elapsed / divisor
            if not view.smooth then value = math.floor(value) end
            value = value % view.range
            for _, hand in ipairs(view.hands) do hand:set {value = value} end
        end
    end
end

function M:screen(on, temporary)
    if not temporary then
        self.screenOn = on
        if not on then self.pendingTap = false end
    end
    self.active = on
    for _, view in ipairs(self.views) do
        -- Page pause stops updates. Only screen-off/AOD hides the graphics;
        -- a temporary touch pause should not make all small hands disappear.
        if self.screenOn then view.root:clear_flag(lvgl.FLAG.HIDDEN)
        else view.root:add_flag(lvgl.FLAG.HIDDEN) end
        if view.animation then view.animation:set {run = on} end
    end
    if self.timer then
        if on then self.timer:resume(); self:update(self.clock())
        else self.timer:pause() end
    end
    if on and self.pendingTap then
        self.pendingTap = false
        self:tap()
    end
end

function M:add(view)
    self.views[#self.views + 1] = view
    if view.source == "studioDecisecond" then
        -- Anim uses the engine's own millisecond scheduler. Public Xiaomi Lua
        -- examples use duration=1000, repeat_count=-1 and linear exec_cb.
        -- One animation drives both the hand and its shadow in lockstep.
        view.animation = view.root:Anim {
            run = self.active, start_value = 0, end_value = 1000,
            duration = 1000, repeat_count = -1, path = "linear",
            exec_cb = function(_, phase)
                if not M.active then return end
                local tenth = (phase % 1000) / 100
                if not view.smooth then tenth = math.floor(tenth) end
                -- A full configured sweep every second, including projects
                -- which retained their former seconds range of 60.
                local value = view.valueStart + tenth / 10 * view.valueRange
                for _, hand in ipairs(view.hands) do hand:set {value = value} end
            end
        }
    elseif not self.timer then
        self.timer = lvgl.Timer {period = 40, cb = function() M:update(M.clock()) end}
    end
    if lvgl.EVENT.DELETE then
        view.root:onevent(lvgl.EVENT.DELETE, function()
            if view.animation then view.animation:set {run = false} end
            for index, item in ipairs(M.views) do
                if item == view then table.remove(M.views, index); break end
            end
            if #M.views == 0 then
                if M.timer then M.timer:pause() end
                M.state, M.elapsed, M.started = "reset", 0, 0
                M.pendingTap = false
            end
        end)
    end
    if not self.lifecycle then
        self.lifecycle = true
        -- Both lifecycle mechanisms are present in the public device examples.
        local previous = ScreenStateChangedCB
        ScreenStateChangedCB = function(pre, now, reason)
            if previous then previous(pre, now, reason) end
            M:screen(now == "ON")
        end
        local pause, resume = pageOnPause, pageOnResume
        pageOnPause = function() if pause then pause() end; M:screen(false, true) end
        pageOnResume = function() if resume then resume() end; M:screen(M.screenOn, true) end
    end
    if self.active then
        if self.timer then self.timer:resume(); self:update(self.clock()) end
    else view.root:add_flag(lvgl.FLAG.HIDDEN) end
end
return M
