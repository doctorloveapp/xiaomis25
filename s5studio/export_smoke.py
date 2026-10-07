"""Check completed/failed build events in the real embedded editor DOM."""
import json
import tempfile
import threading
import time
from pathlib import Path


def verify_export(window,app):
    from . import web_ui
    bridge=window.bridge;original=web_ui.build
    checks=[]
    def until(predicate,message):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            app.processEvents()
            if predicate():return
        raise ValueError(message)
    def js(code):
        result=[];window.view.page().runJavaScript('(()=>{'+code+'})()',result.append)
        until(lambda:bool(result),'Risposta JavaScript esportazione mancante')
        return result[0]
    base=Path(tempfile.gettempdir())
    with tempfile.TemporaryDirectory(prefix='s5-export-ui-',dir=base) as temp:
        for failure in (False,True):
            released=threading.Event()
            def compile(*args):
                if not released.wait(10):raise ValueError('Timeout fixture UI')
                if failure:raise ValueError('Errore controllato della compilazione')
                return Path(temp)
            web_ui.build=compile
            worker=web_ui.BuildTask(bridge.project,bridge.compiler,Path(temp))
            bridge.worker=worker;worker.finished.connect(bridge.build_finished)
            worker.start();bridge.send(state=bridge.state())
            try:
                until(lambda:js('return state.busy&&document.getElementById("compile").disabled;'),
                      'Pulsante ZIP non disabilitato durante il lavoro')
                released.set()
                until(lambda:bridge.worker is None,'Notifica QThread.finished non elaborata')
                until(lambda:js('return !state.busy&&!document.getElementById("compile").disabled;'),
                      'Pulsante ZIP rimasto occupato dopo la notifica')
                if failure:
                    until(lambda:js('return document.getElementById("status").textContent.includes("interrotta");'),
                          'Errore compilazione non visibile')
                    checks.append('failed-export-clears-busy-and-reenables-button')
                else:
                    until(lambda:js('return document.getElementById("status").textContent.startsWith("ZIP pronto:")&&!document.getElementById("show-output").classList.contains("hidden");'),
                          'ZIP pronto e cartella non visibili dopo il completamento')
                    checks.append('finished-export-clears-busy-and-shows-output-without-full-render')
                    # A late pre-completion response must not restore busy=True.
                    stale=bridge.state();stale.update(stateSequence=bridge.state_sequence-2,busy=True)
                    bridge.send(state=stale);app.processEvents()
                    assert js('return !state.busy&&!document.getElementById("compile").disabled;')
                    checks.append('stale-build-state-cannot-reopen-progress')
            finally:
                released.set()
                if bridge.worker is worker:worker.wait()
                web_ui.build=original
    return checks
