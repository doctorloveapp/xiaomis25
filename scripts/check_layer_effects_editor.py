"""Source editor check for shape borders, ellipses and live/static shadows."""
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
from s5studio.color_picker import graphic_color_changes


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='effects-editor-',dir=ROOT/'build') as temporary:
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
            def action(code):return js('(()=>{'+code+';return true;})()')
            def ready(code,message):until(lambda:js(code),message)
            ready('Boolean(window.s5Ready&&state)','Startup')
            assert js('document.body.textContent.includes("Version 2.1")');checks.append('version-2.1')
            shape=Element(kind='rect',x=140,y=170,width=160,height=80,color='#ff0000')
            text=Element(kind='text',text='S5',x=150,y=80,width=160,height=44,size=28)
            live=Element(kind='number',source='heartRate',x=150,y=300,width=160,height=44,size=28)
            hand=Element(kind='analog',x=60,y=60,width=360,height=360)
            b.project=Project(elements=[shape,text,live,hand]);b.project.ensure_independent_variants();b._design=None;b.send(state=b.state())
            ready('state.layers.some(e=>e.id==='+json.dumps(shape.id)+')','Fixture')
            def select(element):action('selected='+json.dumps(element.id)+';S5Multi.pick(selected);paint()')
            def change(key,value,expected=None):
                target='document.querySelector('+json.dumps('[data-prop='+key+']')+')'
                action('const n='+target+';n[n.type==="checkbox"?"checked":"value"]='+json.dumps(value)+';n.dispatchEvent(new Event("change"))')
                ready('state.resolvedElements.find(e=>e.id===selected).'+key+'==='+json.dumps(value if expected is None else expected),'Commit '+key)
            select(shape)
            assert js('document.querySelector("[data-prop=fill_enabled]").checked&&document.querySelector("[data-prop=border_width]").value==="0"')
            checks.append('legacy-filled-shape-defaults')
            change('fill_enabled',False)
            assert b.element({'id':shape.id}).border_width==2;checks.append('outline-only-defaults-to-visible-border')
            change('border_width',7);checks.append('border-width-refreshes-preview')
            with patch('s5studio.color_picker.choose_graphic_color',lambda e,k,p:graphic_color_changes(e,k,'#12ab34')):
                action('document.querySelector("[data-prop=border_color]").click()')
                ready('state.resolvedElements.find(e=>e.id===selected).border_color==="#12ab34"','Border color')
            assert b.element({'id':shape.id}).color=='#ff0000';checks.append('independent-border-fill-colors')
            action('const n=document.getElementById("shape-kind");n.value="circle";n.dispatchEvent(new Event("change"))')
            ready('state.resolvedElements.find(e=>e.id===selected).kind==="circle"','Ellipse selected')
            assert (b.element({'id':shape.id}).width,b.element({'id':shape.id}).height)==(160,80)
            checks.append('shape-switch-preserves-nonsquare-geometry')
            change('width',190);assert b.element({'id':shape.id}).height==80
            change('height',95);assert b.element({'id':shape.id}).width==190
            checks.append('ellipse-width-height-independent')
            handle=json.dumps('.selection[data-element="'+shape.id+'"] [data-resize=se]')
            action('const h=document.querySelector('+handle+');const dx=24*document.getElementById("canvas").getBoundingClientRect().width/480;h.dispatchEvent(new PointerEvent("pointerdown",{bubbles:true,clientX:10,clientY:10,button:0,buttons:1}));window.dispatchEvent(new PointerEvent("pointermove",{clientX:10+dx,clientY:10}));window.dispatchEvent(new PointerEvent("pointerup"))')
            ready('state.resolvedElements.find(e=>e.id===selected).width===214','Ellipse drag')
            assert b.element({'id':shape.id}).height==95;checks.append('ellipse-drag-does-not-lock-aspect')
            change('shadow_enabled',True)
            for key,value in [('shadow_offset_x',-6),('shadow_offset_y',8),('shadow_blur',5),('shadow_spread',2)]:change(key,value)
            change('shadow_opacity',70,179);checks.append('shadow-parameters-and-percent-conversion')
            with patch('s5studio.color_picker.choose_graphic_color',lambda e,k,p:graphic_color_changes(e,k,None)):
                action('document.querySelector("[data-prop=shadow_color]").click()')
                ready('state.resolvedElements.find(e=>e.id===selected).shadow_color==="none"','Absent shadow color')
            assert b.element({'id':shape.id}).border_color=='#12ab34';checks.append('shadow-color-none-keeps-border-fill')
            for element in (text,live):
                select(element);change('shadow_enabled',True)
                for key in ('shadow_color','shadow_opacity','shadow_blur','shadow_spread'):
                    assert js('Boolean(document.querySelector('+json.dumps('[data-prop='+key+']')+'))')
                checks.append(element.kind+'-shadow-controls')
            select(hand);assert js('!document.querySelector("[data-prop=shadow_enabled]")');checks.append('hand-shadows-keep-existing-controls')
            select(shape);b.command(json.dumps({'action':'add-variant'}));b.send(state=b.state())
            ready('state.variantIndex===1','Second style');change('border_width',11)
            assert next(e for e in b.project.variant_project(0).elements if e.id==shape.id).border_width==7
            checks.append('independent-style-effects')
            b.command(json.dumps({'action':'undo'}));b.send(state=b.state())
            ready('state.resolvedElements.find(e=>e.id===selected).border_width===7','Undo effects')
            checks.append('undo-effects')
            assert not b.design.validate(),b.design.validate()
            window.view.grab().save(str(ROOT/'build/layer-effects-editor-2.1.png'))
            window.close();app.processEvents()
    report={'applicationVersion':'2.1','status':'passed','checks':checks,'checkCount':len(checks),
            'sourceEditorTested':True,'executableLaunched':False,'screenshot':'build/layer-effects-editor-2.1.png'}
    (ROOT/'docs/layer-effects-editor-2.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
