"""Capture hand gallery empty/hover states in the real embedded browser."""
from pathlib import Path
import os,sys,time,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
app=QApplication([]);w=MainWindow(smoke=True);w.show()
def js(code):
    result=[];w.view.page().runJavaScript(code,result.append);end=time.monotonic()+10
    while not result and time.monotonic()<end:app.processEvents()
    if not result:raise RuntimeError('DOM timeout')
    return result[0]
def until(predicate):
    end=time.monotonic()+10
    while time.monotonic()<end:
        app.processEvents()
        if predicate():return
    raise RuntimeError('UI timeout')
def capture(label):
    until(lambda:js('document.getElementById("preview").complete'))
    end=time.monotonic()+.6
    while time.monotonic()<end:app.processEvents()
    assert w.grab().save(str(ROOT/f'docs/screenshots/editor-0.7-{label}.png'))
until(lambda:js('Boolean(window.s5Ready&&state)'))
js('selected=state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).id;paint();document.querySelector("[data-preset=hour]").parentElement.scrollIntoView({block:"center"});true')
assert js('document.getElementById("preset-hour").hidden&&!document.getElementById("preset-hour").hasAttribute("src")')
capture('empty')
js('document.querySelector("[data-preset=hour]").parentElement.querySelector(".select-trigger").click();[...document.querySelectorAll(".select-option")].find(e=>e.dataset.value).dispatchEvent(new MouseEvent("mouseover",{bubbles:true}));true')
until(lambda:js('document.querySelector(".select-graphic-preview img").complete&&document.querySelector(".select-graphic-preview img").naturalWidth>0'))
assert js('document.querySelector("[data-preset=hour]").value')==''
assert js('document.querySelector(".select-popup").getBoundingClientRect().bottom<=window.innerHeight-7')
capture('hover');w.close();app.processEvents()
print('Empty/hover gallery screenshots: OK')
