-- Original event-driven bitmap data renderer. No polling, timers or animations.
-- dataman delivers Xiaomi numeric sources in Q8, as in the public PointerTest.
local lvgl = require("lvgl")
local dataman = require("dataman")
local M = {views={}, active=true}

function M.format(c,value)
    if type(value)~="number" or value~=value or math.abs(value)==math.huge then
        return string.rep("-",c.count)
    end
    local text
    if c.decimals>0 then
        text=string.format("%."..c.decimals.."f",value)
        if #text>c.count then text=string.rep("-",c.count) end
    else
        value=value<0 and math.ceil(value) or math.floor(value)
        value=math.max(-(10^(c.count-1)-1),math.min(value,10^c.count-1))
        text=string.format("%.0f",value)
    end
    if c.leadingZero and #text<c.count then
        if text:sub(1,1)=="-" then text="-"..string.rep("0",c.count-#text)..text:sub(2)
        else text=string.rep("0",c.count-#text)..text end
    end
    return text
end

function M.draw(v)
    if not M.active or v.deleted or v.screenOn==false then return end
    local text=M.format(v.config,v.value)
    if text==v.last then return end
    v.last=text
    local positions=v.config.glyphs[#text]
    for i,img in ipairs(v.images) do
        local item=positions and positions[i] and positions[i][text:sub(i,i)]
        if item then
            img:set {x=item.x,y=item.y,src=SCRIPT_PATH..item.src}
            img:clear_flag(lvgl.FLAG.HIDDEN)
        else img:add_flag(lvgl.FLAG.HIDDEN) end
    end
end

function M.add(scene,config)
    local root=lvgl.Object(scene,{x=0,y=0,w=480,h=480,bg_opa=0,border_width=0,pad_all=0})
    root:clear_flag(lvgl.FLAG.SCROLLABLE);root:clear_flag(lvgl.FLAG.CLICKABLE)
    local v={config=config,root=root,images={},screenOn=true}
    for i=1,config.count do
        local item=config.glyphs[config.count][i]["-"]
        local img=root:Image {x=item.x,y=item.y,src=SCRIPT_PATH..item.src}
        img:clear_flag(lvgl.FLAG.CLICKABLE)
        v.images[i]=img
    end
    M.views[#M.views+1]=v
    M.draw(v)
    if lvgl.EVENT.DELETE then root:onevent(lvgl.EVENT.DELETE,function() v.deleted=true end) end
    dataman.subscribe(config.source,root,function(_,raw)
        if v.deleted then return end
        v.value=type(raw)=="number" and raw~=2147483647 and raw~=4294967295 and raw~=-2147483648 and raw~=2147483648 and raw/256 or nil
        M.draw(v)
    end)
    if not M.lifecycle then
        M.lifecycle=true
        local previous=ScreenStateChangedCB
        ScreenStateChangedCB=function(pre,now,reason)
            if previous then previous(pre,now,reason) end
            for _,view in ipairs(M.views) do
                if not view.deleted then
                    local visible=(now=="ON" and not view.config.aod) or (now=="AOD" and view.config.aod)
                    view.screenOn=visible
                    if visible then view.root:clear_flag(lvgl.FLAG.HIDDEN) else view.root:add_flag(lvgl.FLAG.HIDDEN) end
                    if visible then M.draw(view) end
                end
            end
        end
        local pause,resume=pageOnPause,pageOnResume
        pageOnPause=function() if pause then pause() end;M.active=false end
        pageOnResume=function()
            if resume then resume() end
            M.active=true
            for _,view in ipairs(M.views) do M.draw(view) end
        end
    end
    return v
end
return M
