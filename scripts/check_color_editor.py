"""Source UI check for the no-tint checkbox; never launch the packaged EXE."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,os,sys,time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS','--disable-gpu')
from PIL import Image
from PySide6.QtWidgets import QApplication
from s5studio.web_ui import MainWindow
from s5studio.model import Project,Element
from s5studio.render import png_bytes
from s5studio.color_picker import graphic_color_changes


def check():
    app=QApplication.instance() or QApplication([]);checks=[]
    with TemporaryDirectory(prefix='color-ui-',dir=ROOT/'build') as temporary:
        with patch('s5studio.web_ui.user_data_root',lambda:Path(temporary)/'user'):
            window=MainWindow(smoke=True);window.show();b=window.bridge;page=window.view.page()
            def until(predicate,message):
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    app.processEvents()
                    if predicate():return
                raise AssertionError(message)
            def js(code):
                replies=[];page.runJavaScript(code,replies.append)
                until(lambda:bool(replies),'JavaScript callback');return replies[0]
            def ready(expression,message):until(lambda:js(expression),message)
            ready('Boolean(window.s5Ready&&state)','Startup')
            raw=png_bytes(Image.new('RGBA',(20,80),(44,133,211,173)));key='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png'
            analog=Element(kind='analog',hour_asset=key,minute_asset=key,second_asset=key,hour_color='#ff0000',minute_color='#ff0000',second_color='#ff0000')
            pointer=Element(kind='pointer',second_asset=key,second_color='#ff0000')
            image=Element(kind='image',asset=key,tint=True,color='#ff0000',width=20,height=80)
            compass=Element(kind='compass',asset=key,tint=True,color='#ff0000',source='systemSensorCompass',value_range=360,angle_range=-360)
            b.project=Project(elements=[analog,pointer,image,compass],assets={key:raw});b.project.ensure_independent_variants();b._design=None
            b.send(state=b.state())
            ready('state.resolvedElements.some(e=>e.id==='+json.dumps(image.id)+')','Fixture repaint')
            calls=[];choice=[None]
            def picker(element,key,parent):
                calls.append((element.get("id","context") if isinstance(element,dict) else element.id,key));return graphic_color_changes(element,key,choice[0])
            with patch('s5studio.color_picker.choose_graphic_color',picker):
                for element,field in [(analog,'hour_color'),(analog,'minute_color'),(analog,'second_color'),(pointer,'second_color'),(image,'color'),(compass,'color')]:
                    js('selected='+json.dumps(element.id)+';S5Multi.pick(selected);paint();true')
                    ready('Boolean(document.querySelector('+json.dumps('[data-prop="'+field+'"]')+'))','Color control')
                    before=len(calls)
                    js('document.querySelector('+json.dumps('[data-prop="'+field+'"]')+').click();true')
                    until(lambda:len(calls)==before+1,'Color dialog command')
                    ready('document.querySelector('+json.dumps('[data-prop="'+field+'"]')+')?.dataset.originalColor==="true"','Original indicator')
                    current=b.element({'id':element.id})
                    assert not getattr(current,field) if field.endswith('_color') else not current.tint
                    checks.append(element.kind+'-'+field+'-restores-original')
                choice[0]='#123456'
                js('document.querySelector("[data-prop=color]").click();true')
                until(lambda:b.element({'id':compass.id}).color=='#123456','New tint applied')
                ready('document.querySelector("[data-prop=color]").dataset.originalColor==="false"','Tint indicator')
                assert b.element({'id':compass.id}).tint
                checks.append('choosing-color-reenables-tint')
            from s5studio.model import normalized_slot
            text=Element(kind='text');live=Element(kind='number');shape=Element(kind='rect')
            b.design.elements.extend([text,live,shape])
            slot=normalized_slot({'id':'colorslot','name':'Valore','x':20,'y':20,'options':['steps'],'default':'steps'})
            b.design.complications.append(slot);b.send(state=b.state())
            ready('state.layers.some(e=>e.id==="colorslot")','Universal fixture repaint')
            with patch('s5studio.color_picker.choose_graphic_color',lambda e,k,p:graphic_color_changes(e,k,None)):
                for identity,field in [(analog.id,'color'),(text.id,'color'),(live.id,'color'),(shape.id,'color'),('colorslot','color')]:
                    js('selected='+json.dumps(identity)+';S5Multi.pick(selected);paint();true')
                    selector=json.dumps('[data-prop="'+field+'"]')
                    ready('Boolean(document.querySelector('+selector+'))','Color field '+identity+' '+field)
                    js('document.querySelector('+selector+').click();true')
                    ready('document.querySelector('+selector+')?.dataset.originalColor==="true"','Universal absent color')
                    checks.append('universal-'+identity+'-'+field)
                assert not b.element({'id':analog.id}).show_center_cap
                assert b.element({'id':analog.id}).hour_asset==key
                for field in ('project-background','variant-accent','variant-background'):
                    js('paint();document.querySelector('+json.dumps('[data-prop="'+field+'"]')+').click();true')
                    ready('document.querySelector('+json.dumps('[data-prop="'+field+'"]')+')?.dataset.originalColor==="true"','Project/style absent color')
                    assert not b.design.validate(),b.design.validate()
                    checks.append(field+'-absent')
                js('selected='+json.dumps(live.id)+';S5Multi.pick(selected);paint();true')
                assert js('Boolean(document.querySelector("[data-prop=rotation]")&&document.querySelector("[data-prop=arc]"))')
                js('document.querySelector("[data-prop=rotation]").value=30;document.querySelector("[data-prop=rotation]").dispatchEvent(new Event("change"));true')
                until(lambda:b.element({'id':live.id}).rotation==30,'Live rotation command')
                js('document.querySelector("[data-prop=arc]").value=60;document.querySelector("[data-prop=arc]").dispatchEvent(new Event("change"));true')
                until(lambda:b.element({'id':live.id}).arc==60,'Live arc command')
                checks.append('live-data-rotation-and-arc-controls')
                assert js('[...document.querySelectorAll("input[type=color]")].every(e=>e.dataset.studioColorPicker==="true")')
                checks.append('every-color-control-uses-universal-picker')
            # Select compass again for the cancellation/undo test.
            js('selected='+json.dumps(compass.id)+';S5Multi.pick(selected);paint();true')
            before=b.project.metadata();undo=len(b.undo_stack);assets=dict(b.project.assets)
            with patch('s5studio.color_picker.choose_graphic_color',return_value=None):
                result=json.loads(b.command(json.dumps({'action':'choose-color','id':compass.id,'key':'color'})))
                assert 'error' not in result
            assert b.project.metadata()==before and len(b.undo_stack)==undo and b.project.assets==assets
            checks.append('cancel-preserves-project-and-undo')
            result=json.loads(b.command(json.dumps({'action':'undo'})));assert 'error' not in result
            assert b.element({'id':live.id}).arc==0
            checks.append('color-change-supports-undo')
            assert any(s['name']=='Hamilton Lancette' for s in b.hand_set_catalog.sets())
            checks.append('new-hamilton-set-is-bundled')
            window.close();app.processEvents()
    report={'status':'passed','applicationVersion':'1.8.1','checks':checks,'checkCount':len(checks),'sourceEditorTested':True,'executableLaunched':False}
    (ROOT/'docs/color-editor-1.8.1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
