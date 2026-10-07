"""Real DOM Ctrl-selection, group drag, keyboard, alignment, undo and bindings."""
import json,time


def verify_multi(window,app):
    bridge=window.bridge;page=window.view.page();checks=[]
    def until(predicate,message):
        end=time.monotonic()+8
        while time.monotonic()<end:
            app.processEvents()
            if predicate():return
        raise ValueError(message)
    def js(code):
        replies=[];page.runJavaScript('(()=>{return eval('+json.dumps(code)+');})()',replies.append)
        until(lambda:bool(replies),'DOM non risponde');return replies[0]
    def command(action,**params):
        reply=json.loads(bridge.command(json.dumps({'action':action,**params})))
        if reply.get('error'):raise ValueError(reply['error'])
        bridge.send(state=reply['state']);return reply
    ids=[]
    for x,y in [(60,80),(200,150)]:
        key=command('add',kind='rect')['selectedLayer'];ids.append(key)
        command('edit',id=key,changes={'x':x,'y':y,'width':40,'height':40})
    until(lambda:js('state.layers.some(e=>e.id==='+json.dumps(ids[1])+'&&e.x===200&&e.width===40)'),'Livelli non sincronizzati')
    first,second=map(json.dumps,ids)
    js(f'setTab("design");S5Multi.clear();document.querySelector(`[data-element="${{{first}}}"]`).dispatchEvent(new PointerEvent("pointerdown",{{bubbles:true,ctrlKey:true,clientX:100,clientY:100}}));true')
    js(f'document.querySelector(`[data-element="${{{second}}}"]`).dispatchEvent(new PointerEvent("pointerdown",{{bubbles:true,ctrlKey:true,clientX:200,clientY:200}}));true')
    assert js('S5Multi.ids().length')==2
    assert js('document.querySelectorAll(".selection.selected").length')==2
    assert js('document.querySelectorAll("[data-align-group]").length')==6
    assert js('document.querySelectorAll(".resize-handle").length')==0
    checks+=['ctrl-click-multiple-canvas-levels','multiple-selection-visible','group-six-align-controls','group-hides-individual-resize']
    js(f'document.querySelector(`[data-layer="${{{first}}}"]`).dispatchEvent(new MouseEvent("click",{{bubbles:true,ctrlKey:true}}));true')
    assert js('S5Multi.ids().length')==1
    js(f'document.querySelector(`[data-layer="${{{first}}}"]`).dispatchEvent(new MouseEvent("click",{{bubbles:true,ctrlKey:true}}));true')
    assert js('S5Multi.ids().length')==2
    checks.append('ctrl-click-toggle-in-layer-panel')
    js('document.getElementById("preview-zoom").value="200";document.getElementById("preview-zoom").dispatchEvent(new Event("change"));true')
    js(f'document.querySelector(`[data-element="${{{first}}}"]`).dispatchEvent(new PointerEvent("pointerdown",{{bubbles:true,clientX:100,clientY:100}}));window.dispatchEvent(new PointerEvent("pointermove",{{clientX:120,clientY:120}}));window.dispatchEvent(new PointerEvent("pointerup"));true')
    until(lambda:bridge.element({'id':ids[0]}).x==70,'Drag gruppo non applicato')
    assert (bridge.element({'id':ids[1]}).x,bridge.element({'id':ids[1]}).y)==(210,160)
    assert bridge.element({'id':ids[0]}).y==90
    until(lambda:js('state.layers.find(e=>e.id==='+first+').x===70'),'DOM drag gruppo non aggiornato')
    checks+=['group-drag-at-200-percent-native-coordinates','group-preserves-relative-offsets']
    js('document.getElementById("canvas").focus();window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",cancelable:true}));true')
    until(lambda:bridge.element({'id':ids[0]}).x==71,'Frecce gruppo non applicate')
    assert bridge.element({'id':ids[1]}).x==211
    until(lambda:js('state.layers.find(e=>e.id==='+first+').x===71'),'DOM frecce gruppo non aggiornato')
    js('document.querySelector("[data-align-group=center-x]").click();true')
    until(lambda:bridge.element({'id':ids[0]}).x==150,'Allineamento gruppo non applicato')
    assert bridge.element({'id':ids[1]}).x==290
    js('document.getElementById("undo").click();true')
    until(lambda:bridge.element({'id':ids[0]}).x==71,'Annulla gruppo non atomico')
    assert bridge.element({'id':ids[1]}).x==211
    checks+=['group-keyboard-one-pixel','group-align-keeps-internal-spacing','group-undo-is-atomic']
    js('document.getElementById("zoom-reset").click();S5Multi.clear();true')
    analog=next(e for e in bridge.project.elements if e.kind=='analog' and not e.aod)
    js('selected='+json.dumps(analog.id)+';variantOnly=false;paint();const c=document.querySelector("[data-prop=smooth_seconds]");c.checked=true;c.dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':analog.id}).smooth_seconds,'Flag sweep non salvato')
    checks.append('sweep-flag-reaches-project')
    key=command('add',kind='pointer')['selectedLayer']
    until(lambda:js('state.layers.some(e=>e.id==='+json.dumps(key)+')'),'Lancetta piccola non pronta')
    js('selected='+json.dumps(key)+';paint();true')
    assert js('Object.keys(state.luaSources).length')==4
    assert js('document.querySelector("[data-prop=source]").options.length')==62
    js('const s=document.querySelector("[data-prop=source]");s.value="studioDecisecond";s.dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':key}).source=='studioDecisecond','Abbinamento decimi non salvato')
    assert bridge.element({'id':key}).value_range==10
    until(lambda:js('state.layers.find(e=>e.id==='+json.dumps(key)+').source==="studioDecisecond"'),'DOM decimi non pronto')
    js('const s=document.querySelector("[data-prop=source]");s.value="studioChronoSecond";s.dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':key}).source=='studioChronoSecond','Abbinamento Crono non salvato')
    assert bridge.element({'id':key}).value_range==60
    checks+=['four-distinct-lua-bindings-in-small-hand-menu','decisecond-binding-sets-ten-values','chrono-binding-sets-sixty-values']
    for expected in ('running','stopped','reset'):
        js('document.getElementById("chrono-preview").click();true')
        until(lambda:bridge.chrono_state==expected,'Ciclo Crono anteprima non valido')
        until(lambda:js('state.chronoState==='+json.dumps(expected)),'DOM Crono non aggiornato')
    checks.append('chrono-preview-start-stop-reset')
    assert not bridge.project.validate()
    return checks
