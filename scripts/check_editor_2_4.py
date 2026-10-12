"""Exercise the source UI and dialogs, never the packaged executable."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PySide6.QtWidgets import QApplication
from PIL import Image,ImageDraw
from s5studio.web_ui import MainWindow
from s5studio.model import Element,Project


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='editor-2.4-',dir=ROOT/'build') as temporary:
        directory=Path(temporary)
        with patch('s5studio.web_ui.user_data_root',lambda:directory/'user'):
            window=MainWindow(smoke=True);window.show();b=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                result=[];page.runJavaScript(code,result.append);until(lambda:bool(result),'JavaScript callback');return result[0]
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,message):until(lambda:js(code),message)
            def command(name,**values):
                result=json.loads(b.command(json.dumps({'action':name,**values})))
                assert 'error' not in result,result
                b.send(state=result['state']);return result
            ready('Boolean(window.s5Ready&&state)','Startup')
            assert js('document.body.textContent.includes("Version 2.4")')
            assert len(b.disk_presets)==89;checks.append('version-and-89-disc-catalog')
            action('setTab("disks")');assert js('document.querySelectorAll("[data-disk-load]").length')==89
            celestial=next(p for p in b.disk_presets if p['category']=='celestial' and p['frames']==30)
            command('disk-catalog-load',id=celestial['id'])
            ready('state.diskDraft.id==='+json.dumps(celestial['id']),'Load sequence')
            assert js('document.getElementById("disk-frame").options.length')==30
            command('disk-catalog-meta',changes={'generateShadows':True})
            assert all(i.get('shadow',{}).get('generated') for i in b.disk_draft['hands'].values())
            command('disk-catalog-save');checks.append('edit-lunar-sequence-generate-all-shadows')
            r=command('add',kind='disk',preset=celestial['id']);identity=r['selectedLayer']
            action('setTab("design");selected='+json.dumps(identity)+';S5Multi.pick(selected);paint()')
            assert js('Boolean(document.getElementById("disk-applied-pivot"))')
            assert b.element({'id':identity}).show_shadows
            p=directory/'disc.s5faceproj';b.project.save(p);loaded=Project.load(p)
            assert next(e for e in loaded.elements if e.id==identity).disk_shadow_assets
            checks.append('apply-disc-level-pivot-preview-save-load')
            action('setTab("disks");window.confirm=()=>true')
            assert js('document.querySelectorAll("[data-disk-delete]").length')==89
            command('disk-catalog-load',id=celestial['id'])
            action('document.querySelector('+json.dumps('[data-disk-delete="'+celestial['id']+'"]')+').click()')
            ready('state.diskPresets.length===88&&state.deletedDisks.length===1','Delete bundled disc')
            assert b.disk_draft['id']==''
            assert next(e for e in b.project.elements if e.id==identity).disk_shadow_assets
            action('document.querySelector('+json.dumps('[data-disk-restore="'+celestial['id']+'"]')+').click()')
            ready('state.diskPresets.length===89&&state.deletedDisks.length===0','Restore deleted disc')
            checks.append('delete-bundled-disc-button-project-preserved-and-restore')
            command('disk-catalog-new');command('disk-catalog-meta',changes={'source':'dateMoon'})
            assert js('document.getElementById("disks-panel").textContent.includes("8 stati (0–7)")')
            command('disk-catalog-meta',changes={'source':'dateLunarDay'})
            assert js('document.getElementById("disks-panel").textContent.includes("ciclo continuo di 59 giorni")')
            checks.append('lunar-source-help-distinguishes-eight-phases-and-daily-month-reset')
            command('disk-catalog-new');command('disk-catalog-meta',changes={'name':'My Sun'})
            im=Image.new('RGBA',(80,80));ImageDraw.Draw(im).ellipse((10,10,69,69),fill='yellow');path=directory/'sun.png';im.save(path)
            with patch.object(b.dialogs,'open',return_value=str(path)):
                command('disk-catalog-image',key='disk')
            assert b.disk_draft['hands']['disk']['pivot']==[40,40]
            command('disk-catalog-part',key='disk',changes={'pivot':[38,42]})
            command('disk-catalog-meta',changes={'generateShadows':True})
            command('disk-catalog-save')
            custom=next(p for p in b.disk_presets if p['name']=='My Sun')
            command('add',kind='disk',preset=custom['id'])
            command('disk-catalog-delete',id=custom['id'])
            assert not any(p['id']==custom['id'] for p in b.disk_presets)
            checks.append('import-custom-png-center-click-edit-shadow-delete')
            r=command('add',kind='number');identity=r['selectedLayer'];command('edit',id=identity,changes={'source':'dateMonth'})
            action('selected='+json.dumps(identity)+';S5Multi.pick(selected);paint();let el=document.querySelector("[data-prop=month_abbreviated]");el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).month_abbreviated','Month flag')
            assert b.element({'id':identity}).month_abbreviated;checks.append('month-abbreviation-checkbox')
            command('edit',id=identity,changes={'source':'dateMoon'})
            assert js('document.querySelector("[data-prop=source]").textContent.includes("Fasi lunari")')
            assert not b.project.validate();checks.append('live-lunar-phase-native-menu')
            r=command('add',kind='pointer');identity=r['selectedLayer']
            action('selected='+json.dumps(identity)+';S5Multi.pick(selected);paint();let el=document.querySelector("[data-prop=source]");el.value="timeHour24";el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).source==="timeHour24"','24 hour source')
            e=b.element({'id':identity});assert (e.value_start,e.value_range,e.angle_start,e.angle_range)==(0,24,0,360)
            assert js('document.querySelector("[data-prop=source]").value')=='timeHour24'
            checks.append('24h-small-hand-source-and-one-daily-revolution')
            main=next(e for e in b.design.elements if e.kind=='analog' and not e.aod)
            action('selected='+json.dumps(main.id)+';S5Multi.pick(selected);paint();let el=document.querySelector("[data-prop=only_chrono]");el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).only_chrono','Only Crono flag')
            assert main.only_chrono and main.chrono_pro and main.second_hand
            assert b.values['__proValues'][main.id+'_second']==0
            checks.append('only-crono-enables-pro-and-parks-main-seconds')
            window.close();app.processEvents()
    report={'applicationVersion':'2.4','status':'passed','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/editor-2.4.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':check()
