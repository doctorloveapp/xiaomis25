"""Source UI checks for the opt-in flag, preview cycle and AOD cancellation."""
import json,time
from .model import template,Element


def verify_pro(window,app):
    bridge=window.bridge;page=window.view.page()
    def until(predicate):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate():return
        raise AssertionError('Crono Pro UI check timed out')
    def js(code):
        result=[];page.runJavaScript(code,result.append);until(lambda:bool(result));return result[0]
    bridge.project=template('Analogico');bridge.variant=0;bridge.aod=False
    bridge.project.ensure_independent_variants()
    analog=bridge.project.elements[0]
    bridge.send(state=bridge.state())
    until(lambda:js('state.layers.some(e=>e.id==='+json.dumps(analog.id)+')'))
    js('variantOnly=false;selected='+json.dumps(analog.id)+';setTab("design");paint();true')
    assert not js('document.querySelector("[data-prop=chrono_pro]").checked')
    js('const c=document.querySelector("[data-prop=chrono_pro]");c.checked=true;c.dispatchEvent(new Event("change"));true')
    until(lambda:analog.chrono_pro)
    until(lambda:js('state.chronoPro&&document.getElementById("chrono-preview").textContent==="Prepara Crono Pro"'))
    assert analog.second_hand
    pointer=Element(kind='pointer',source='second',value_range=60,smooth_seconds=True)
    bridge.project.elements.insert(0,pointer);bridge.send(state=bridge.state())
    until(lambda:js('state.layers.some(e=>e.id==='+json.dumps(pointer.id)+')'))
    js('selected='+json.dumps(pointer.id)+';paint();const s=document.querySelector("[data-prop=source]");s.value="studioChronoDecisecond";s.dispatchEvent(new Event("change"));true')
    until(lambda:pointer.source=='studioChronoDecisecond')
    assert pointer.value_range==10
    js('document.getElementById("chrono-preview").click();true')
    until(lambda:bridge.chrono_state=='arming')
    bridge.pro_preview.transition['started']-=400;bridge.preview_tick()
    until(lambda:js('state.chronoState==="ready"&&!document.getElementById("chrono-preview").disabled'))
    js('document.getElementById("chrono-preview").click();true');until(lambda:bridge.chrono_state=='running')
    bridge.pro_preview.started-=6456;bridge.preview_tick()
    value=bridge.values['__proValues'][pointer.id]
    assert value==int(value) and 0<=value<10 and pointer.smooth_seconds
    js('document.getElementById("chrono-preview").click();true');until(lambda:bridge.chrono_state=='stopped')
    js('document.getElementById("chrono-preview").click();true');until(lambda:bridge.chrono_state=='resetting')
    bridge.aod=True;bridge.send(state=bridge.state())
    assert bridge.pro_preview.transition is None and bridge.chrono_state=='rest'
    until(lambda:js('document.getElementById("chrono-preview").disabled'))
    bridge.aod=False;bridge.send(state=bridge.state())
    assert not bridge.project.validate()
    return ['chrono-pro-flag-default-off','chrono-pro-flag-in-second-hand-properties',
            'chrono-pro-enables-main-seconds','chrono-decisecond-binding-ten-values',
            'chrono-pro-preview-prepare-ready-start-stop-reset',
            'chrono-pro-running-deciseconds-ignore-smooth','chrono-pro-preview-aod-cancels-reset']
