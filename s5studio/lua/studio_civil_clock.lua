-- dataman delivers H/M/S separately. Publish whole civil samples, never a
-- new minute paired with the preceding second (or a new hour with minute 59).
-- No timer, animation or chronograph clock is involved.
local M = {}

function M.new(onSample)
    local clock = {pending={}}
    function clock:push(key, raw)
        if type(raw)~="number" or raw~=raw or raw<0 or raw==math.huge then return end
        local value=math.floor(raw/256)
        local limit=key=="hour" and 24 or 60
        if value>=limit then return end
        self.pending[key]=value
        local p,previous=self.pending,self.current
        if p.hour==nil or p.minute==nil or p.second==nil then return end
        -- Upper counters are staged until a fresh second is available. A late
        -- minute/hour notification can complete a waiting rollover sample.
        if previous then
            if p.second==previous.second then return end
            local step=(p.second-previous.second)%60
            if step<=2 then
                -- Normal ticking (or one missed second) has an unambiguous
                -- carry. Also reject upper counters that arrived before an
                -- old queued second from the preceding minute/hour.
                local total=(previous.hour*3600+previous.minute*60+previous.second+step)%86400
                if p.minute~=math.floor(total/60)%60 or p.hour~=math.floor(total/3600) then return end
            end
        end
        -- Copy the table: later notifications must not mutate a published pose.
        self.current={hour=p.hour,minute=p.minute,second=p.second}
        onSample(self.current)
    end
    return clock
end

return M
