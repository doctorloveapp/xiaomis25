-- Frame sequences only when a GIF is interleaved inside the shared Lua scene.
-- Ordinary GIF layers use the firmware's native SpriteGroup instead.
local lvgl = require("lvgl")
local M = {views={}, active=true, screenOn=true}

local function refresh(v,phase)
    if v.deleted or not M.active or not M.screenOn then return end
    local index=math.floor(math.max(0,phase)/v.interval)%#v.sequence+1
    local key=v.sequence[index]
    if key==v.last then return end
    v.last=key
    v.image:set {src=SCRIPT_PATH..v.frames[key]}
end

local function activate(v)
    if v.deleted then return end
    local run=M.active and M.screenOn
    if run then v.root:clear_flag(lvgl.FLAG.HIDDEN) else v.root:add_flag(lvgl.FLAG.HIDDEN) end
    v.animation:set {run=false}
    if run then
        v.last=nil;refresh(v,0)
        v.animation:set {run=true}
    end
end

function M.add(scene,config)
    for i=#M.views,1,-1 do if M.views[i].deleted then table.remove(M.views,i) end end
    local v={frames=config.frames,sequence=config.sequence,interval=config.interval}
    v.root=lvgl.Object(scene,{x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})
    v.root:clear_flag(lvgl.FLAG.SCROLLABLE);v.root:clear_flag(lvgl.FLAG.CLICKABLE)
    v.image=v.root:Image {x=config.x,y=config.y,src=SCRIPT_PATH..v.frames[v.sequence[1]]}
    v.image:clear_flag(lvgl.FLAG.CLICKABLE)
    local carrier=lvgl.Object(v.root,{x=0,y=0,w=1,h=1,bg_opa=0,border_width=0,pad_all=0})
    carrier:clear_flag(lvgl.FLAG.SCROLLABLE);carrier:clear_flag(lvgl.FLAG.CLICKABLE)
    v.animation=carrier:Anim {start_value=0,end_value=config.interval*#config.sequence,
        duration=config.interval*#config.sequence,repeat_count=-1,path="linear",run=false,
        exec_cb=function(_,phase) refresh(v,phase) end}
    M.views[#M.views+1]=v
    if lvgl.EVENT.DELETE then v.root:onevent(lvgl.EVENT.DELETE,function()
        v.deleted=true;v.animation:set {run=false};v.frames={};v.sequence={}
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

return M
