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
from s5studio.moon_disk import SOURCE,REFERENCE_DATE
from s5studio.render import element_image,png_bytes
from s5studio.complications import sample_values


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='editor-2.6-',dir=ROOT/'build') as temporary:
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
            assert js('document.body.textContent.includes("Version 2.6")')
            assert len(b.disk_presets)==90;checks.append('version-and-90-disc-catalog')
            assert js('document.getElementById("day").value')=='15'
            assert js('document.getElementById("day").min')=='1' and js('document.getElementById("day").max')=='31'
            assert (b.values['day'],b.values['month'],b.values['dateYear'],b.values['__moonDate'])==(15,10,2026,'2026-10-15')
            checks.append('simulation-day-field-range-and-shared-default-calendar')
            action('setTab("disks")');assert js('document.querySelectorAll("[data-disk-load]").length')==90
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
            assert js('document.querySelectorAll("[data-disk-delete]").length')==90
            command('disk-catalog-load',id=celestial['id'])
            action('document.querySelector('+json.dumps('[data-disk-delete="'+celestial['id']+'"]')+').click()')
            ready('state.diskPresets.length===89&&state.deletedDisks.length===1','Delete bundled disc')
            assert b.disk_draft['id']==''
            assert next(e for e in b.project.elements if e.id==identity).disk_shadow_assets
            action('document.querySelector('+json.dumps('[data-disk-restore="'+celestial['id']+'"]')+').click()')
            ready('state.diskPresets.length===90&&state.deletedDisks.length===0','Restore deleted disc')
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
            action('let el=document.querySelector("[data-prop=source]");el.value="timeMinute";el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).source==="timeMinute"','Civil minute source')
            assert js('document.querySelector("[data-prop=source] option[value=timeMinute]").textContent')=='Minuti giorno (0–59)'
            assert js('document.querySelectorAll("[data-prop=source] option[value=timeMinute]").length')==1
            assert (e.value_start,e.value_range,e.angle_start,e.angle_range)==(0,60,0,360)
            assert 'indipendenti dal cronografo' in js('state.sourceDescriptions.timeMinute')
            minute_path=directory/'civil-minute.s5faceproj';b.project.save(minute_path)
            assert next(e for e in Project.load(minute_path).elements if e.id==identity).source=='timeMinute'
            checks.append('civil-minutes-menu-label-default-scale-and-project-persistence')
            main=next(e for e in b.design.elements if e.kind=='analog' and not e.aod)
            action('selected='+json.dumps(main.id)+';S5Multi.pick(selected);paint();let el=document.querySelector("[data-prop=only_chrono]");el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).only_chrono','Only Crono flag')
            assert main.only_chrono and main.chrono_pro and main.second_hand
            assert b.values['__proValues'][main.id+'_second']==0
            checks.append('only-crono-enables-pro-and-parks-main-seconds')
            action('setTab("disks")')
            command('disk-catalog-new');command('disk-catalog-meta',changes={'source':SOURCE})
            assert [b.disk_draft[k] for k in ('valueStart','valueRange','angleStart','angleRange')]==[0,59,0,360]
            assert b.disk_draft['moonReferenceDate']==REFERENCE_DATE and b.disk_draft['moonDayOffset']==0
            assert js('Boolean(document.querySelector("[data-disk-meta=moonReferenceDate]"))')
            checks.append('lunar-source-auto-defaults-and-reference-fields')
            command('disk-catalog-load',id='disk-longines-moonphase-59')
            action('let el=document.getElementById("disk-moon-direction");el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.diskDraft.angleRange===-360','Catalog direction')
            command('disk-catalog-meta',changes={'moonDayOffset':2,'generateShadows':True});command('disk-catalog-save')
            r=command('add',kind='disk',preset='disk-longines-moonphase-59');identity=r['selectedLayer']
            e=b.element({'id':identity})
            assert (e.source,e.second_anchor_x,e.second_anchor_y,e.angle_range,e.moon_day_offset)==(SOURCE,240,240,-360,2)
            action('setTab("design");selected='+json.dumps(identity)+';S5Multi.pick(selected);paint()')
            assert js('Boolean(document.getElementById("moon-preview-date"))') and e.show_shadows
            checks.append('longines-graphic-center-pivot-shadow-catalog-calibration-applied')
            action('document.getElementById("moon-preview-reference").click()')
            ready('state.moonPositions['+json.dumps(identity)+']===2','Reference preview')
            before=b.project.metadata()
            action('let el=document.getElementById("moon-preview-date");el.value="2026-11-24";el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.moonPreviewDate==="2026-11-24"','Preview date')
            assert js('state.moonPositions['+json.dumps(identity)+']')==2
            command('moon-preview',date='2026-09-27')
            assert js('state.moonPositions['+json.dumps(identity)+']')==3
            assert b.project.metadata()==before
            action('document.getElementById("moon-preview-live").click()')
            ready('state.moonPreviewDate!=="2026-09-27"','Restore current preview date')
            checks.append('preview-calendar-59-day-cycle-does-not-change-exported-project')
            action('let el=document.querySelector("[data-prop=source]");el.value="dateMoon";el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).source==="dateMoon"','Native phase selection')
            assert (e.value_start,e.value_range,e.angle_start,e.angle_range)==(0,8,-90,180)
            action('let el=document.querySelector("[data-prop=source]");el.value="'+SOURCE+'";el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).source==="'+SOURCE+'"','Daily moon selection')
            assert (e.value_start,e.value_range,e.angle_start,e.angle_range,e.moon_day_offset)==(0,59,0,360,0)
            action('let el=document.getElementById("moon-direction");el.checked=true;el.dispatchEvent(new Event("change",{bubbles:true}))')
            ready('state.resolvedElements.find(e=>e.id===selected).angle_range===-360','Layer direction')
            command('edit',id=identity,changes={'moon_day_offset':-3,'angle_start':25})
            b.project.save(directory/'daily-moon.s5faceproj')
            saved=next(e for e in Project.load(directory/'daily-moon.s5faceproj').elements if e.id==identity)
            assert (saved.moon_day_offset,saved.angle_start,saved.angle_range)==(-3,25,-360)
            checks.append('native-eight-phases-preserved-daily-defaults-restored-calibration-saved')
            action('setTab("hands")');command('hand-set-new');command('hand-set-meta',changes={'small':True,'name':'Date hand'})
            assert js('Boolean(document.querySelector("[data-set-image=date]"))')
            with patch.object(b.dialogs,'open',return_value=str(path)):
                command('hand-set-image',role='date')
            command('hand-set-meta',changes={'generateShadows':True});command('hand-set-save')
            preset=next(p for p in b.hand_presets if p['hand']=='date')
            r=command('add',kind='pointer');identity=r['selectedLayer']
            command('hand-preset',id=identity,preset=preset['id'],hand='second')
            e=b.element({'id':identity});assert (e.source,e.value_start,e.value_range)==('dateDay',1,31)
            assert e.second_shadow_asset in b.project.assets
            checks.append('date-small-hand-role-import-shadow-save-and-calendar-auto-binding')
            date_hand=e
            r=command('add',kind='number');date_value=b.element({'id':r['selectedLayer']})
            command('edit',id=date_value.id,changes={'source':'dateDay'})
            r=command('add',kind='date');date_widget=b.element({'id':r['selectedLayer']})
            moon=next(e for e in b.design.elements if e.kind=='disk' and e.source==SOURCE)
            assert moon.disk_mode=='rotation'
            action('setTab("design");selected='+json.dumps(moon.id)+';S5Multi.pick(selected);paint()')
            metadata=b.project.metadata();dirty=b.dirty;undo=len(b.undo_stack)
            command('time',day=1,month=10,dateYear=2026)
            def bitmaps():
                p=b.project.variant_project(0);values=sample_values(b.values)
                return [png_bytes(element_image(p,e,values)) for e in (date_value,date_widget,date_hand,moon)]
            previous=bitmaps()
            for day in (9,15,31):
                action('let el=document.getElementById("day");el.value='+json.dumps(str(day))+';el.dispatchEvent(new Event("change",{bubbles:true}))')
                ready('state.values.day==='+str(day),'Simulated day '+str(day))
                assert sample_values(b.values)['dateDay']==day and b.values['__moonDate']==f'2026-10-{day:02}'
                assert js('document.getElementById("moon-preview-date").value')==b.values['__moonDate']
                current=bitmaps()
                assert all(a!=c for a,c in zip(previous,current)),(day,[e.kind+':'+e.source for e,a,c in zip((date_value,date_widget,date_hand,moon),previous,current) if a==c])
                previous=current
            assert b.project.metadata()==metadata and b.dirty==dirty and len(b.undo_stack)==undo
            checks.append('simulated-day-updates-live-date-date-widget-date-hand-and-moon-without-project-mutation')
            command('time',month=2);assert (b.values['day'],b.values['__moonDate'])==(28,'2026-02-28')
            command('time',dateYear=2028);command('time',day=29);assert b.values['__moonDate']=='2028-02-29'
            command('time',dateYear=2027);assert b.values['__moonDate']=='2027-02-28'
            for bad in (0,32,1.5,True,29):
                old_date=b.values['__moonDate']
                result=json.loads(b.command(json.dumps({'action':'time','day':bad})))
                assert result.get('error') and b.values['__moonDate']==old_date and b.values['day']==28
            checks.append('calendar-month-length-leap-year-clamping-and-invalid-days-rejected-atomically')
            action('document.getElementById("moon-preview-reference").click()')
            ready('state.values.__moonDate==="'+REFERENCE_DATE+'"','Shared moon reference')
            assert [js('document.getElementById('+json.dumps(k)+').value') for k in ('day','month','dateYear')]==['26','9','2026']
            for scenario,iso in [('Mezzanotte','2026-01-01'),('Valori alti','2026-12-31'),('Normale','2026-10-15')]:
                command('scenario',value=scenario)
                assert b.values['__moonDate']==iso and js('document.getElementById("moon-preview-date").value')==iso
            command('motion-preview',value=True);b.preview_tick()
            assert b.values['__moonDate']=='2026-10-15' and b.values['day']==15
            command('motion-preview',value=False)
            checks.append('moon-date-controls-scenarios-and-animated-preview-share-calendar')
            window.close();app.processEvents()
    report={'applicationVersion':'2.6','status':'passed','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/editor-2.6.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':check()
