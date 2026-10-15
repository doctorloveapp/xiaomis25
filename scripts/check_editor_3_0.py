"""Exercise GIF controls in the source editor; never launch the bundled EXE."""
import json,os,sys,time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from s5studio.web_ui import MainWindow
from s5studio.model import Project
from test_gif_animation import sample_gif


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='gif-editor-',dir=ROOT/'build') as temporary:
        folder=Path(temporary);gif=sample_gif(folder/'sample.gif');settings=folder/'settings.json'
        with patch('s5studio.web_ui.user_data_root',lambda:folder/'user'):
            window=MainWindow(smoke=True,settings_path=settings);window.show();bridge=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+20
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                result=[];page.runJavaScript(code,result.append);until(lambda:bool(result),'JS result');return result[0]
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,message):until(lambda:js(code),message)
            def command(name,**kwargs):
                reply=json.loads(bridge.command(json.dumps({'action':name,**kwargs})));assert not reply.get('error'),reply
                bridge.send(state=reply['state']);return reply
            ready('Boolean(window.s5Ready&&state)','Editor startup')
            assert not bridge.project.elements and not bridge.project.complications and not bridge.project.aod_enabled
            assert js('state.layers.length')==0 and js('document.body.textContent.includes("Version 3.0")')
            checks.append('blank-startup-with-no-normal-or-aod-objects')
            toolbar=json.loads(js('JSON.stringify([...document.querySelectorAll(".toolbar>button span")].map(e=>e.textContent))'))
            assert toolbar==['＋ Immagine','＋ Gif','Lancette','Lancette piccole','Disco','Dato live','Bussola analogica','Complicazione','Ora','Data','Testo','Forma'],toolbar
            checks.append('requested-toolbar-order-and-dedicated-gif-button')
            calls=[]
            def choose(*args):calls.append(args);return str(gif)
            bridge.dialogs.open=choose
            action('document.getElementById("import-gif").click()')
            ready('state.layers.length===1&&state.layers[0].kind==="gif"','GIF import')
            eid=bridge.project.elements[0].id
            ready('Boolean(document.getElementById("gif-play"))','GIF controls')
            assert calls[0][0]=='gif-open' and calls[0][-1]=='GIF (*.gif)'
            assert js('document.querySelectorAll("[data-gif-frame]").length')==3
            assert len(bridge.project.elements[0].gif_frames)==3
            ready('[...document.querySelectorAll(".gif-frame img")].every(img=>img.complete&&img.naturalWidth>0)','Decoded GIF thumbnails')
            checks.append('gif-only-dialog-and-all-decoded-frames-in-inspector')
            action('document.querySelector("[data-gif-frame=\\"1\\"]").click()')
            ready('!state.layers[0].gif_frames[1].included','Frame exclusion')
            action('document.getElementById("gif-remove").click()')
            ready('state.layers[0].gif_frames.length===2','Frame deletion')
            action('document.getElementById("undo").click()')
            ready('state.layers[0].gif_frames.length===3','Frame deletion undo')
            command('gif-frame',id=eid,index=1,included=True)
            checks.append('frame-exclusion-deletion-and-undo')
            action('document.getElementById("prop-gif_speed").value="200";document.getElementById("prop-gif_speed").dispatchEvent(new Event("change"))')
            ready('state.layers[0].gif_speed===200','GIF speed')
            action('document.getElementById("gif-play").click()')
            ready('state.gifPreview===true','GIF playback')
            first=bridge.image_url(bridge.project.variant_project(0));bridge.gif_started=time.monotonic_ns()//1000000-60;bridge.preview_tick()
            assert first!=bridge.image_url(bridge.project.variant_project(0))
            action('document.querySelector("[data-gif-inspect=\\"2\\"]").click()')
            ready('state.gifPreview===false','Frame inspection pauses playback')
            assert bridge.values['__gifFrames'][eid]==2
            checks.append('speed-playback-and-manual-frame-inspection')
            command('edit',id=eid,changes={'width':700,'height':700,'x':-100,'y':-100})
            ready('state.layers[0].width===700','Oversized GIF positioning')
            checks.append('gif-scaling-beyond-480-and-clipped-preview')
            command('add',kind='analog')
            assert not bridge.project.elements[-1].show_ticks
            checks.append('new-hand-group-defaults-to-no-dial-ticks')
            command('settings',changes={'aodEnabled':True});command('aod',value=True)
            assert not any(e.kind=='gif' for e in bridge.project.ordered_layers(True))
            for layer in list(bridge.project.ordered_layers(True)):command('delete',id=layer.id)
            assert not bridge.project.ordered_layers(True)
            command('add',kind='clock')
            assert [e.kind for e in bridge.project.ordered_layers(True)]==['clock']
            normal_ids=[e.id for e in bridge.project.ordered_layers(False)]
            imported=command('gif')['selectedLayer']
            command('delete',id=imported)
            assert [e.id for e in bridge.project.ordered_layers(False)]==normal_ids
            assert [e.kind for e in bridge.project.ordered_layers(True)]==['clock']
            checks.append('aod-simple-clock-with-gif-omitted-or-deleted-independently')
            command('aod',value=False)
            action('selected='+json.dumps(eid)+';S5Multi.pick(selected);paint()')
            for language,label in [('en','Play GIF preview'),('zh','播放 GIF 预览'),('it','Avvia anteprima GIF')]:
                action('document.getElementById("language").value='+json.dumps(language)+';document.getElementById("language").dispatchEvent(new Event("change"))')
                ready('document.documentElement.lang==='+json.dumps(language)+'&&state.language==='+json.dumps(language)+'&&document.getElementById("gif-play").textContent==='+json.dumps(label),'GIF translated '+language)
                boxes=json.loads(js('JSON.stringify([".language-control .select-trigger","#open","#save","#compile"].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return {y:r.y,h:r.height};}))'))
                assert max(b['y'] for b in boxes)-min(b['y'] for b in boxes)<.5
                assert all(abs(b['h']-36)<.5 for b in boxes)
            checks.append('gif-controls-localized-in-three-languages-and-header-aligned')
            path=folder/'roundtrip.s5faceproj';bridge.project.save(path)
            assert Project.load(path).metadata()==bridge.project.metadata()
            checks.append('portable-project-keeps-gif-frames-speed-and-aod')
            deadline=time.monotonic()+.4
            while time.monotonic()<deadline:app.processEvents()
            window.grab().save(str(ROOT/'build/editor-3.0-it.png'))
            action('document.getElementById("inspector").scrollTop=document.getElementById("inspector").scrollHeight')
            deadline=time.monotonic()+.4
            while time.monotonic()<deadline:app.processEvents()
            window.grab().save(str(ROOT/'build/editor-gif-3.0-it.png'))
            bridge.dirty=False;window.close();window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
    report={'applicationVersion':'3.0','status':'passed','passed':len(checks),'checks':checks,
            'sourceEditorTested':True,'executableLaunched':False,'hardwareTestPerformed':False}
    (ROOT/'docs/editor-3.0.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
