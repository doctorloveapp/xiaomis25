"""Exercise the source editor's seconds selector and motion preview, no EXE."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,os,sys,time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Project,Element
from s5studio.render import SCENARIOS


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='civil-seconds-',dir=ROOT/'build') as temporary:
        with patch('s5studio.web_ui.user_data_root',lambda:Path(temporary)/'user'):
            window=MainWindow(smoke=True);window.show();b=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                result=[];page.runJavaScript(code,result.append)
                until(lambda:bool(result),'JavaScript callback');return result[0]
            def ready(expression,message):until(lambda:js(expression),message)
            def command(request):
                result=json.loads(b.command(json.dumps(request)))
                assert not result.get('error'),result
                b.send(state=result['state'])
            ready('Boolean(window.s5Ready&&state)','Editor startup')
            e=Element(kind='pointer',source='healthHeartRate',value_start=1,x=180,y=180,width=120,height=120)
            b.project=Project(elements=[e]);b.project.ensure_independent_variants();b._design=None;b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(e.id)+')','Fixture repaint')
            js('selected='+json.dumps(e.id)+';S5Multi.pick(selected);paint();true')
            js('const input=document.querySelector("[data-prop=source]");input.value="timeSecond";input.dispatchEvent(new Event("change"));true')
            ready('state.resolvedElements.find(e=>e.kind==="pointer").source==="timeSecond"','Civil source selected')
            current=b.element({'id':e.id})
            assert (current.value_start,current.value_range,current.angle_start,current.angle_range)==(0,60,0,360)
            assert not current.smooth_seconds
            checks+=['civil-source-selected','source-select-restores-0-60-360','small-seconds-default-is-ticking']
            assert js('state.sourceDescriptions.timeSecond.includes("Valore iniziale 0")&&state.sourceDescriptions.timeSecond.includes("Simula movimento")')
            checks.append('zero-and-simulation-help')
            js('document.getElementById("second").value=0;document.getElementById("second").dispatchEvent(new Event("change"));true')
            ready('state.values.second===0','Set civil second zero')
            zero=b.image_url(b.project.variant_project(0))
            ready('document.getElementById("preview").src==='+json.dumps(zero),'Zero visible')
            checks.append('second-zero-visible')
            js('document.getElementById("motion-preview").click();true')
            ready('state.motionPreview','Motion enabled')
            origin=b.motion_started
            for elapsed in (15,30,59,60):
                with patch('s5studio.web_ui.time.monotonic_ns',return_value=(origin+elapsed*1000)*1000000):b.preview_tick()
                expected=b.image_url(b.project.variant_project(0))
                ready('document.getElementById("preview").src==='+json.dumps(expected),'Live frame '+str(elapsed))
                assert (expected==zero)==(elapsed==60)
                checks.append('tick-and-wrap-'+str(elapsed))
            # The normal sample starts at 30 seconds, not at the scale origin.
            command({'action':'scenario','value':'Normale'})
            assert b.values['second']==30 and b.values['__secondFraction']==0
            normal=b.image_url(b.project.variant_project(0),values=SCENARIOS['Normale'])
            ready('document.getElementById("preview").src==='+json.dumps(normal),'Normal sample at thirty seconds')
            checks.append('normal-start-is-selected-thirty-seconds')
            origin=b.motion_started
            with patch('s5studio.web_ui.time.monotonic_ns',return_value=(origin+4000)*1000000):b.preview_tick()
            thirty_four=b.image_url(b.project.variant_project(0),values={'second':34})
            ready('document.getElementById("preview").src==='+json.dumps(thirty_four),'Normal sample advances to thirty four')
            checks.append('normal-thirty-plus-four-is-thirty-four')
            # Changing the second while motion is on must discard its old phase.
            with patch('s5studio.web_ui.time.monotonic_ns',return_value=(origin+4000)*1000000):
                command({'action':'time','second':0})
            assert b.values['__secondFraction']==0
            ready('document.getElementById("preview").src==='+json.dumps(zero),'Manual zero while ticking')
            checks.append('manual-second-resets-running-phase')
            origin=b.motion_started
            with patch('s5studio.web_ui.time.monotonic_ns',return_value=(origin+1000)*1000000):b.preview_tick()
            one=b.image_url(b.project.variant_project(0),values={'second':1})
            ready('document.getElementById("preview").src==='+json.dumps(one),'Tick after manual zero')
            checks.append('ticks-from-manually-selected-second')
            command({'action':'scenario','value':'Mezzanotte'})
            assert b.values['__secondFraction']==0
            ready('document.getElementById("preview").src==='+json.dumps(zero),'Scenario changes reset phase')
            checks.append('scenario-change-resets-running-phase')
            names={s['name'] for s in b.hand_set_catalog.sets()}
            assert {'Omega moon','Omega moon piccole'}<=names
            checks.append('both-omega-sets-bundled')
            window.close();app.processEvents()
    report={'applicationVersion':'1.8.1','status':'passed','checks':checks,'checkCount':len(checks),'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/civil-seconds-editor-1.8.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
