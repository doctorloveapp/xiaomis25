"""Source-only UI check: per-hand sweep flags and stable hand sections."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,os,sys,time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Project,Element


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='hand-motion-',dir=ROOT/'build') as temporary:
        with patch('s5studio.web_ui.user_data_root',lambda:Path(temporary)/'user'):
            window=MainWindow(smoke=True);window.show();b=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                if 'const ' in code:
                    assert code.endswith('true')
                    code='(()=>{'+code[:-4]+'return true;})()'
                result=[];page.runJavaScript(code,result.append)
                until(lambda:bool(result),'JavaScript callback');return result[0]
            def ready(expression,message):until(lambda:js(expression),message)
            ready('Boolean(window.s5Ready&&state)','Editor startup')
            e=Element(kind='analog',x=60,y=60,width=360,height=360,second_hand=True,smooth_seconds=True)
            aod=Element(kind='analog',x=60,y=60,width=360,height=360,aod=True,smooth_hours=True,smooth_minutes=True)
            b.project=Project(elements=[e,aod],aod_enabled=True);b.project.ensure_independent_variants();b._design=None;b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(e.id)+')','Fixture repaint')
            js('selected='+json.dumps(e.id)+';S5Multi.pick(selected);paint();true')
            for hand,key in [('hour','smooth_hours'),('minute','smooth_minutes'),('second','smooth_seconds')]:
                assert js('document.querySelector("[data-prop='+key+']").closest("details").dataset.details==='+json.dumps(hand))
                assert js('document.querySelectorAll("[data-prop='+key+']").length===1')
                checks.append(hand+'-has-only-own-motion-flag')
            assert js('document.querySelector("[data-prop=smooth_seconds]").checked&&!document.querySelector("[data-prop=smooth_hours]").checked&&!document.querySelector("[data-prop=smooth_minutes]").checked')
            checks.append('legacy-second-setting-preserved')
            for hand,key in [('minute','smooth_minutes'),('hour','smooth_hours')]:
                js('document.querySelectorAll("#properties details").forEach(d=>d.open=d.dataset.details==='+json.dumps(hand)+');const c=document.querySelector("[data-prop='+key+']");c.checked=true;c.dispatchEvent(new Event("change"));true')
                ready('state.resolvedElements.find(e=>e.id==='+json.dumps(e.id)+').'+key,'Flag saved')
                assert js('document.querySelector("details[data-details='+hand+']").open')
                checks.append(hand+'-motion-edit-keeps-section')
            js('const c=document.querySelector("[data-prop=smooth_seconds]");c.checked=false;c.dispatchEvent(new Event("change"));true')
            ready('!state.resolvedElements.find(e=>e.id==='+json.dumps(e.id)+').smooth_seconds','Second flag disabled')
            assert b.element({'id':e.id}).smooth_hours and b.element({'id':e.id}).smooth_minutes
            checks.append('disabling-seconds-does-not-disable-hours-minutes')
            for hand in ('minute','second'):
                js('document.querySelectorAll("#properties details").forEach(d=>d.open=d.dataset.details==='+json.dumps(hand)+');const input=document.querySelector("[data-prop='+hand+'_length]");input.scrollIntoView({block:"center"});input.focus();input.value=53;input.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",bubbles:true}));input.dispatchEvent(new Event("change"));true')
                ready('state.resolvedElements.find(e=>e.id==='+json.dumps(e.id)+').'+hand+'_length===53','Length committed')
                assert js('document.querySelector("details[data-details='+hand+']").open&&!document.querySelector("details[data-details=hour]").open')
                assert js('[...document.querySelectorAll("#properties details[open]")].length===1')
                checks.append(hand+'-enter-edit-keeps-only-current-section-open')
            b.command(json.dumps({'action':'undo'}));b.send(state=b.state())
            ready('state.resolvedElements.find(e=>e.id==='+json.dumps(e.id)+').second_length===50','Undo committed')
            assert js('document.querySelector("details[data-details=second]").open&&!document.querySelector("details[data-details=hour]").open')
            checks.append('undo-keeps-current-section')
            b.aod=True;b.send(state=b.state())
            ready('state.aod','AOD selected')
            js('selected='+json.dumps(aod.id)+';S5Multi.pick(selected);paint();true')
            assert js('[...document.querySelectorAll("#properties [data-prop^=smooth_]")].length===3&&[...document.querySelectorAll("#properties [data-prop^=smooth_]")].every(e=>e.disabled)')
            checks.append('aod-flags-disabled-with-settings-preserved')
            window.close();app.processEvents()
    report={'applicationVersion':'1.8.1','status':'passed','checks':checks,'checkCount':len(checks),'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/hand-motion-editor-1.8.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
