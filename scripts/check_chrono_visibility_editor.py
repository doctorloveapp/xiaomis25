"""Exercise the source editor's actual visibility buttons; never launch an EXE."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow


def check():
    app = QApplication.instance() or QApplication([])
    checks = []
    (ROOT / 'build').mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='chrono-visibility-', dir=ROOT / 'build') as temporary:
        with patch('s5studio.web_ui.user_data_root', lambda: Path(temporary) / 'user'):
            window = MainWindow(smoke=True)
            window.show()
            bridge, page = window.bridge, window.view.page()

            def until(predicate, message):
                end = time.monotonic() + 8
                while time.monotonic() < end:
                    app.processEvents()
                    if predicate():
                        return
                raise AssertionError(message)

            def js(code):
                replies = []
                page.runJavaScript(code, replies.append)
                until(lambda: bool(replies), 'JavaScript callback timeout')
                return replies[0]

            def ready(expression, message):
                until(lambda: js(expression), message)

            def visible_button(identifier):
                js('document.querySelector(' + json.dumps('[data-visible="' + identifier + '"]') + ').click();true')

            ready('Boolean(window.s5Ready && state)', 'Editor startup')
            assert js('document.body.textContent.includes("Version 1.7.3")')
            analog = next(e for e in bridge.project.elements if e.kind == 'analog' and not e.aod)
            js('selectLayer(' + json.dumps(analog.id) + ');document.querySelector("[data-prop=chrono_pro]").click();true')
            ready('state.chronoPro', 'Enable the general Crono Pro flag')
            js('send("add",{kind:"pointer"});true')
            ready('state.resolvedElements.some(e=>e.kind==="pointer")', 'Add small hand')
            pointer = next(e for e in bridge.design.elements if e.kind == 'pointer')
            js('const source=document.querySelector("[data-prop=source]");source.value="studioChronoDecisecond";source.dispatchEvent(new Event("change"));true')
            ready('state.resolvedElements.some(e=>e.source==="studioChronoDecisecond")', 'Choose chrono deciseconds')
            assert js('state.luaSources.studioDecisecond.includes("continui")&&state.luaSources.studioChronoDecisecond.includes("Start/Stop/Reset")')
            assert js('state.sourceDescriptions.studioDecisecond.includes("Non misura il tempo")&&state.sourceDescriptions.studioChronoDecisecond.includes("unico flag generale")')
            checks += ['version-1.7.3', 'distinct-source-labels-and-help', 'one-general-pro-flag']

            visible_button(analog.id)
            ready('!state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).visible', 'Hide analog layer')
            assert bridge.preview_pro_mode and not bridge.project.validate()
            assert js('state.chronoPro&&state.errors.length===0&&document.getElementById("toast").classList.contains("hidden")')
            visible_button(pointer.id)
            ready('!state.resolvedElements.find(e=>e.kind==="pointer").visible', 'Hide small hand')
            visible_button(pointer.id)
            ready('state.resolvedElements.find(e=>e.kind==="pointer").visible', 'Show small hand with main layer hidden')
            checks += ['hide-main-without-blocking-message', 'pro-flag-preserved-while-hidden', 'small-chrono-hand-can-be-shown-with-main-hidden']

            js('document.getElementById("chrono-preview").click();true')
            ready('state.chronoState==="arming"', 'Prepare hidden-main Pro')
            bridge.update_pro_preview(time.monotonic_ns() // 1000000 + 800)
            bridge.send(state=bridge.state())
            ready('state.chronoState==="ready"', 'Prepared hidden-main Pro')
            js('document.getElementById("chrono-preview").click();true')
            ready('state.chronoState==="running"', 'Start hidden-main Pro')
            visible_button(analog.id)
            ready('state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).visible', 'Show main during measure')
            assert js('state.chronoState==="running"&&state.chronoPro')
            visible_button(analog.id)
            ready('!state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).visible', 'Hide main during measure')
            assert js('state.chronoState==="running"&&state.chronoPro')
            js('send("undo");true')
            ready('state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).visible', 'Undo visibility')
            js('send("redo");true')
            ready('!state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).visible', 'Redo visibility')
            assert js('state.chronoState==="running"&&state.chronoPro&&state.errors.length===0')
            checks += ['hidden-main-pro-preview-starts', 'visibility-does-not-reset-running-measure', 'undo-redo-visibility-preserves-mode']

            js('selectLayer(' + json.dumps(analog.id) + ');document.querySelector("[data-prop=chrono_pro]").click();true')
            ready('!document.getElementById("toast").classList.contains("hidden")', 'Missing flag dependency error')
            assert js('document.getElementById("toast").textContent.includes("di questo stile")&&state.chronoPro')
            assert next(e for e in bridge.design.elements if e.id == analog.id).chrono_pro
            checks += ['real-dependency-error-still-blocks-and-restores-flag']
            window.close()
            app.processEvents()
    report = {'status': 'passed', 'applicationVersion': '1.7.3', 'checks': checks,
              'checkCount': len(checks), 'sourceEditorTested': True,
              'executableLaunched': False, 'hardwareTested': False}
    (ROOT / 'docs/chrono-visibility-editor-1.7.3.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    check()
