"""Source UI checks for 2.1 POST bindings and independent arc endpoints."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Element,template


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='post-editor-',dir=ROOT/'build') as tmp:
        with patch('s5studio.web_ui.user_data_root',lambda:Path(tmp)/'user'):
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
            ready('Boolean(window.s5Ready&&state)','Startup')
            assert js('document.body.textContent.includes("Version 2.1")');checks.append('version-2.1')
            p=template('Analogico');p.elements[0].chrono_pro=True
            small=Element(kind='pointer',x=140,y=180,width=90,height=90,source='timeSecond')
            p.elements.insert(0,small);p.ensure_independent_variants();b.project=p;b._design=None;b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(small.id)+')','Fixture')
            action('selected='+json.dumps(small.id)+';S5Multi.pick(selected);paint()')
            def current():return b.element({'id':small.id})
            def change(key,value,actual=None,expected=None):
                target='document.querySelector('+json.dumps('[data-prop='+key+']')+')'
                action('const n='+target+';n[n.type==="checkbox"?"checked":"value"]='+json.dumps(value)+';n.dispatchEvent(new Event("change"))')
                ready('state.resolvedElements.find(e=>e.id===selected).'+(actual or key)+'==='+json.dumps(value if expected is None else expected),'Commit '+key)
            assert js('state.luaSources.studioChronoCentisecond==="Centesimi (POST)"&&state.luaSources.studioChronoMillisecond==="Millesimi (POST)"')
            checks.append('both-post-sources-and-help')
            change('source','studioChronoMillisecond')
            assert current().value_range==1000 and not current().smooth_seconds
            assert js('!document.querySelector("[data-prop=smooth_seconds]")');checks.append('post-hides-smooth-flag-and-initializes-full-range')
            change('pointer_arc',True)
            assert current().value_range==999 and current().angle_range==120;checks.append('arc-defaults-cover-complete-post-fraction')
            change('angle_start',30)
            assert current().angle_range==90;checks.append('editing-start-preserves-angle-end')
            change('angle_end',140,'angle_range',110);checks.append('clockwise-30-to-140')
            change('arc_direction','ccw','angle_range',-250);checks.append('counterclockwise-30-to-140')
            change('post_readout','digit');assert current().value_range==9;checks.append('single-digit-readout')
            change('value_end',8,'value_range',8);checks.append('zero-to-eight-mapping')
            change('value_start',2);assert current().value_range==6;checks.append('editing-value-start-preserves-end')
            change('value_start',0);assert current().value_range==8
            def pose(value):
                action('document.querySelector('+json.dumps('[data-calibration='+value+']')+').click()')
                ready('state.values.__pointerCalibration[selected]==='+json.dumps(value),'Calibration '+value)
            pose('start');first=b.state()['preview'];pose('end');last=b.state()['preview']
            assert first!=last and not b.values.get('__proValues',{}).get(small.id)
            checks.append('visual-endpoints-override-preview-only')
            window.view.grab().save(str(ROOT/'build/chrono-post-editor-2.1.png'))
            action('document.querySelector("[data-calibration=live]").click()')
            ready('!state.values.__pointerCalibration[selected]','Return to live');checks.append('return-to-live')
            change('pointer_arc',False);assert current().angle_range==-360
            assert not js('Boolean(document.querySelector("[data-prop=angle_end]"))');checks.append('full-circle-kept')
            change('source','timeSecond');assert js('Boolean(document.querySelector("[data-prop=smooth_seconds]"))')
            checks.append('existing-sources-keep-smooth-setting')
            assert not b.project.validate(),b.project.validate()
            window.close();app.processEvents()
    report={'applicationVersion':'2.1','status':'passed','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False,'screenshot':'build/chrono-post-editor-2.1.png'}
    (ROOT/'docs/chrono-post-editor-2.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
