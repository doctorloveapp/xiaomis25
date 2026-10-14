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
    app=QApplication.instance() or QApplication([]);checks=[];header_measurements=[]
    with TemporaryDirectory(prefix='i18n-2.9-',dir=ROOT/'build') as temporary:
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
            assert js('document.body.textContent.includes("Version 2.9")')
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
            example=ROOT/'resources/examples/Bulova.s5faceproj'
            original_digest=hashlib.sha256(example.read_bytes()).hexdigest()
            action('setTab("project")')
            assert js('document.getElementById("example-bulova").textContent')=='Open Bulova example'
            action('document.getElementById("example-bulova").click()')
            ready('state.name==="Bulova"&&tab==="design"','Bulova example from visible button')
            assert bridge.project.name=='Bulova' and bridge.path is None and not bridge.dirty
            assert len(bridge.project.variants)==2 and len(bridge.project.assets)==14
            assert hashlib.sha256(example.read_bytes()).hexdigest()==original_digest
            checks.append('visible-example-button-opens-bulova-as-independent-editable-document')
            ready('document.getElementById("preview").complete&&document.getElementById("preview").naturalWidth===480','Decoded preview')
            deadline=time.monotonic()+0.7
            while time.monotonic()<deadline:app.processEvents()
            window.grab().save(str(ROOT/'build/editor-2.9-en.png'))
            before=json.dumps(bridge.project.metadata(),ensure_ascii=False,sort_keys=True)
            action('document.getElementById("language").value="zh";document.getElementById("language").dispatchEvent(new Event("change"))')
            ready('document.documentElement.lang==="zh"&&document.getElementById("save").textContent==="保存项目"','Chinese switch')
            assert window.language=='zh' and json.loads(settings.read_text())['language']=='zh'
            assert json.dumps(bridge.project.metadata(),ensure_ascii=False,sort_keys=True)==before
            assert js('document.getElementById("project-title").textContent')=='Bulova'
            checks.append('chinese-switch-persists-with-project-and-user-names-unchanged')
            for name,title in [('design','设计你的时间'),('variants','一个表盘，五种样式'),('slots','适合设计的数据'),('hands','个人目录'),('disks','太阳、月亮与方位'),('project','为你的 S5 准备就绪')]:
                action('setTab('+json.dumps(name)+')')
                ready('document.getElementById("view-title").textContent==='+json.dumps(title),'Chinese '+name)
            assert '千分之一秒 456' in js('chronoReading(123456)')
            action('setTab("design");selected=state.layers.find(e=>e.kind==="pointer").id;S5Multi.pick(selected);paint();document.querySelector("[data-prop=source]").closest(".select-control").querySelector(".select-trigger").click()')
            action('document.querySelector(".select-popup [data-value=timeSecond]").dispatchEvent(new MouseEvent("mouseenter"))')
            ready('document.querySelector(".select-description").textContent.includes("真实时间的秒数")','Chinese source tooltip')
            action('S5Selectors.close()')
            checks.append('chinese-six-tabs-source-tooltip-and-chrono-readout')
            for language in ('it','en','zh'):
                action('document.getElementById("language").value='+json.dumps(language)+';document.getElementById("language").dispatchEvent(new Event("change"))')
                ready('document.documentElement.lang==='+json.dumps(language),'Header language')
                for width in (1120,1440):
                    window.resize(width,920)
                    ready('innerWidth==='+str(width),'Resized browser viewport')
                    boxes=json.loads(js('JSON.stringify([".language-control .select-trigger","#open","#save","#compile"].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return {selector:s,x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};}))'))
                    assert max(box['y'] for box in boxes)-min(box['y'] for box in boxes)<.5,(language,width,boxes)
                    assert all(abs(box['height']-36)<.5 for box in boxes),(language,width,boxes)
                    assert all(a['right']<=b['x'] for a,b in zip(boxes,boxes[1:])),(language,width,boxes)
                    assert boxes[-1]['right']<=js('innerWidth'),(language,width,boxes)
                    header_measurements.append({'language':language,'windowWidth':width,'controls':boxes})
            checks.append('aligned-36px-header-controls-in-three-languages-at-1120-and-1440')
            action('setTab("design");S5Multi.pick("");selected="";paint()')
            deadline=time.monotonic()+.7
            while time.monotonic()<deadline:app.processEvents()
            window.grab().save(str(ROOT/'build/editor-2.9-zh.png'))
            window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
            window=MainWindow(smoke=True,settings_path=settings);window.show();bridge=window.bridge;page=window.view.page()
            ready('Boolean(window.s5Ready&&state&&document.documentElement.lang==="zh")','Chinese startup')
            assert window.language=='zh' and js('document.getElementById("save").textContent')=='保存项目'
            checks.append('new-window-loads-chinese-from-settings')
            action('document.getElementById("language").value="it";document.getElementById("language").dispatchEvent(new Event("change"))')
            ready('document.getElementById("save").textContent==="Salva progetto"','Italian after Chinese')
            checks.append('italian-restored-after-chinese')
            window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
    report={'applicationVersion':'2.9','status':'passed','checks':checks,'passed':len(checks),
            'headerMeasurements':header_measurements,
            'sourceEditorTested':True,'executableLaunched':False,'watchfaceZipCreated':False}
    (ROOT/'docs/editor-2.9.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':check()
