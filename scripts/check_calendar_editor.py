"""Targeted source UI check for the 1.8.1 calendar; never launch an EXE."""
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
from s5studio.render import calendar_metrics


def check():
    app = QApplication.instance() or QApplication([])
    checks = []
    with TemporaryDirectory(prefix='calendar-ui-', dir=ROOT/'build') as temporary:
        with patch('s5studio.web_ui.user_data_root', lambda: Path(temporary)/'user'):
            window=MainWindow(smoke=True);window.show()
            bridge=window.bridge;page=window.view.page()

            def until(predicate, message):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)

            def js(code):
                replies=[];page.runJavaScript(code,replies.append)
                until(lambda:bool(replies),'JavaScript callback')
                return replies[0]

            def ready(expression, message):
                until(lambda:js(expression),message)

            def change(key, value):
                js('(()=>{const input=document.querySelector('+json.dumps('[data-prop="'+key+'"]')+');input.value='+json.dumps(str(value))+';input.dispatchEvent(new Event("change"));})()')

            ready('Boolean(window.s5Ready&&state)','Editor startup')
            assert js('document.body.textContent.includes("Version 1.8.1")')
            js('send("add",{kind:"number"});true')
            ready('Boolean(document.getElementById("prop-digits"))','Numeric controls')
            change('source','dateWeek')
            ready('state.resolvedElements.some(e=>e.kind==="number"&&e.source==="dateWeek")','Weekday source')
            assert js('document.getElementById("properties").textContent.includes("MON, TUE, WED")&&!document.getElementById("prop-digits")')
            assert bridge.values['dateWeek']==1
            change('size',36)
            ready('state.resolvedElements.some(e=>e.kind==="number"&&e.size===36)','Calendar font size')
            expected=bridge.image_url(bridge.project.variant_project(0))
            ready('document.getElementById("preview").src==='+json.dumps(expected)+'&&document.getElementById("preview").complete','Updated MON preview')
            checks+=['version-1.8.1','weekday-source-help-and-mon-default','numeric-format-controls-hidden-for-calendar','font-change-refreshes-decoded-preview']
            change('source','dateMonth')
            ready('state.resolvedElements.some(e=>e.kind==="number"&&e.source==="dateMonth")','Month source')
            month=next(e for e in bridge.design.elements if e.kind=='number')
            assert month.width>=calendar_metrics(bridge.design,month)[0]
            assert js('document.getElementById("properties").textContent.includes("January–December")&&!document.getElementById("prop-digits")')
            checks+=['full-english-month-help','source-selection-fits-longest-month']
            change('source','dateDay')
            ready('Boolean(document.getElementById("prop-digits"))','Day remains numeric')
            change('digits',2)
            ready('state.resolvedElements.some(e=>e.kind==="number"&&e.digits===2)','Two date digits')
            change('align','right')
            ready('state.resolvedElements.some(e=>e.kind==="number"&&e.align==="right")','Right alignment')
            bridge.values['day']=6;bridge.send(state=bridge.state())
            expected=bridge.image_url(bridge.project.variant_project(0))
            ready('document.getElementById("preview").src==='+json.dumps(expected)+'&&document.getElementById("preview").complete','Single-day right-aligned preview')
            assert js('state.resolvedElements.find(e=>e.kind==="number").align==="right"&&state.errors.length===0')
            checks+=['day-keeps-numeric-controls','right-alignment-selected-through-ui','single-day-preview-refreshes-without-validation-error']
            window.close();app.processEvents()
    report={'status':'passed','applicationVersion':'1.8.1','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False,'hardwareTested':False}
    (ROOT/'docs/calendar-editor-1.8.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
