"""Pixel mapping, source help, zoom and compass in the real embedded browser."""
import json
import time


def verify_precision(window,app):
    from .render import hand_image,png_bytes
    bridge=window.bridge;page=window.view.page();checks=[]
    def until(predicate,message):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate():return
        raise ValueError(message)
    def js(code):
        replies=[];page.runJavaScript(code,replies.append);until(lambda:bool(replies),'JavaScript non risponde');return replies[0]
    def command(action,**args):
        before=len(bridge.undo_stack)
        js('send('+json.dumps(action)+','+json.dumps(args)+');true')
        until(lambda:len(bridge.undo_stack)>before,'Il comando non è arrivato: '+action)
        until(lambda:js('state.canUndo && !document.getElementById("toast").textContent.includes("Proprietà non supportata")'),'Stato non aggiornato')
    def wait_dom(expression):until(lambda:js(expression),'DOM non aggiornato: '+expression)
    js('setTab("design");document.querySelector("[data-add=pointer]").click();true')
    until(lambda:any(e.kind=='pointer' for e in bridge.project.elements),'Lancetta piccola non creata')
    pointer=next(e for e in bridge.project.elements if e.kind=='pointer')
    wait_dom('selected==='+json.dumps(pointer.id)+' && document.querySelector("[data-preset=second]")!==null')
    preset=next(p for p in bridge.hand_presets if p['small'] and p['shadow'] and not p['aod'])
    command('hand-preset',id=pointer.id,hand='second',preset=preset['id'])
    wait_dom('document.querySelector("[data-pivot-hand=second] img")?.complete===true')
    preview=bridge.state()['handPreviews'][pointer.id]['second']
    source_x=max(0,min(479,preview['originX']+preview['width']//2));source_y=max(0,min(479,preview['originY']+preview['height']*2//3))
    js('(()=>{const image=document.querySelector("[data-pivot-hand=second] img"),r=image.getBoundingClientRect();image.parentElement.dispatchEvent(new MouseEvent("click",{bubbles:true,clientX:r.left+('+str(source_x-preview['originX'])+'+.5)/'+str(preview['width'])+'*r.width,clientY:r.top+('+str(source_y-preview['originY'])+'+.5)/'+str(preview['height'])+'*r.height}));return true;})()')
    until(lambda:(bridge.element({'id':pointer.id}).second_anchor_x,bridge.element({'id':pointer.id}).second_anchor_y)==(source_x,source_y),'Il clic non imposta il pixel sorgente esatto')
    assert not bridge.element({'id':pointer.id}).pointer_end_pivot
    wait_dom('document.getElementById("prop-second_anchor_x").value==='+json.dumps(str(source_x)))
    wait_dom('document.getElementById("prop-second_anchor_y").value==='+json.dumps(str(source_y)))
    assert not js('document.querySelector("[data-prop=pointer_end_pivot]").checked')
    checks.extend(['source-pixel-pivot-click','pivot-click-disables-endpoint','manual-pivot-fields-update','click-preview-is-applied-asset'])

    assert js('document.querySelector("[data-prop=source]").options.length')==62
    original=bridge.element({'id':pointer.id}).source
    js('document.querySelector("[data-prop=source]").parentElement.querySelector(".select-trigger").click();[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="timeHourLow").dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));true')
    assert js('document.querySelector(".select-description").textContent.includes("vale 4")')
    assert bridge.element({'id':pointer.id}).source==original
    js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="timeHourHigh").dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));true')
    assert js('document.querySelector(".select-description").textContent.includes("vale 1")')
    js('S5Selectors.close();true')
    checks.extend(['58-native-and-four-lua-pointer-sources-without-alias-duplicates','source-help-on-hover','hour-digit-options-have-distinct-labels','source-help-does-not-commit'])

    analog=next(e for e in bridge.project.elements if e.kind=='analog' and not e.aod)
    js('selected='+json.dumps(analog.id)+';paint();true')
    before=png_bytes(hand_image(analog,'hour',bridge.project)[0])
    js('document.getElementById("prop-hour_length").value="65";document.getElementById("prop-hour_length").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':analog.id}).hour_length==65,'Lunghezza non salvata')
    wait_dom('document.getElementById("prop-hour_length").value==="65"')
    assert png_bytes(hand_image(bridge.element({'id':analog.id}),'hour',bridge.project)[0])!=before
    before=png_bytes(hand_image(bridge.element({'id':analog.id}),'hour',bridge.project)[0])
    js('document.getElementById("prop-hour_width").value="27";document.getElementById("prop-hour_width").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':analog.id}).hour_width==27,'Spessore non salvato')
    assert png_bytes(hand_image(bridge.element({'id':analog.id}),'hour',bridge.project)[0])!=before
    checks.extend(['imported-clock-length-control-changes-bitmap','imported-clock-thickness-control-changes-bitmap'])

    js('selected='+json.dumps(pointer.id)+';paint();document.getElementById("preview-zoom").value="200";document.getElementById("preview-zoom").dispatchEvent(new Event("change"));true')
    assert js('document.getElementById("canvas").getBoundingClientRect().width')==960
    old=bridge.element({'id':pointer.id}).x
    js('document.querySelector(".selection.selected").dispatchEvent(new PointerEvent("pointerdown",{bubbles:true,clientX:100,clientY:100}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:120,clientY:100}));window.dispatchEvent(new PointerEvent("pointerup"));true')
    until(lambda:bridge.element({'id':pointer.id}).x==old+10,'Il drag con zoom non rispetta le coordinate native')
    wait_dom('state.layers.find(e=>e.id==='+json.dumps(pointer.id)+').x==='+str(old+10))
    js('document.getElementById("canvas").focus();window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",cancelable:true}));true')
    until(lambda:bridge.element({'id':pointer.id}).x==old+11,'Lo zoom altera lo spostamento con le frecce')
    js('document.getElementById("zoom-selection").click();true')
    assert js('document.getElementById("stage-viewport").scrollWidth>document.getElementById("stage-viewport").clientWidth')
    js('document.getElementById("zoom-reset").click();true')
    assert js('S5Precision.getZoom()===100 && document.getElementById("canvas").getBoundingClientRect().width===480')
    checks.extend(['preview-zoom-200-percent','zoomed-drag-native-pixels','zoomed-keyboard-one-pixel','zoom-scrolls-and-centres-selection','zoom-reset'])

    js('document.querySelector("[data-add=compass]").click();true')
    until(lambda:any(e.kind=='compass' for e in bridge.project.elements),'Bussola non aggiunta')
    compass=next(e for e in bridge.project.elements if e.kind=='compass')
    wait_dom('selected==='+json.dumps(compass.id)+' && document.getElementById("compass-preset")!==null')
    assert js('document.getElementById("compass-preset").options.length')==11
    candidate=next(c for c in bridge.compass_presets if c['name']=='Bouldering' and c['kind']=='Rosa completa')
    js('document.getElementById("compass-preset").parentElement.querySelector(".select-trigger").click();[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==='+json.dumps(candidate['id'])+').dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));true')
    assert js('document.getElementById("compass-preview").src')==candidate['thumbnail']
    assert compass.compass_preset!=candidate['id']
    js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==='+json.dumps(candidate['id'])+').click();document.getElementById("compass-apply").click();true')
    until(lambda:bridge.element({'id':compass.id}).compass_preset==candidate['id'],'Modello bussola non applicato')
    assert (compass.source,compass.value_start,compass.value_range,compass.angle_start,compass.angle_range)==('systemSensorCompass',0,360,0,-360)
    before=bridge.state()['preview']
    js('document.getElementById("compass-heading").value="270";document.getElementById("compass-heading").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.values.get('systemSensorCompass')==270,'Simulazione bussola non applicata')
    assert bridge.state()['preview']!=before
    wait_dom('state.values.systemSensorCompass===270')
    checks.extend(['compass-is-independent-layer','ten-compass-presets','compass-hover-preview-without-commit','compass-model-explicit-apply','compass-uses-real-sensor-counterrotation','compass-heading-simulation'])
    assert not bridge.project.validate()
    return checks
