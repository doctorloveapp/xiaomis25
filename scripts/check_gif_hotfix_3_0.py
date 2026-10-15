"""Source-editor regression checks for Gatto, frame limits and nested scroll."""
import hashlib,json,os,sys,time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from s5studio.web_ui import MainWindow
from s5studio.model import Project


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    path=ROOT/'projects/Gattos5faceproj.s5faceproj';digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with TemporaryDirectory(prefix='gif-hotfix-editor-',dir=ROOT/'build') as temp:
        folder=Path(temp)
        with patch('s5studio.web_ui.user_data_root',lambda:folder/'user'):
            window=MainWindow(smoke=True,settings_path=folder/'settings.json');window.show();bridge=window.bridge;page=window.view.page()
            def until(fn,label):
                deadline=time.monotonic()+25
                while time.monotonic()<deadline:
                    app.processEvents()
                    if fn():return
                raise AssertionError(label)
            def js(code):
                result=[];page.runJavaScript(code,result.append);until(lambda:bool(result),'JS result');return result[0]
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,label):until(lambda:js(code),label)
            ready('Boolean(window.s5Ready&&state)','Editor startup')
            assert not js('document.getElementById("aod").disabled')
            action('document.getElementById("aod").click()')
            ready('state.aod&&!state.aodEnabled','AOD edit without exporting')
            assert not js('document.getElementById("aod-export-note").classList.contains("hidden")')
            checks.append('aod-always-editable-even-with-export-disabled')
            bridge.project=Project.load(path);bridge.aod=False;bridge.variant=0;bridge.send(state=bridge.state())
            ready('state.name==="Gatto"&&state.layers.some(e=>e.kind==="gif")','Gatto loaded')
            eid=next(e.id for e in bridge.project.elements if e.kind=='gif')
            action('selected='+json.dumps(eid)+';S5Multi.pick(selected);paint()')
            ready('Boolean(document.querySelector(".gif-frames"))','Gatto frame controls')
            assert js('document.getElementById("compile").disabled')
            assert js('state.exportErrors[0].includes("44")&&state.exportErrors[0].includes("20")')
            assert len(bridge.project.elements[0].gif_frames)==60
            checks.append('gatto-60-total-44-included-loads-and-shows-20-frame-export-limit')
            bridge.dialogs.directory=lambda *_:(_ for _ in ()).throw(AssertionError('must not open export dialog'))
            reply=json.loads(bridge.command('{"action":"build"}'))
            assert '44 fotogrammi inclusi; massimo 20' in reply['error'] and bridge.worker is None
            checks.append('backend-refuses-oversized-gif-before-dialog-or-worker')
            action('document.getElementById("aod").click()')
            ready('state.aod&&!state.aodEnabled','AOD after importing Gatto GIF')
            action('document.querySelector("[data-add=clock]").click()')
            ready('state.layers.some(e=>e.aod&&e.kind==="clock")','Simple AOD clock')
            ready('state.aod&&state.aodEnabled','Editing AOD automatically enables its export')
            assert [e.kind for e in bridge.project.ordered_layers(True)]==['clock']
            action('document.getElementById("normal").click()')
            ready('!state.aod','Normal scene')
            action('selected='+json.dumps(eid)+';S5Multi.pick(selected);paint()')
            checks.append('aod-remains-accessible-with-gif-and-can-export-independent-simple-clock')
            included=[i for i,f in enumerate(bridge.project.elements[0].gif_frames) if f['included']]
            index=next(i for i in included if i>=20)
            action('window.frameNode=document.querySelector("[data-gif-frame=\\"'+str(index)+'\\"]");window.galleryNode=document.querySelector(".gif-frames");galleryNode.scrollTop=440;document.getElementById("inspector").scrollTop=document.getElementById("inspector").scrollHeight')
            before=json.loads(js('JSON.stringify([galleryNode.scrollTop,document.getElementById("inspector").scrollTop,document.getElementById("workspace").scrollTop,frameNode.getBoundingClientRect().top])'))
            assert before[0]>0,before
            action('frameNode.click()')
            ready('state.layers.find(e=>e.id==='+json.dumps(eid)+').gif_frames['+str(index)+'].included===false','Frame toggled')
            after=json.loads(js('JSON.stringify([galleryNode.scrollTop,document.getElementById("inspector").scrollTop,document.getElementById("workspace").scrollTop,frameNode.getBoundingClientRect().top])'))
            assert js('frameNode.isConnected&&galleryNode===document.querySelector(".gif-frames")')
            assert all(abs(a-b)<.5 for a,b in zip(before,after)),(before,after)
            checks.append('frame-checkbox-preserves-dom-nested-gallery-inspector-workspace-and-pixel-position')
            included=[i for i,f in enumerate(bridge.project.elements[0].gif_frames) if f['included']]
            for index in included[20:]:
                action('document.querySelector("[data-gif-frame=\\"'+str(index)+'\\"]").click()')
                ready('state.layers.find(e=>e.id==='+json.dumps(eid)+').gif_frames['+str(index)+'].included===false','Reduce frames')
            assert js('state.layers.find(e=>e.id==='+json.dumps(eid)+').gif_frames.filter(f=>f.included).length')==20
            assert not js('document.getElementById("compile").disabled')
            assert not bridge.project.validate()
            checks.append('export-unlocks-at-exactly-20-included-frames-without-deleting-project-frames')
            for language in ['en','zh','it']:
                action('document.getElementById("language").value='+json.dumps(language)+';document.getElementById("language").dispatchEvent(new Event("change"))')
                ready('document.documentElement.lang==='+json.dumps(language),'Language '+language)
                expected={'en':'included frames','zh':'已包含','it':'fotogrammi inclusi'}[language]
                ready('document.querySelector("[data-gif-count]").textContent.includes('+json.dumps(expected)+')','Localized GIF counter')
            checks.append('new-aod-and-limit-ui-remains-localized')
            window.grab().save(str(ROOT/'build/gif-hotfix-3.0.png'))
            bridge.dirty=False;window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    report={'applicationVersion':'3.0','status':'passed','passed':len(checks),'checks':checks,
            'scrollBefore':before,'scrollAfter':after,'originalGattoProjectUnchanged':True,'executableLaunched':False}
    (ROOT/'docs/gif-hotfix-editor-3.0.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
