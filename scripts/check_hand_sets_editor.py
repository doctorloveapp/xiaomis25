"""Targeted source-editor DOM check; never launches the packaged executable."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PIL import Image,ImageDraw
from PySide6.QtWidgets import QApplication,QFileDialog
from s5studio.web_ui import MainWindow


def check():
    app=QApplication.instance() or QApplication([])
    checks=[]
    (ROOT/'build').mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='hand-set-ui-',dir=ROOT/'build') as temporary:
        folder=Path(temporary)
        with patch('s5studio.web_ui.user_data_root',lambda:folder/'user'):
            window=MainWindow(smoke=True);window.showNormal();window.resize(1440,920);window.show()
            bridge=window.bridge;page=window.view.page()
            def until(predicate,message,timeout=8):
                end=time.monotonic()+timeout
                while time.monotonic()<end:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                replies=[];page.runJavaScript(code,replies.append)
                until(lambda:bool(replies),'JavaScript callback timeout')
                return replies[0]
            def ready(expression,message):until(lambda:js(expression),message)
            ready('Boolean(window.s5Ready && state && document.getElementById("preview").complete)','Editor startup')
            js('document.querySelector("[data-tab=hands]").click();true')
            assert js('!document.getElementById("hands-panel").classList.contains("hidden")&&document.getElementById("stage-wrap").classList.contains("hidden")&&document.getElementById("inspector").classList.contains("hidden")')
            assert js('document.body.textContent.includes("Version 1.7.6")')
            checks+=['new-navigation-panel','catalog-uses-full-workspace','version-1.7.6']
            initial_count=len(bridge.hand_set_catalog.sets())
            assert len(bridge.hand_presets)==595+sum(len(s['hands']) for s in bridge.hand_set_catalog.personal_sets())
            assert js('document.querySelectorAll("[data-set-load]").length===state.handSets.length')
            assert js('JSON.stringify(state.handSets.filter(s=>s.bundled).map(s=>s.name))').count('Swatch')==2
            original_set=next(s for s in bridge.hand_set_catalog.sets() if s['id'].startswith('builtin-') and not s['small'])
            original_project=bridge.project.metadata()
            js('document.querySelector('+json.dumps('[data-set-load="'+original_set['id']+'"]')+').click();true')
            until(lambda:bridge.hand_set_draft['id']==original_set['id'],'Load original set')
            ready('state.handSetDraft.id==='+json.dumps(original_set['id']),'Original draft repaint')
            ready('Array.from(document.querySelectorAll(".hand-set-pivot img")).every(i=>i.complete&&i.naturalWidth>0)','Original graphics decode')
            js('document.getElementById("hand-set-name").value="Edited original UI";document.getElementById("hand-set-name").dispatchEvent(new Event("change"));true')
            until(lambda:bridge.hand_set_draft['name']=='Edited original UI','Original rename')
            ready('state.handSetDraft.name==="Edited original UI"','Original rename repaint')
            js('document.getElementById("hand-set-save").click();true')
            until(lambda:any(s['name']=='Edited original UI' for s in bridge.hand_set_catalog.sets()),'Save original edit')
            ready('Boolean(document.querySelector('+json.dumps('[data-set-restore="'+original_set['id']+'"]')+'))','Original restore button')
            js('window.confirm=()=>true;document.querySelector('+json.dumps('[data-set-restore="'+original_set['id']+'"]')+').click();true')
            until(lambda:not any(s['name']=='Edited original UI' for s in bridge.hand_set_catalog.sets()),'Restore original')
            ready('state.handSetDraft.name===""&&!state.handSets.some(s=>s.name==="Edited original UI")','Original restore repaint')
            assert bridge.project.metadata()==original_project
            js('document.getElementById("hand-set-search").value="Swatch";document.getElementById("hand-set-search").dispatchEvent(new Event("input"));true')
            assert js('document.querySelectorAll("#hand-set-list [data-set-load]").length===2')
            js('document.getElementById("hand-set-search").value="";document.getElementById("hand-set-search").dispatchEvent(new Event("input"));true')
            checks+=['bundled-personal-sets-present-on-fresh-pc','every-original-set-has-edit-button','original-set-images-decode','edit-and-save-original-set','restore-original-without-changing-project','catalog-search-filters-results']
            js('document.getElementById("hand-set-name").value="NASA Custom UI";document.getElementById("hand-set-name").dispatchEvent(new Event("change"));true')
            until(lambda:bridge.hand_set_draft['name']=='NASA Custom UI','Name not received')
            ready('state.handSetDraft.name==="NASA Custom UI"','Name not repainted')
            for role,color in [('hour','red'),('minute','green'),('second','blue')]:
                image=Image.new('RGBA',(24,160));ImageDraw.Draw(image).polygon([(12,3),(17,145),(12,154),(7,145)],fill=color)
                path=folder/(role+'.png');image.save(path)
                with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'PNG')):
                    js('document.querySelector("[data-set-image='+role+'][data-shadow=false]").click();true')
                    until(lambda:role in bridge.hand_set_draft['hands'],'Image import: '+role)
                    ready('Boolean(document.querySelector("[data-set-pivot='+role+'][data-shadow=false] img")?.naturalWidth)','Image decode: '+role)
            checks+=['name-edit','three-role-png-import','source-pngs-decode']
            clicked=json.loads(js('JSON.stringify((()=>{const box=document.querySelector("[data-set-pivot=hour][data-shadow=false]"),r=box.querySelector("img").getBoundingClientRect(),event=new MouseEvent("click",{clientX:r.left+r.width*.5,clientY:r.top+r.height*.25,bubbles:true});box.dispatchEvent(event);return [Math.max(0,Math.min(23,Math.floor((event.clientX-r.left)/r.width*24))),Math.max(0,Math.min(159,Math.floor((event.clientY-r.top)/r.height*160)))];})())'))
            until(lambda:bridge.hand_set_draft['hands']['hour']['pivot']==clicked,'Click pivot')
            ready('JSON.stringify(state.handSetDraft.hands.hour.pivot)==='+json.dumps(json.dumps(clicked,separators=(',',':'))),'Pivot repainted')
            shadow=folder/'shadow.png';Image.new('RGBA',(24,160),(10,10,10,100)).save(shadow)
            with patch.object(QFileDialog,'getOpenFileName',return_value=(str(shadow),'PNG')):
                js('document.querySelector("[data-set-image=hour][data-shadow=true]").click();true')
                until(lambda:'shadow' in bridge.hand_set_draft['hands']['hour'],'Shadow import')
                ready('Boolean(state.handSetDraft.hands.hour.shadow)','Shadow repainted')
            js('const offset=document.querySelector("[data-set-coordinate=hour][data-coordinate=offset]");offset.value="3";offset.dispatchEvent(new Event("change"));true')
            until(lambda:bridge.hand_set_draft['hands']['hour']['shadow']['offset'][0]==3,'Shadow offset')
            checks+=['click-source-pivot','optional-shadow-import','shadow-offset-edit']
            from copy import deepcopy
            manual_shadow=deepcopy(bridge.hand_set_draft['hands']['hour']['shadow'])
            js('document.getElementById("hand-set-generate-shadows").click();true')
            until(lambda:bridge.hand_set_draft['generateShadows'] and all(bridge.hand_set_draft['hands'][h].get('shadow',{}).get('generated') for h in ('minute','second')),'Generate missing shadows flag')
            ready('Boolean(document.querySelector("[data-auto-shadow=minute] img")?.naturalWidth)','Generated shadow preview')
            assert bridge.hand_set_draft['hands']['hour']['shadow']==manual_shadow
            assert js('document.querySelector("[data-set-coordinate=minute][data-shadow=true]").readOnly')
            js('document.getElementById("hand-set-shadow-opacity").value="55";document.getElementById("hand-set-shadow-opacity").dispatchEvent(new Event("change"));true')
            until(lambda:bridge.hand_set_draft['shadowOptions']['opacity']==55,'Automatic opacity control')
            ready('state.handSetDraft.shadowOptions.opacity===55','Opacity repaint')
            js('document.getElementById("hand-set-generate-shadows").click();true')
            until(lambda:not bridge.hand_set_draft['generateShadows'] and all('shadow' not in bridge.hand_set_draft['hands'][h] for h in ('minute','second')),'Generation OFF removes only automatic shadows')
            assert bridge.hand_set_draft['hands']['hour']['shadow']==manual_shadow
            ready('!state.handSetDraft.generateShadows','Generation OFF repaint')
            js('document.getElementById("hand-set-generate-shadows").click();true')
            until(lambda:bridge.hand_set_draft['generateShadows'],'Generation ON again')
            ready('state.handSetDraft.generateShadows','Generation ON repaint')
            js('document.getElementById("hand-set-shadow-offset-0").value="4";document.getElementById("hand-set-shadow-offset-0").dispatchEvent(new Event("change"));true')
            until(lambda:bridge.hand_set_draft['hands']['minute']['shadow']['offset'][0]==4,'Automatic shadow offset control')
            assert bridge.hand_set_draft['hands']['hour']['shadow']==manual_shadow
            checks+=['generate-missing-shadows-checkbox','generated-shadow-preview-decodes','automatic-pivot-follows-mother','generated-shadow-opacity-and-offset-controls','generation-off-preserves-imported-shadow','generation-on-restores-only-missing-shadows']

            js('document.getElementById("hand-set-save").click();true')
            until(lambda:len(bridge.hand_set_catalog.sets())==initial_count+1,'Save catalog')
            ready('state.handSets.length==='+str(initial_count+1)+'&&state.handSetDraft.name===""','Save repaint')
            assert not bridge.dirty
            saved=next(s for s in bridge.hand_set_catalog.sets() if s['name']=='NASA Custom UI')
            checks+=['save-named-set','draft-cleared-after-save','catalog-does-not-dirty-project']
            js('setTab("design");selected=state.resolvedElements.find(e=>e.kind==="analog"&&!e.aod).id;paint();true')
            analog=bridge.element({'id':js('selected')})
            preset=next(p for p in bridge.hand_presets if p.get('custom') and p['hand']=='hour' and p['setId']==saved['id'])
            assert js('Array.from(document.querySelector("[data-preset=hour]").options).some(o=>o.textContent.includes("NASA Custom UI"))')
            js('const model=document.querySelector("[data-preset=hour]");model.value='+json.dumps(preset['id'])+';model.dispatchEvent(new Event("change"));document.querySelector("[data-use-preset=hour]").click();true')
            until(lambda:bridge.element({'id':analog.id}).hour_preset==preset['id'],'Apply new set')
            applied=bridge.element({'id':analog.id})
            assert all(getattr(applied,r+'_preset')==preset['setMembers'][r] for r in ('hour','minute','second'))
            assert applied.hour_anchor_y==clicked[1] and applied.hour_shadow_offset_x==3
            assert all(getattr(applied,r+'_shadow_asset') in bridge.project.assets for r in ('hour','minute','second'))
            assert next(s for s in bridge.hand_set_catalog.sets() if s['id']==saved['id'])['generateShadows']
            checks+=['generated-shadows-persist-in-catalog','generated-shadows-auto-pair-into-project']
            checks+=['set-visible-in-hand-menu','hour-applies-matching-minute-second','stored-pivot-and-shadow-applied']
            assert all(getattr(applied,r+'_length')==50 and getattr(applied,r+'_width')==15 for r in ('hour','minute','second'))
            assert all(getattr(applied,r+'_length_adjusted') and getattr(applied,r+'_width_adjusted') for r in ('hour','minute','second'))
            expected=bridge.image_url(bridge.project.variant_project(bridge.variant),bridge.aod)
            ready('document.getElementById("preview").src==='+json.dumps(expected)+'&&document.getElementById("preview").complete','Immediate decoded model preview')
            assert js('document.getElementById("prop-hour_length").value==="50"&&document.getElementById("prop-hour_width").value==="15"')
            js('document.getElementById("prop-hour_length").dispatchEvent(new Event("change"));true')
            ready('document.getElementById("preview").src==='+json.dumps(expected),'Same-value edit changed model preview')
            bridge.send(preview='data:image/png;base64,AAAA',previewValues=bridge.values,previewSequence=bridge.state_sequence-1,progress='stale-frame-check')
            ready('document.getElementById("status").textContent==="stale-frame-check"','Old-frame event not processed')
            assert js('document.getElementById("preview").src==='+json.dumps(expected))
            assert bridge.values['day']==15
            checks+=['new-hand-defaults-50-and-15','model-activates-both-size-controls','model-preview-decoded-before-any-size-edit','same-value-edit-does-not-wake-or-change-preview','old-animation-frame-cannot-overwrite-applied-model','two-digit-day-preview-15']

            js('setTab("hands");document.querySelector(\'[data-set-load="'+saved['id']+'"]\').click();true')
            until(lambda:bridge.hand_set_draft['id']==saved['id'],'Load set for edit')
            ready('state.handSetDraft.id==='+json.dumps(saved['id']),'Edit draft repaint')
            # Save a screenshot of the populated dedicated panel for visual QA.
            ready('Array.from(document.querySelectorAll(".hand-set-pivot img")).every(i=>i.complete&&i.naturalWidth>0)','Draft images decode')
            until(lambda:js('document.querySelector(".hand-set-pivot img").getBoundingClientRect().height>0'),'Bitmap layout')
            deadline=time.monotonic()+.7
            while time.monotonic()<deadline:app.processEvents()
            screenshot=ROOT/'build/hand-sets-editor-1.7.6.png'
            assert window.grab().save(str(screenshot))
            original=bridge.project.metadata();assets=dict(bridge.project.assets)
            js('window.confirm=()=>true;document.querySelector(\'[data-set-delete="'+saved['id']+'"]\').click();true')
            until(lambda:len(bridge.hand_set_catalog.sets())==initial_count,'Delete personal set')
            ready('state.handSets.length==='+str(initial_count),'Delete repaint')
            assert bridge.project.metadata()==original and bridge.project.assets==assets
            checks+=['edit-existing-set','catalog-delete','applied-project-independent-of-catalog']
            window.close();app.processEvents()
    report={'status':'passed','applicationVersion':'1.7.6','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False,'hardwareTested':False,
            'screenshot':'build/hand-sets-editor-1.7.6.png'}
    (ROOT/'docs/hand-sets-editor-1.7.6.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
