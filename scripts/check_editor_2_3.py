"""Check the source editor's decisecond flag and preview; never launch the EXE."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json, os, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Element,Project,template


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='editor-2.3-',dir=ROOT/'build') as directory:
        directory=Path(directory)
        with patch('s5studio.web_ui.user_data_root',lambda:directory/'user'):
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
            def command(name,**values):
                result=json.loads(b.command(json.dumps({'action':name,**values})))
                assert 'error' not in result,result
                b.send(state=result['state']);return result
            ready('Boolean(window.s5Ready&&state)','Startup')
            assert js('document.body.textContent.includes("Version 2.3")')
            assert '2.3' in window.windowTitle();checks.append('version-2.3')
            p=template('Analogico');p.elements[0].chrono_pro=True
            small=Element(kind='pointer',source='studioChronoDecisecond',value_range=10,
                          x=140,y=180,width=90,height=90)
            post=Element(kind='pointer',source='studioChronoMillisecond',value_range=1000,
                         x=240,y=180,width=90,height=90)
            p.elements[:0]=[small,post];p.ensure_independent_variants();b.project=p;b._design=None
            b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(small.id)+')','Fixture')
            action('selected='+json.dumps(small.id)+';S5Multi.pick(selected);paint()')
            assert js('document.body.textContent.includes("target 25 fps")')
            assert js('document.body.textContent.includes("dieci scatti al secondo")')
            checks.append('decisecond-help-smooth-or-stepped')
            action('let e=document.querySelector("[data-prop=smooth_seconds]");e.checked=true;e.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.elements.find(e=>e.id==='+json.dumps(small.id)+').smooth_seconds','Smooth flag edit')
            assert b.element({'id':small.id}).smooth_seconds
            checks.append('checkbox-updates-project')
            command('edit',id=small.id,changes={'pointer_arc':True,'value_start':2,'value_range':8,'angle_start':30,'angle_range':-140})
            ready('state.resolvedElements.find(e=>e.id===selected).pointer_arc','Arc calibration')
            action('let e=document.querySelector("[data-prop=post_readout]");e.value="digit";e.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).post_readout==="digit"','Digit readout')
            current=b.element({'id':small.id})
            assert (current.value_start,current.value_range,current.angle_start,current.angle_range,current.pointer_arc,current.smooth_seconds)==(2,8,30,-140,True,True)
            assert js('document.body.textContent.includes("Nei decimi le due letture coincidono")')
            checks.append('decisecond-readout-keeps-calibration-and-smooth')
            command('edit',id=small.id,changes={'pointer_arc':False,'value_start':0,'value_range':10,'angle_start':0,'angle_range':360})
            saved=directory/'motion.s5faceproj';b.project.save(saved);b.project=Project.load(saved)
            assert b.element({'id':small.id}).smooth_seconds
            assert b.element({'id':small.id}).post_readout=='digit'
            b._design=None;b.send(state=b.state());checks.append('smooth-flag-save-load')
            from s5studio.native import generate_fprj
            generate_fprj(b.project,directory/'source')
            scene=(directory/'source/app/lua/studio_v0_scene.lua').read_text(encoding='utf8')
            binding=next(line for line in scene.splitlines() if 'core:add {id="'+small.id+'"' in line)
            assert 'postReadout="digit",smooth=true' in binding
            checks.append('decisecond-readout-save-load-and-export')
            now=[100000]
            with patch('s5studio.web_ui.time.monotonic_ns',lambda:now[0]*1000000):
                command('chrono-preview');now[0]+=720;b.preview_tick();command('chrono-preview')
                assert b.chrono_state=='running' and b.motion_timer.interval()==40
                now[0]+=456;b.preview_tick()
                assert abs(b.values['__proValues'][small.id]-4.56)<.001
                main=next(e for e in b.project.elements if e.kind=='analog' and not e.aod)
                assert b.values['__proValues'][main.id+'_second']==0
                checks.append('smooth-preview-40ms-main-seconds-stepped')
                command('edit',id=small.id,changes={'smooth_seconds':False})
                b.preview_tick()
                assert b.motion_timer.interval()==100 and b.values['__proValues'][small.id]==4
                checks.append('stepped-preview-100ms')
                command('edit',id=small.id,changes={'smooth_seconds':True})
                command('chrono-preview');assert b.chrono_state=='reading'
                now[0]+=720;b.preview_tick();assert b.chrono_state=='stopped' and b.chrono_elapsed==456
                ready('state.chronoState==="stopped"','Frozen reading')
                assert 'Millesimi 456' in js('document.getElementById("chrono-reading").textContent')
                assert b.values['__proValues'][post.id]==456
                checks.append('post-and-numeric-reading-share-stop-time')
            action('selected='+json.dumps(post.id)+';S5Multi.pick(selected);paint()')
            assert js('document.querySelector("[data-prop=smooth_seconds]")===null')
            checks.append('post-has-no-smooth-flag')
            action('let e=document.querySelector("[data-prop=post_readout]");e.value="digit";e.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).post_readout==="digit"','POST digit readout')
            assert b.element({'id':post.id}).value_range==10
            action('let e=document.querySelector("[data-prop=post_readout]");e.value="fraction";e.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).post_readout==="fraction"','POST full fraction')
            assert b.element({'id':post.id}).value_range==1000
            checks.append('post-readout-still-sets-its-own-range')
            command('edit',id=small.id,changes={'source':'studioDecisecond'})
            action('selected='+json.dumps(small.id)+';S5Multi.pick(selected);paint()')
            assert js('document.body.textContent.includes("Lettura dei decimi")')
            action('let e=document.querySelector("[data-prop=post_readout]");e.value="fraction";e.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).post_readout==="fraction"','Continuous decisecond readout')
            current=b.element({'id':small.id})
            assert current.value_range==10 and current.smooth_seconds
            checks.append('continuous-decisecond-readout-control')
            window.close();app.processEvents()
    report={'applicationVersion':'2.3','status':'passed','checkCount':len(checks),'checks':checks,
            'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/editor-2.3.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
