"""Check real source Qt/WebChannel i18n without launching the executable."""
import hashlib,json,os,sys,time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from s5studio.web_ui import MainWindow


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='i18n-2.8-',dir=ROOT/'build') as temporary:
        directory=Path(temporary);settings=directory/'settings.json'
        with patch('s5studio.web_ui.user_data_root',lambda:directory/'user'):
            window=MainWindow(smoke=True,settings_path=settings);window.show();bridge=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+20
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                result=[];page.runJavaScript(code,result.append);until(lambda:bool(result),'JS callback');return result[0]
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,message):until(lambda:js(code),message)
            ready('Boolean(window.s5Ready&&state)','Editor startup')
            assert js('document.documentElement.lang')=='it'
            assert js('document.getElementById("save").textContent')=='Salva progetto'
            assert js('document.body.textContent.includes("Version 2.8")')
            checks.append('italian-default-original-labels-and-version')
            # Give editable names the same spelling as a real interface message.
            bridge.project.name='Salva progetto'
            bridge.project.elements[0].name='Data'
            bridge.project.variants[0]['name']='Ora'
            bridge.send(state=bridge.state())
            ready('state.name==="Salva progetto"','Updated project')
            before=json.dumps(bridge.project.metadata(),ensure_ascii=False,sort_keys=True)
            action('document.getElementById("language").value="en";document.getElementById("language").dispatchEvent(new Event("change"))')
            ready('document.documentElement.lang==="en"&&document.getElementById("save").textContent==="Save project"','English switch')
            assert json.loads(settings.read_text())['language']=='en'
            assert js('document.getElementById("project-title").textContent')=='Salva progetto'
            assert js('document.getElementById("current-style").textContent')=='Ora'
            name_selector='[data-layer="'+bridge.project.elements[0].id+'"] .layer-name'
            assert js('document.querySelector('+json.dumps(name_selector)+').textContent')=='Data'
            assert json.dumps(bridge.project.metadata(),ensure_ascii=False,sort_keys=True)==before
            checks.append('english-persisted-with-project-names-and-data-unchanged')
            assert js('S5I18n.t("Unknown key")')=='Unknown key'
            assert js('S5I18n.t("{v0} livelli selezionati",{v0:5})')=='5 selected layers'
            assert js('S5I18n.t("constructor")')=='constructor'
            checks.append('missing-key-parameters-and-inherited-key-fallback')
            for tab,expected in [('variants','One watchface, five styles'),('slots','Data that fits your design'),('hands','Your personal catalog'),('disks','Sun, moon and directions'),('project','Ready for your S5')]:
                action('setTab('+json.dumps(tab)+')')
                ready('document.getElementById("view-title").textContent==='+json.dumps(expected),'Translated '+tab)
            checks.append('all-six-tabs-dynamic-content-translated')
            action('setTab("design")')
            assert js('document.getElementById("scenario").options[0].value')=='Normale'
            assert js('document.getElementById("scenario").options[0].textContent')=='Normal'
            action('document.getElementById("scenario").value="Dati assenti";document.getElementById("scenario").dispatchEvent(new Event("change"))')
            ready('state.scenario==="Dati assenti"','Stable scenario ID')
            checks.append('translated-selector-preserves-backend-value')
            # New markup must translate without touching user input values.
            action('window.testNode=document.createElement("div");testNode.innerHTML=\'<span>Movimento Fluido</span><span data-i18n-skip>Movimento Fluido</span><input value="Salva progetto">\';document.body.append(testNode)')
            ready('testNode.children[0].textContent==="Smooth Motion"','Mutation translation')
            assert js('testNode.children[1].textContent')=='Movimento Fluido'
            assert js('testNode.querySelector("input").value')=='Salva progetto'
            checks.append('new-dom-translated-user-content-preserved')
            # Dropdown trigger copies already localized labels exactly once.
            action('setTab("design");selected=state.layers.find(e=>e.kind==="analog").id;S5Multi.pick(selected);paint()')
            ready('Boolean(document.getElementById("properties").querySelector("details"))','Hand properties')
            assert js('document.getElementById("properties").textContent.includes("Smooth Motion")')
            checks.append('dynamic-hand-controls-and-smooth-flags-localized')
            action('document.getElementById("language").value="it";document.getElementById("language").dispatchEvent(new Event("change"))')
            ready('document.documentElement.lang==="it"&&document.getElementById("save").textContent==="Salva progetto"','Italian switch')
            assert js('testNode.children[0].textContent')=='Movimento Fluido'
            assert json.loads(settings.read_text())['language']=='it'
            checks.append('switch-back-restores-original-italian')
            window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
            # A new application window must read the saved preference at startup.
            settings.write_text('{"language":"en","custom":"kept"}',encoding='utf8')
            window=MainWindow(smoke=True,settings_path=settings);window.show();bridge=window.bridge;page=window.view.page()
            ready('Boolean(window.s5Ready&&state&&document.documentElement.lang==="en")','English startup')
            assert js('document.getElementById("save").textContent')=='Save project'
            assert window.language=='en'
            assert js('document.getElementById("layers-count").textContent')=='3 layers'
            checks.append('parameterized-layer-count-localized')
            checks.append('new-window-loads-language-from-settings')
            ready('document.getElementById("preview").complete&&document.getElementById("preview").naturalWidth===480','Decoded preview')
            deadline=time.monotonic()+0.7
            while time.monotonic()<deadline:app.processEvents()
            window.grab().save(str(ROOT/'build/editor-2.8-en.png'))
            window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
    report={'applicationVersion':'2.8','status':'passed','checks':checks,'passed':len(checks),
            'sourceEditorTested':True,'executableLaunched':False,'watchfaceZipCreated':False}
    (ROOT/'docs/editor-2.8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':check()
