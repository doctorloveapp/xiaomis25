-- Original S5 Studio runtime. Public API examples: m0tral/MiWatchLuaWatchfaces.
-- Shared by the entry points in one watchface Lua VM. No invented sensor IDs.
local existing = rawget(_G, "S5StudioChrono010")
if existing then return existing end
local lvgl = require("lvgl")
local M = {state = "reset", elapsed = 0, started = 0, views = {}, active = true}
_G.S5StudioChrono010 = M

local function milliseconds()
    -- Use a monotonic clock, never CPU time or a count of timer callbacks.
    if type(lvgl.tick_get) == "function" then return lvgl.tick_get() end
    local f = io.open("/proc/uptime", "r")
    if not f then return nil end
    local line = f:read("*l")
    f:close()
    local seconds = line and tonumber(line:match("^%s*([%d%.]+)"))
    return seconds and math.floor(seconds * 1000) or nil
end
M.clock = milliseconds

function M:value(now)
    if self.state == "running" then return math.max(0, now - self.started) end
    return self.elapsed
end

function M:tap()
    if not self.active then return end
    local now = self.clock()
    if not now then print("S5 Studio: monotonic clock unavailable; chrono disabled"); return end
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
        local value
        if view.source == "studioDecisecond" then
            value = (now % 1000) / 100
            if not view.smooth then value = math.floor(value) end
        else
            local divisor = view.source == "studioChronoHour" and 3600000 or
                (view.source == "studioChronoMinute" and 60000 or 1000)
            value = elapsed / divisor
            if not view.smooth then value = math.floor(value) end
            value = value % view.range
        end
        for _, hand in ipairs(view.hands) do hand:set {value = value} end
    end
end

function M:screen(on)
    self.active = on
    for _, view in ipairs(self.views) do
        if on then view.root:clear_flag(lvgl.FLAG.HIDDEN)
        else view.root:add_flag(lvgl.FLAG.HIDDEN) end
    end
    if on then self.timer:resume(); self:update(self.clock())
    else self.timer:pause() end
end

function M:add(view)
    self.views[#self.views + 1] = view
    if lvgl.EVENT.DELETE then
        view.root:onevent(lvgl.EVENT.DELETE, function()
            for index, item in ipairs(M.views) do
                if item == view then table.remove(M.views, index); break end
            end
            if #M.views == 0 then
                M.timer:pause()
                M.state, M.elapsed, M.started = "reset", 0, 0
            end
        end)
    end
    if not self.timer then
        self.timer = lvgl.Timer {period = 40, cb = function() M:update(M.clock()) end}
        -- Both lifecycle mechanisms are present in the public device examples.
        local previous = ScreenStateChangedCB
        ScreenStateChangedCB = function(pre, now, reason)
            if previous then previous(pre, now, reason) end
            M:screen(now == "ON")
        end
        local pause, resume = pageOnPause, pageOnResume
        pageOnPause = function() if pause then pause() end; M:screen(false) end
        pageOnResume = function() if resume then resume() end; M:screen(true) end
    end
    if self.active then self.timer:resume() else view.root:add_flag(lvgl.FLAG.HIDDEN) end
    self:update(self.clock())
end
return M
