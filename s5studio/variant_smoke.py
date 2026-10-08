"""Exercise owned variant layers through the real editor DOM."""
import hashlib,json,time
from io import BytesIO
from PIL import Image
from .model import template,Element
from .render import png_bytes,render,SCENARIOS


def verify_variants(window,app):
    bridge=window.bridge;page=window.view.page()
    def until(predicate,message):
        end=time.monotonic()+8
        while time.monotonic()<end:
            app.processEvents()
            if predicate():return
        raise ValueError(message)
    def js(code):
        replies=[];page.runJavaScript(code,replies.append);until(lambda:bool(replies),'DOM varianti non risponde');return replies[0]
    def wait_dom(code,message):until(lambda:js(code),message)
    def sync():
        bridge.send(state=bridge.state())
        wait_dom('state.variantIndex==='+str(bridge.variant)+' && state.layers.length==='+str(len(bridge.state()['layers'])),'Stato della variante non sincronizzato')
    bridge.project=template('Analogico');bridge.project.ensure_independent_variants()
    bridge.variant=0;bridge.aod=False;bridge.undo_stack=[];bridge.redo_stack=[];bridge.values=dict(SCENARIOS['Normale'])
    def image(color):
        out=BytesIO();Image.new('RGBA',(480,480),color).save(out,'PNG');data=out.getvalue()
        key='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';bridge.project.assets[key]=data
        return key
    red=image('#cc2200');blue=image('#0044dd')
    background=Element(kind='image',name='Sfondo NASA',asset=red,x=0,y=0,width=480,height=480)
    bridge.project.elements.insert(0,background);bridge.project.sync_layer_order();sync()
    original=png_bytes(render(bridge.project.variant_project(0)))
    js('setTab("variants");document.getElementById("variant-add").click();true')
    until(lambda:bridge.variant==1,'Il pulsante Duplica stile non crea una copia')
    wait_dom('state.variantIndex===1 && selected==="" && S5Multi.ids().length===0','La selezione non viene svuotata cambiando stile')
    imported=bridge.import_image
    def fake_image():
        e=Element(kind='image',asset=blue);bridge.design.elements.append(e);return e
    bridge.import_image=fake_image
    try:
        js('document.getElementById("variant-image").click();true')
        until(lambda:bridge.design.elements[0].asset==blue,'Il nuovo sfondo della variante resta coperto')
    finally:bridge.import_image=imported
    wait_dom('state.layers.find(e=>e.id==='+json.dumps(background.id)+').asset==='+json.dumps(blue),'Sfondo selezionato non visibile nello stato editor')
    assert original==png_bytes(render(bridge.project.variant_project(0)))
    assert render(bridge.project.variant_project(1)).getpixel((240,420))[:3]==(0,68,221)
    js('document.getElementById("variant-edit").click();true')
    assert js('tab==="design" && !document.getElementById("variant-only")')
    js('[...document.querySelectorAll("[data-delete-layer]")].find(e=>e.dataset.deleteLayer==='+json.dumps(background.id)+').click();true')
    until(lambda:all(e.id!=background.id for e in bridge.design.elements),'Cancellazione non locale alla variante')
    assert bridge.project.elements[0].asset==red
    js('document.getElementById("undo").click();true')
    until(lambda:any(e.id==background.id and e.asset==blue for e in bridge.design.elements),'Annulla non ripristina la variante')
    js('document.querySelector("[data-add=text]").click();true')
    until(lambda:any(e.name=='Testo' for e in bridge.design.elements),'Il nuovo livello non viene aggiunto allo stile')
    added=next(e for e in bridge.design.elements if e.name=='Testo')
    wait_dom('selected==='+json.dumps(added.id),'Nuovo livello non selezionato')
    js('document.querySelector("#editing-style").value="0";document.querySelector("#editing-style").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.variant==0,'Il selettore nel pannello livelli non cambia stile')
    wait_dom('state.variantIndex===0 && !state.layers.some(e=>e.id==='+json.dumps(added.id)+') && selected===""','Il pannello mostra livelli della variante precedente')
    assert original==png_bytes(render(bridge.project.variant_project(0)))
    js('document.querySelector("#editing-style").value="1";document.querySelector("#editing-style").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.variant==1,'Ritorno alla variante non riuscito')
    wait_dom('state.variantIndex===1 && state.layers.some(e=>e.id==='+json.dumps(added.id)+')','La variante perde i suoi livelli cambiando stile')
    analog=next(e for e in bridge.design.elements if e.kind=='analog')
    js('selected='+json.dumps(analog.id)+';paint();document.getElementById("prop-hour_color").value="#ffcc11";document.getElementById("prop-hour_color").dispatchEvent(new Event("change"));true')
    until(lambda:bridge.element({'id':analog.id}).hour_color=='#ffcc11','Colore lancetta non salvato nello stile')
    assert not bridge.project.elements[1].hour_color and not bridge.project.validate()
    js('document.getElementById("toast").classList.add("hidden");document.getElementById("status").textContent="Pronto · Stili indipendenti";true')
    return ['variant-clone-owns-independent-layers','variant-background-replaces-original-image-locally',
            'variant-background-preview-is-real','variant-delete-and-undo-are-local',
            'variant-add-layer-is-local','inspector-style-selector-switches-layer-list',
            'variant-switch-clears-single-and-multi-selection','variant-switch-retains-owned-layers',
            'variant-hand-colour-is-local-without-a-checkbox']
