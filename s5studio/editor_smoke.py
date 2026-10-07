"""Exercise editor gestures and selector commits in the real QtWebEngine DOM."""
from io import BytesIO
import json,time,hashlib
from PIL import Image

def verify_editor(window,app):
    bridge=window.bridge;page=window.view.page();checks=[]
    def until(predicate,message,timeout=6):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            app.processEvents()
            if predicate():return
        raise ValueError(message+' | ordine='+str(bridge.project.layer_order))
    def js(code):
        replies=[];page.runJavaScript(code,replies.append)
        until(lambda:bool(replies),'JavaScript non risponde')
        return replies[0]
    def wait_js(code,message):until(lambda:js(code),message)
    def sync():
        token=time.time();bridge.send(state=bridge.state())
        js('window._editorSync='+str(token)+';true')
        wait_js('state.layers.length==='+str(len(bridge.state()['layers'])),'Livelli non aggiornati')
    js('setTab("design");document.querySelector("#scenario").parentElement.querySelector(".select-trigger").click();true')
    assert js('document.querySelector(".select-popup")!==null')
    before=bridge.scenario
    js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="Dati assenti").dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="Dati assenti").dispatchEvent(new MouseEvent("mousemove",{bubbles:true}));true')
    assert bridge.scenario==before and js('document.getElementById("scenario").value')==before
    assert js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="Dati assenti").classList.contains("is-hovered")')
    assert js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="Dati assenti").getAttribute("aria-selected")')=='false'
    js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==="Dati assenti").click();true')
    until(lambda:bridge.scenario=='Dati assenti','Il clic nel menu non conferma')
    js('document.querySelector("#scenario").parentElement.querySelector(".select-trigger").click();document.querySelector(".select-option").click();true')
    until(lambda:bridge.scenario=='Normale','Scenario non ripristinato')
    wait_js('[...document.querySelectorAll("select")].every(e=>getComputedStyle(e).display==="none")','Un menu usa ancora il popup nativo')
    checks.extend(['dropdown-hover-does-not-commit','dropdown-hover-highlights-without-selection','dropdown-click-commits','all-native-selects-replaced'])
    assert js('document.body.textContent.includes("Version 0.10")&&!document.body.textContent.includes("WATCHFACE DESIGNER")')
    checks.append('header-Version-0.10')

    analog=next(e for e in bridge.project.elements if e.kind=='analog' and not e.aod)
    js('selected='+json.dumps(analog.id)+';paint();true')
    js('document.querySelector("[data-clear-hand=hour]").click();true')
    until(lambda:bridge.element({'id':analog.id}).hour_asset=='','La galleria non ritorna allo stato vuoto')
    wait_js('document.getElementById("preset-hour").hidden','Anteprima vuota non aggiornata')
    assert js('document.getElementById("preset-hour").hidden&&!document.getElementById("preset-hour").hasAttribute("src")&&document.querySelector("[data-use-preset=hour]").disabled')
    original_asset='';undo_count=len(bridge.undo_stack)
    presets=[p for p in bridge.hand_presets if p['hand']=='hour'][:2]
    js('document.querySelector("[data-preset=hour]").parentElement.querySelector(".select-trigger").click();true')
    assert js('document.querySelector(".select-popup").getBoundingClientRect().bottom<=window.innerHeight-7')
    for preset in presets:
        js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==='+json.dumps(preset['id'])+').dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));true')
        assert js('document.getElementById("preset-hour").src')==preset['thumbnail']
        assert js('document.querySelector(".select-graphic-preview img").src')==preset['thumbnail']
        assert js('document.querySelector("[data-preset=hour]").value')==''
        assert js('[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==='+json.dumps(preset['id'])+').classList.contains("is-hovered")')
        assert bridge.element({'id':analog.id}).hour_asset==original_asset and len(bridge.undo_stack)==undo_count
    js('S5Selectors.close();true')
    assert js('document.getElementById("preset-hour").hidden&&!document.getElementById("preset-hour").hasAttribute("src")')
    js('document.querySelector("[data-preset=hour]").parentElement.querySelector(".select-trigger").click();[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value==='+json.dumps(presets[0]['id'])+').click();true')
    assert js('!document.getElementById("preset-hour").hidden&&!document.querySelector("[data-use-preset=hour]").disabled')
    assert bridge.element({'id':analog.id}).hour_asset==original_asset
    js('document.querySelector("[data-use-preset=hour]").click();true')
    until(lambda:bridge.element({'id':analog.id}).hour_asset!='','Il modello scelto non si applica')
    applied=bridge.element({'id':analog.id})
    assert applied.hour_preset==presets[0]['id']
    for role,identity in presets[0]['setMembers'].items():assert getattr(applied,role+'_preset')==identity
    js('document.querySelector("[data-prop=show_shadows]").click();true')
    until(lambda:bridge.element({'id':analog.id}).show_shadows is False,'Il flag ombre non si disattiva')
    wait_js('document.querySelector("[data-prop=show_shadows]").checked===false','Flag ombre non aggiornato nel DOM')
    js('document.querySelector("[data-prop=show_shadows]").click();true')
    until(lambda:bridge.element({'id':analog.id}).show_shadows is True,'Il flag ombre non si riattiva')
    checks.extend(['hour-model-auto-pairs-matching-set','shadow-visibility-checkbox'])
    checks.extend(['empty-hand-preview-has-no-image-src','hand-hover-shows-both-previews-without-commit','hand-preview-restores-on-menu-close','hand-model-requires-explicit-apply'])
    for hand,color in [('hour','#ff6b77'),('minute','#67f4bc'),('second','#a093ff')]:
        js('document.getElementById("prop-'+hand+'_color").value='+json.dumps(color)+';document.getElementById("prop-'+hand+'_color").dispatchEvent(new Event("change"));true')
        until(lambda:getattr(bridge.element({'id':analog.id}),hand+'_color')==color,'Colore lancetta non salvato')
    checks.append('individual-hour-minute-second-colours')

    # Import the test image directly into the same project; all subsequent
    # editing actions use the DOM, so no user file dialog is opened.
    raw=BytesIO();Image.new('RGBA',(240,120),(100,160,230,255)).save(raw,'PNG');data=raw.getvalue()
    from .model import Element
    key='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';bridge.project.assets[key]=data
    image=Element(kind='image',name='Immagine test UI',asset=key,x=160,y=160,width=160,height=80)
    bridge.project.elements.append(image);bridge.project.sync_layer_order();sync()
    js('selected='+json.dumps(image.id)+';paint();document.getElementById("prop-opacity").value="77";document.getElementById("prop-opacity").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':image.id}).opacity==196,'Opacità 77% non applicata')
    assert js('document.getElementById("prop-opacity").value')=='77'
    js('const resize=document.querySelector(".selection.selected [data-resize=se]");resize.dispatchEvent(new PointerEvent("pointerdown",{clientX:100,clientY:100,bubbles:true}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:100+32*document.getElementById("canvas").getBoundingClientRect().width/480,clientY:100+16*document.getElementById("canvas").getBoundingClientRect().width/480}));window.dispatchEvent(new PointerEvent("pointerup"));true')
    until(lambda:bridge.element({'id':image.id}).width==192,'Maniglia non ridimensiona immagine')
    assert bridge.element({'id':image.id}).height==96
    js('document.getElementById("image-cover").click();true')
    until(lambda:bridge.element({'id':image.id}).width==480,'Immagine non riempie il quadrante')
    assert (bridge.element({'id':image.id}).x,bridge.element({'id':image.id}).y)==(0,0)
    checks.extend(['image-opacity-percentage','image-resize-handle-keeps-aspect','image-fit-watch-rim'])
    js('document.getElementById("image-scale").value="150";document.getElementById("image-scale").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':image.id}).width==720,'Scala oltre 480 bloccata')
    assert (bridge.element({'id':image.id}).x,bridge.element({'id':image.id}).y)==(-120,-120)
    assert bridge.element({'id':image.id}).height==720 and not bridge.project.validate()
    js('document.querySelector(".selection.selected").dispatchEvent(new PointerEvent("pointerdown",{clientX:100,clientY:100,bubbles:true}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:100-12*document.getElementById("canvas").getBoundingClientRect().width/480,clientY:100+12*document.getElementById("canvas").getBoundingClientRect().width/480}));window.dispatchEvent(new PointerEvent("pointerup"));true')
    until(lambda:bridge.element({'id':image.id}).x==-132,'Immagine ingrandita non trascinabile oltre il bordo')
    assert bridge.element({'id':image.id}).y==-108
    js('document.getElementById("canvas").focus();for(let i=0;i<5;i++)window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",cancelable:true}));window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowUp",shiftKey:true,cancelable:true}));true')
    until(lambda:bridge.element({'id':image.id}).x==-127 and bridge.element({'id':image.id}).y==-118,'Frecce ripetute o Maiusc non spostano di pixel')
    before=(bridge.element({'id':image.id}).x,bridge.element({'id':image.id}).y)
    js('document.getElementById("prop-x").focus();document.getElementById("prop-x").dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",bubbles:true,cancelable:true}));true')
    assert before==(bridge.element({'id':image.id}).x,bridge.element({'id':image.id}).y)
    js('document.getElementById("image-center").click();true')
    until(lambda:bridge.element({'id':image.id}).x==-120 and bridge.element({'id':image.id}).y==-120,'Centra immagine non funziona')
    checks.extend(['image-scale-beyond-480','oversized-image-negative-canvas-drag','arrow-keys-accumulate-one-pixel','shift-arrows-ten-pixels','arrows-preserve-input-editing','center-oversized-image'])

    count=len(bridge.project.complications);js('document.getElementById("add-complication").click();true')
    until(lambda:len(bridge.project.complications)==count+1,'Complicazione non aggiunta')
    slot=bridge.project.complications[-1];sid=slot['id'];wait_js('selected==='+json.dumps(sid),'Complicazione nuova non selezionata')
    assert slot['frame']=='none' and not slot['showLabel'] and not slot['showUnit']
    sx=slot['x'];js('document.getElementById("canvas").focus();window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowRight",cancelable:true}));true')
    until(lambda:bridge.layer(sid)['x']==sx+1,'Frecce non spostano una complicazione')
    assert js('[...document.querySelectorAll("[data-layer]")].filter(e=>e.dataset.layer==='+json.dumps(sid)+').length')==1
    initial=slot['x'];js('document.querySelector(".selection.selected").dispatchEvent(new PointerEvent("pointerdown",{clientX:100,clientY:100,bubbles:true}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:109,clientY:100}));window.dispatchEvent(new PointerEvent("pointerup"));true')
    until(lambda:bridge.layer(sid)['x']!=initial,'Complicazione non trascinabile')
    js('document.getElementById("undo").click();true');until(lambda:bridge.layer(sid)['x']==initial,'Undo complicazione non funziona')
    # Drop in the lower half of an image row: value must end up below it.
    js('const row=[...document.querySelectorAll("[data-layer]")].find(e=>e.dataset.layer==='+json.dumps(image.id)+');const dt=new DataTransfer();dt.setData("text/plain",'+json.dumps(sid)+');row.dispatchEvent(new DragEvent("drop",{bubbles:true,dataTransfer:dt,clientY:row.getBoundingClientRect().bottom-1}));true')
    until(lambda:bridge.project.layer_order.index(sid)<bridge.project.layer_order.index(image.id),'Il drop non cambia ordine')
    js('[...document.querySelectorAll("[data-delete-layer]")].find(e=>e.dataset.deleteLayer==='+json.dumps(sid)+').click();true');until(lambda:len(bridge.project.complications)==count,'Cancellazione dalla lista non funziona')
    js('document.getElementById("undo").click();true');until(lambda:len(bridge.project.complications)==count+1,'Undo cancellazione non funziona')
    checks.extend(['new-complication-is-value-only-layer','complication-canvas-drag','layer-drag-reorder','delete-layer-row','undo-deletion'])

    js('document.querySelector("[data-add=pointer]").click();true')
    until(lambda:any(e.kind=='pointer' for e in bridge.project.elements),'Lancetta piccola non aggiunta')
    pointer=next(e for e in bridge.project.elements if e.kind=='pointer');wait_js('selected==='+json.dumps(pointer.id),'Lancetta piccola non selezionata')
    px=pointer.x;js('document.getElementById("canvas").focus();window.dispatchEvent(new KeyboardEvent("keydown",{key:"ArrowLeft",cancelable:true}));true')
    until(lambda:bridge.element({'id':pointer.id}).x==px-1,'Frecce non spostano una lancetta piccola')
    js('const source=document.querySelector("[data-prop=source]");source.value="systemStatusBattery";source.dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':pointer.id}).source=='systemStatusBattery','Sorgente lancetta piccola non applicata')
    assert bridge.element({'id':pointer.id}).value_range==100
    js('document.getElementById("prop-name").focus();document.getElementById("prop-name").dispatchEvent(new KeyboardEvent("keydown",{key:"Delete",bubbles:true}));true')
    assert any(e.id==pointer.id for e in bridge.project.elements)
    js('document.getElementById("prop-name").blur();document.body.dispatchEvent(new KeyboardEvent("keydown",{key:"Delete",bubbles:true}));true')
    until(lambda:not any(e.id==pointer.id for e in bridge.project.elements),'Tasto Canc non elimina')
    checks.extend(['arrow-keys-move-complication-and-small-pointer','small-pointer-layer-and-live-source','delete-key-preserves-editing','delete-key-removes-selected-layer'])
    # Exercise the real Save button three times without opening user dialogs.
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from unittest.mock import patch
    from PySide6.QtWidgets import QFileDialog
    build_dir=bridge.root/'build';build_dir.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='ui-save-',dir=build_dir) as temp:
        target=Path(temp).resolve();assert target.is_relative_to(build_dir.resolve())
        names=[str(target/'primo'),str(target/'secondo.s5faceproj'),''];calls=[]
        def choose(*args):calls.append(args[2]);return names[len(calls)-1],'Progetti S5'
        with patch.object(QFileDialog,'getSaveFileName',choose):
            js('document.getElementById("save").click();true')
            until(lambda:len(calls)==1 and bridge.path==target/'primo.s5faceproj','Il primo Salva non chiede il nome')
            js('document.getElementById("save").click();true')
            until(lambda:len(calls)==2 and bridge.path==target/'secondo.s5faceproj','Il secondo Salva non chiede il nome')
            current=bridge.path;bridge.dirty=True
            js('document.getElementById("save").click();true')
            until(lambda:len(calls)==3,'Salva non apre il dialogo dopo un progetto già salvato')
            assert bridge.path==current and bridge.dirty
        assert (target/'primo.s5faceproj').is_file() and (target/'secondo.s5faceproj').is_file()
        assert calls[1].endswith('primo.s5faceproj') and calls[2].endswith('secondo.s5faceproj')
    checks.extend(['every-save-button-click-asks-filename','save-cancel-preserves-path-and-dirty'])
    return checks
