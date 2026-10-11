"""Source UI checks: tenths models, folder history and frozen chrono readings."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PIL import Image
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow,StudioBridge
from s5studio.model import Element,template


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='editor-2.1-',dir=ROOT/'build') as temp:
        temp=Path(temp)
        with patch('s5studio.web_ui.user_data_root',lambda:temp/'user'):
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
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,message):until(lambda:js(code),message)
            def command(action,**values):
                result=json.loads(b.command(json.dumps({'action':action,**values})))
                assert 'error' not in result,result
                b.send(state=result['state']);return result
            ready('Boolean(window.s5Ready&&state)','Startup')
            assert js('document.body.textContent.includes("Version 2.1")');checks.append('version-2.1')
            action('setTab("hands")')
            assert js('document.querySelectorAll("[data-set-image][data-shadow=false]").length===3')
            command('hand-set-meta',changes={'name':'Decimi UI','small':True})
            ready('state.handSetDraft.small','Small type')
            assert js('document.querySelectorAll("[data-set-image][data-shadow=false]").length===6')
            assert js('document.querySelector("[data-set-image=decisecond]").closest(".card").textContent.includes("Decimi")')
            checks.append('main-three-small-six-roles-with-tenths-label')
            png=temp/'decimi.png';Image.new('RGBA',(16,80),'orange').save(png)
            with patch('s5studio.web_ui.QFileDialog.getOpenFileName',return_value=(str(png),'PNG')):
                action('document.querySelector("[data-set-image=decisecond][data-shadow=false]").click()')
                ready('Boolean(state.handSetDraft.hands.decisecond)','Import tenths')
            command('hand-set-meta',changes={'generateShadows':True});command('hand-set-save')
            saved=next(s for s in b.hand_set_catalog.sets() if s['name']=='Decimi UI')
            command('hand-set-load',id=saved['id'])
            assert b.hand_set_draft['hands']['decisecond']['shadow']['generated']
            ready('state.handSetDraft.id==='+json.dumps(saved['id']),'Reload tenths')
            checks.append('tenths-import-save-reopen-with-shadow')
            p=template('Analogico');p.elements[0].chrono_pro=True
            small=Element(kind='pointer',source='studioChronoDecisecond',value_range=10,x=140,y=180,width=90,height=90)
            post=Element(kind='pointer',source='studioChronoMillisecond',value_range=1000,x=240,y=180,width=90,height=90)
            p.elements.extend([small,post]);p.ensure_independent_variants();b.project=p;b._design=None
            preset=next(h for h in b.hand_presets if h.get('setId')==saved['id'] and h['hand']=='decisecond')
            command('hand-preset',id=small.id,hand='second',preset=preset['id'])
            assert b.element({'id':small.id}).source=='studioChronoDecisecond'
            assert not b.project.validate(),b.project.validate()
            checks.append('tenths-model-keeps-pro-binding')

            # Every visible file operation routes to its own persisted category.
            cases=[('open','project-open',{}),('save','project-save',{}),('save-as','project-save',{}),
                   ('image','image-open',{}),('variant-image','image-open',{}),
                   ('hand-image','hand-image-open',{'id':small.id,'hand':'second'}),
                   ('compass-image','compass-image-open',{'id':small.id}),('font','font-open',{'id':small.id}),
                   ('compiler','compiler-open',{}),('build','watchface-export',{}),('export-preview','preview-save',{}),
                   ('hand-set-image','hand-set-image-open',{'role':'decisecond'}),
                   ('hand-set-image','hand-set-shadow-open',{'role':'decisecond','shadow':True})]
            for name,category,values in cases:
                folder=temp/category;folder.mkdir(exist_ok=True);b.dialogs.remember(category,folder,directory=True)
                chooser='getSaveFileName' if name in ('save','save-as','export-preview') else 'getExistingDirectory' if name=='build' else 'getOpenFileName'
                with patch('s5studio.web_ui.QFileDialog.'+chooser,return_value='' if name=='build' else ('','')) as dialog:
                    command(name,**values)
                    initial=Path(dialog.call_args.args[2])
                    assert (initial.parent if chooser=='getSaveFileName' else initial)==folder,(name,initial)
            restarted=StudioBridge(window,smoke=True)
            assert restarted.dialogs.folders==b.dialogs.folders
            checks.extend(['all-load-save-buttons-reuse-category-folder','folder-history-persists-across-bridge-restart'])

            expected='01:02:03 · Decimi 4 · Centesimi 48 · Millesimi 488'
            assert js('chronoReading(3723488)')==expected
            assert js('chronoReading(1001)')=='00:00:01 · Decimi 0 · Centesimi 00 · Millesimi 001'
            checks.append('hours-minutes-seconds-full-fractions-format')
            now=[100000]
            with patch('s5studio.web_ui.time.monotonic_ns',lambda:now[0]*1000000):
                command('chrono-preview');now[0]+=720;b.preview_tick()
                ready('state.chronoState==="ready"','Pro ready')
                command('chrono-preview');now[0]+=3723488;command('chrono-preview')
                assert b.chrono_elapsed==3723488 and b.chrono_state=='reading'
                now[0]+=720;b.preview_tick()
                ready('state.chronoState==="stopped"','POST completed')
                assert js('document.getElementById("chrono-state").textContent')=='Crono fermo'
                assert js('document.getElementById("chrono-reading").textContent')==' · '+expected
                assert js('document.getElementById("chrono-state").nextElementSibling.id')=='chrono-reading'
                checks.append('pro-stop-reading-right-of-label-uses-captured-time')
                now[0]+=10000;b.preview_tick()
                assert b.chrono_elapsed==3723488
                ready('state.chronoElapsedMs===3723488','Frozen tick')
                assert js('document.getElementById("chrono-reading").textContent')==' · '+expected
                checks.append('stopped-reading-does-not-drift')
                stale=js('state.stateSequence')-1
                b.send(preview=b.image_url(b.project.variant_project(0)),previewValues=b.values,chronoState='stopped',chronoElapsedMs=1,previewSequence=stale)
                app.processEvents()
                assert js('state.chronoElapsedMs')==3723488;checks.append('stale-frame-does-not-change-reading')
                command('chrono-preview')
                ready('document.getElementById("chrono-reading").classList.contains("hidden")','Reset hides reading')
                checks.append('reset-clears-reading')
                # Also retain the measured reading for the separate classic chrono.
                p=template('Analogico');p.elements.append(Element(kind='pointer',source='studioChronoSecond'))
                p.ensure_independent_variants();b.project=p;b._design=None;b.send(state=b.state())
                command('chrono-preview');now[0]+=3723488;command('chrono-preview')
                ready('state.chronoState==="stopped"&&!state.chronoPro','Classic stopped')
                assert js('document.getElementById("chrono-reading").textContent')==' · '+expected
                checks.append('classic-chrono-same-stop-reading')
            window.close();app.processEvents()
    report={'applicationVersion':'2.1','status':'passed','checkCount':len(checks),'checks':checks,
            'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/editor-2.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
