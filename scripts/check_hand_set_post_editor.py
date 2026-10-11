"""Source UI: create, reopen and apply Centesimi/Millesimi hand-set roles."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PIL import Image
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Element,template


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='post-set-editor-',dir=ROOT/'build') as temp:
        with patch('s5studio.web_ui.user_data_root',lambda:Path(temp)/'user'):
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
            p=template('Analogico');p.elements[0].chrono_pro=True
            small=Element(kind='pointer',source='timeSecond',x=140,y=180,width=90,height=90)
            p.elements.insert(0,small);p.ensure_independent_variants();b.project=p;b._design=None;b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(small.id)+')','Fixture')
            action('setTab("hands")')
            assert js('document.querySelectorAll("[data-set-image][data-shadow=false]").length===3');checks.append('main-set-keeps-three-roles')
            action('document.getElementById("hand-set-type").value="small";document.getElementById("hand-set-type").dispatchEvent(new Event("change"))')
            ready('state.handSetDraft.small','Small type')
            assert js('document.querySelectorAll("[data-set-image][data-shadow=false]").length===6');checks.append('small-set-six-roles')
            action('document.getElementById("hand-set-name").value="POST UI";document.getElementById("hand-set-name").dispatchEvent(new Event("change"))')
            ready('state.handSetDraft.name==="POST UI"','Name')
            for role,color in [('centisecond','orange'),('millisecond','red')]:
                path=Path(temp)/(role+'.png');Image.new('RGBA',(16,80),color).save(path)
                with patch('s5studio.web_ui.QFileDialog.getOpenFileName',return_value=(str(path),'PNG')):
                    action('document.querySelector('+json.dumps('[data-set-image='+role+'][data-shadow=false]')+').click()')
                    ready('Boolean(state.handSetDraft.hands.'+role+')','Import '+role)
                checks.append('import-'+role)
            action('document.getElementById("hand-set-generate-shadows").click()')
            ready('Boolean(state.handSetDraft.hands.millisecond.shadow?.generated)','Generated shadows')
            assert b.hand_set_draft['hands']['centisecond']['shadow']['generated'];checks.append('post-shadows-generated')
            action('const n=document.querySelector('+json.dumps('[data-set-coordinate=millisecond][data-shadow=false][data-axis="1"]')+');n.value=70;n.dispatchEvent(new Event("change"))')
            ready('state.handSetDraft.hands.millisecond.pivot[1]===70','Manual pivot');checks.append('independent-post-pivot')
            action('document.getElementById("hand-set-save").click()')
            ready('state.handSets.some(s=>s.name==="POST UI")&&state.handSetDraft.name===""','Saved')
            saved=next(s for s in b.hand_set_catalog.sets() if s['name']=='POST UI')
            assert js('document.getElementById("hand-set-list").textContent.includes("Centesimi, Millesimi")');checks.append('post-roles-named-in-catalog')
            action('document.querySelector('+json.dumps('[data-set-load="'+saved['id']+'"]')+').click()')
            ready('state.handSetDraft.id==='+json.dumps(saved['id']),'Reopen')
            assert b.hand_set_draft['hands']['millisecond']['pivot'][1]==70;checks.append('reopen-keeps-png-pivot-shadow')
            action('setTab("design");selected='+json.dumps(small.id)+';S5Multi.pick(selected);paint()')
            for role,source,period in [('centisecond','studioChronoCentisecond',100),('millisecond','studioChronoMillisecond',1000)]:
                preset=next(p for p in b.hand_presets if p.get('setId')==saved['id'] and p['hand']==role)
                assert js('Array.from(document.querySelector("[data-preset=second]").options).find(o=>o.value==='+json.dumps(preset['id'])+').textContent.includes('+json.dumps('Centesimi' if role=='centisecond' else 'Millesimi')+')')
                action('const n=document.querySelector("[data-preset=second]");n.value='+json.dumps(preset['id'])+';n.dispatchEvent(new Event("change"));document.querySelector("[data-use-preset=second]").click()')
                ready('state.resolvedElements.find(e=>e.id===selected).source==='+json.dumps(source),'Apply '+role)
                element=b.element({'id':small.id})
                assert element.value_range==period and element.second_shadow_asset in b.project.assets
                assert js('!document.querySelector("[data-prop=smooth_seconds]")');checks.append('apply-'+role+'-pairs-post-source-and-shadow')
            assert not b.project.validate(),b.project.validate()
            window.close();app.processEvents()
    report={'applicationVersion':'2.1','status':'passed','checkCount':len(checks),'checks':checks,
            'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/hand-set-post-editor-2.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
