"""Exercise the real embedded browser and editor bridge, without user dialogs."""
import json
import os
from pathlib import Path
import time


def smoke(screenshot: Path):
    os.environ['QT_QPA_PLATFORM']='offscreen'
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
    from PySide6.QtWidgets import QApplication
    from .web_ui import MainWindow
    app=QApplication.instance() or QApplication([])
    w=MainWindow(smoke=True);w.show_editor();app.processEvents()
    assert w.isMaximized()
    # Use a deterministic viewport for the remaining DOM gesture checks.
    w.showNormal();w.resize(1440,920)
    deadline=time.monotonic()+30
    ready=[]
    while time.monotonic()<deadline:
        app.processEvents()
        ready.clear()
        w.view.page().runJavaScript('Boolean(window.s5Ready && state && document.getElementById("preview").complete)',ready.append)
        stop=time.monotonic()+.1
        while time.monotonic()<stop:app.processEvents()
        if ready and ready[0]:break
    else:raise ValueError('Interfaccia WebEngine non pronta entro 30 secondi.')
    # Real bridge mutations, rendering and undo, followed by DOM interaction.
    for action in ('add-variant',*(['add-slot']*5)):
        result=json.loads(w.bridge.command(json.dumps({'action':action})))
        if result.get('error'):raise ValueError(result['error'])
    available=w.bridge.state()['complicationSources']
    if len(available)!=59 or len(set(available.values()))!=59:
        raise ValueError('Le sorgenti delle complicazioni sono mancanti o duplicate.')
    w.bridge.send(state=w.bridge.state())
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents();ready.clear()
        w.view.page().runJavaScript('Boolean(state && state.complications.length===5 && state.variants.length===2)',ready.append)
        stop=time.monotonic()+.05
        while time.monotonic()<stop:app.processEvents()
        if ready and ready[0]:break
    else:raise ValueError('Aggiornamento del progetto non arrivato al browser.')
    # Drag a real layer with the same pointer events used by the canvas.
    original=w.bridge.project.elements[0].x
    result=[]
    w.view.page().runJavaScript('setTab("design");const layer=document.querySelector(".selection");layer.dispatchEvent(new PointerEvent("pointerdown",{clientX:100,clientY:100,bubbles:true}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:110,clientY:100}));window.dispatchEvent(new PointerEvent("pointerup"));true',result.append)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents()
        if w.bridge.project.elements[0].x!=original:break
    else:raise ValueError('Il drag nel canvas non aggiorna la posizione.')
    w.view.page().runJavaScript('document.getElementById("undo").click();true')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents()
        if w.bridge.project.elements[0].x==original:break
    else:raise ValueError('Annulla non ripristina il drag.')
    result=[]
    w.view.page().runJavaScript('setTab("variants");document.getElementById("prop-variant-accent").value="#5f87ff";document.getElementById("prop-variant-accent").dispatchEvent(new Event("change"));true',result.append)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents()
        if w.bridge.project.variants[1]['accent']=='#5f87ff':break
    else:raise ValueError('La modifica del colore dal DOM non raggiunge il progetto Python.')
    # Apply a real gallery bitmap through the visible selector and button.
    w.view.page().runJavaScript('setTab("design");selected=state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).id;paint();const model=document.querySelector("[data-preset=hour]");model.selectedIndex=1;model.dispatchEvent(new Event("change"));document.querySelector("[data-use-preset=hour]").click();true')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents()
        if w.bridge.project.variants[1].get('overrides'):break
        if w.bridge.project.elements[0].hour_asset:break
    else:raise ValueError('Il modello lancetta non viene incorporato nel progetto.')
    w.view.page().runJavaScript('setTab("slots");const card=document.querySelector("[data-slot]");const choice=card.querySelector("[data-simulate]");choice.value="weatherCurrentTemperature";choice.dispatchEvent(new Event("change"));true')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        app.processEvents()
        if w.bridge.values.get('__choices'):break
    else:raise ValueError('La simulazione della complicazione non aggiorna la preview.')
    from .editor_smoke import verify_editor
    editor_checks=verify_editor(w,app)
    from .precision_smoke import verify_precision
    editor_checks+=verify_precision(w,app)
    from .multi_smoke import verify_multi
    editor_checks+=verify_multi(w,app)
    screenshot=Path(screenshot);screenshot.parent.mkdir(parents=True,exist_ok=True)
    w.view.page().runJavaScript('document.getElementById("workspace").scrollTop=0;document.getElementById("inspector").scrollTop=0;true')
    # Let asynchronous PNG decoding and compositor catch up before grabbing.
    deadline=time.monotonic()+.7
    while time.monotonic()<deadline:app.processEvents()
    if not w.grab().save(str(screenshot)):raise ValueError('Screenshot non salvato.')
    report={'status':'passed','frontend':'Tailwind CSS 4.3.3 / QtWebEngine offline',
            'checks':['startup-window-maximized','page-loaded','QWebChannel','add-variant','five-independent-slots','58-unique-sources-plus-none','canvas-drag','DOM-undo','DOM-colour-change','DOM-hand-preset','DOM-slot-choice-preview','preview-decoded','screenshot']+editor_checks,
            'hardwareTested':False}
    screenshot.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    w.close();app.processEvents()
    print('S5 Studio Web UI smoke: OK')
