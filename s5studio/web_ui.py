"""Offline Tailwind editor hosted in Qt, using the same tested Python build path."""
from dataclasses import asdict
import base64
import json
from pathlib import Path
import sys

from PySide6.QtCore import QObject,Signal,Slot,QThread,QTimer,QUrl,Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication,QMainWindow,QFileDialog,QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from .model import Project,Element,template,identifier,SOURCES,VARIANT_PROPERTIES,MAX_SLOTS,MAX_DESIGN_IMAGE_SIZE,normalized_slot
from .watchface_library import library
from .render import render,png_bytes,SCENARIOS,layout_errors
from .native import build
from .hand_presets import preset_changes,clear_hand_changes


def application_root():
    return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]


class BuildTask(QThread):
    progress=Signal(str)
    finished_build=Signal(str,str)

    def __init__(self,project,compiler,destination):
        super().__init__()
        self.project=project.copy();self.compiler=compiler;self.destination=destination

    def run(self):
        try:self.finished_build.emit(str(build(self.project,self.compiler,self.destination,self.progress.emit)),'')
        except Exception as exc:self.finished_build.emit('',str(exc))


class LocalPage(QWebEnginePage):
    def acceptNavigationRequest(self,url,nav_type,is_main_frame):
        return url.scheme() in ('file','qrc','data','about')


class StudioBridge(QObject):
    event=Signal(str)

    def __init__(self,window,*,smoke=False):
        super().__init__(window)
        self.window=window;self.root=application_root();self.project=template('Analogico')
        self.path=None;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
        self.variant=0;self.aod=False;self.scenario='Normale';self.values=dict(SCENARIOS['Normale'])
        self.worker=None;self.output=None;self.smoke=smoke
        self.compiler=self.root/'tools/easyface-4.23/Compiler.exe'
        self.hand_presets=[]
        from PIL import Image
        from io import BytesIO
        for preset in library()['hands']:
            path=self.root/preset['assetPath']
            if not path.is_file():continue
            with Image.open(path) as im:
                im=im.convert('RGBA')
                # Gallery-only crop: the imported bitmap and its pivot stay intact.
                bounds=im.getchannel('A').getbbox()
                if bounds:im=im.crop(bounds)
                im.thumbnail((96,110));out=BytesIO();im.save(out,format='PNG')
            self.hand_presets.append({**preset,'thumbnail':'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()})
        self.recovery=self.root/'data/recovery-web.s5faceproj'
        self.timer=QTimer(self);self.timer.setInterval(20000);self.timer.timeout.connect(self.autosave)
        if not smoke:self.timer.start()

    def image_url(self,p,aod=False):
        return 'data:image/png;base64,'+base64.b64encode(png_bytes(render(p,self.values,aod))).decode()

    def state(self):
        from .complications import ALIASES
        # Lossless migration of old Studio aliases to the observed source names:
        # both keys have the same native code, but should appear only once.
        for s in self.project.complications:
            s['options']=list(dict.fromkeys(ALIASES.get(k,k) for k in s['options']))
            s['default']=ALIASES.get(s['default'],s['default'])
        selectable={'none':'Nessuna',**{k:v[0] for k,v in SOURCES.items() if k not in ALIASES}}
        resolved=self.project.variant_project(0 if self.aod else self.variant)
        result=self.project.metadata()
        result.update(variantIndex=self.variant,aod=self.aod,dirty=self.dirty,path=str(self.path or ''),
                      preview=self.image_url(resolved,self.aod),
                      thumbnails=[self.image_url(self.project.variant_project(i)) for i in range(len(self.project.variants))],
                      resolvedElements=[asdict(e) for e in resolved.elements if e.id in {x.id for x in self.project.elements}],
                      layers=[asdict(e) if isinstance(e,Element) else {**e,'kind':'complication','aod':False}
                              for mode in (False,True) for e in resolved.ordered_layers(mode)
                              if (e.id if isinstance(e,Element) else e['id']) in
                              ({x.id for x in self.project.elements}|{s['id'] for s in self.project.complications})],
                      errors=self.project.validate()+layout_errors(resolved),
                      busy=bool(self.worker and self.worker.isRunning()),output=str(self.output or ''),
                      sources={key:label for key,(label,_,_) in SOURCES.items()},scenario=self.scenario,values=self.values,
                      complications=[normalized_slot(s) for s in self.project.complications],maxSlots=MAX_SLOTS,handPresets=self.hand_presets,
                      complicationSources=selectable,
                      scenarios=list(SCENARIOS),
                      maxImageSize=MAX_DESIGN_IMAGE_SIZE,
                      canUndo=bool(self.undo_stack),canRedo=bool(self.redo_stack))
        return result

    def send(self,**values):self.event.emit(json.dumps(values,ensure_ascii=False))

    def autosave(self):
        if self.dirty and not self.project.validate():
            try:self.project.save(self.recovery)
            except Exception:pass

    def offer_recovery(self):
        if self.smoke or not self.recovery.exists():return
        if QMessageBox.question(self.window,'Recupero progetto','Riprendere il progetto recuperato dopo la chiusura precedente?')==QMessageBox.StandardButton.Yes:
            try:self.project=Project.load(self.recovery);self.dirty=True;self.send(state=self.state())
            except Exception as exc:self.send(error=str(exc))

    def confirm_leave(self):
        if self.smoke:return True
        if not self.dirty:return True
        answer=QMessageBox.question(self.window,'Progetto modificato','Salvare le modifiche al progetto?',
                                    QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
        if answer==QMessageBox.StandardButton.Cancel:return False
        if answer==QMessageBox.StandardButton.Save:return self.save()
        return True

    def save(self):
        suggested=self.path or self.root/'projects/Il_mio_S5.s5faceproj'
        filename,_=QFileDialog.getSaveFileName(self.window,'Salva progetto',str(suggested),'Progetti S5 (*.s5faceproj)')
        if not filename:return False
        path=Path(filename)
        if path.suffix.lower()!='.s5faceproj':path=path.with_suffix('.s5faceproj')
        self.project.save(path,png_bytes(render(self.project.variant_project(self.variant))))
        self.path=path;self.dirty=False
        if not self.smoke:self.recovery.unlink(missing_ok=True)
        return True

    def element(self,req):
        return next(e for e in self.project.elements if e.id==req['id'])

    def layer(self,key):
        for e in self.project.elements:
            if e.id==key:return e
        for slot in self.project.complications:
            if slot['id']==key:return slot
        raise ValueError('Livello non trovato.')

    def remove_layer(self,key):
        layer=self.layer(key)
        if isinstance(layer,Element):
            self.project.elements.remove(layer)
            for v in self.project.variants:v.get('overrides',{}).pop(key,None)
        else:self.project.complications.remove(layer)
        self.project.layer_order=[k for k in self.project.layer_order if k!=key]

    def reorder_layer(self,key,target,placement):
        if key==target:return
        source=self.layer(key);other=self.layer(target)
        source_aod=source.aod if isinstance(source,Element) else False
        other_aod=other.aod if isinstance(other,Element) else False
        if source_aod!=other_aod:raise ValueError('Riordina i livelli nella stessa schermata.')
        if placement not in ('above','below'):raise ValueError('Posizione di riordino non valida.')
        order=self.project.layer_order
        order.remove(key);position=order.index(target)+(placement=='above')
        order.insert(position,key)

    def import_image(self):
        filename,_=QFileDialog.getOpenFileName(self.window,'Importa immagine',str(self.root),'Immagini (*.png *.jpg *.jpeg *.webp *.bmp *.svg)')
        if not filename:return None
        if Path(filename).suffix.lower()=='.svg':
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtGui import QImage,QPainter
            import tempfile
            svg=QSvgRenderer(filename)
            if not svg.isValid():raise ValueError('SVG non valido.')
            size=svg.defaultSize();size.scale(1920,1920,Qt.AspectRatioMode.KeepAspectRatio)
            image=QImage(size,QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.transparent)
            painter=QPainter(image);svg.render(painter);painter.end()
            self.root.joinpath('data').mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir=self.root/'data') as temp:
                path=Path(temp)/'import.png';image.save(str(path));el=self.project.add_image(path)
            el.name=Path(filename).stem
            return el
        return self.project.add_image(Path(filename))

    @Slot(str,result=str)
    def command(self,raw):
        before=None;selection=None
        try:
            req=json.loads(raw);action=req.get('action')
            mutations={'add','edit','nudge','delete','duplicate','move-layer','reorder-layer','fit-image','image','font','hand-image','hand-preset','clear-hand','variant-image','add-variant','edit-variant','delete-variant','add-slot','edit-slot','delete-slot','settings'}
            if action in mutations:
                if self.worker and self.worker.isRunning():raise ValueError('Attendi la fine della compilazione.')
                before=self.project.copy()
                self.project.sync_layer_order()
            if action=='state':pass
            elif action=='new':
                if self.confirm_leave():
                    self.project=template(req.get('template','Analogico'));self.path=None;self.variant=0;self.aod=False;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
                    if not self.smoke:self.recovery.unlink(missing_ok=True)
            elif action=='open':
                if self.confirm_leave():
                    filename,_=QFileDialog.getOpenFileName(self.window,'Apri progetto',str(self.root/'projects'),'Progetti S5 (*.s5faceproj)')
                    if filename:
                        self.project=Project.load(Path(filename));self.path=Path(filename);self.variant=0;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
                        if not self.smoke:self.recovery.unlink(missing_ok=True)
            elif action in ('save','save-as'):
                self.save()
            elif action=='undo' and self.undo_stack:
                self.redo_stack.append(self.project.copy());self.project=self.undo_stack.pop();self.variant=min(self.variant,len(self.project.variants)-1);self.dirty=True
            elif action=='redo' and self.redo_stack:
                self.undo_stack.append(self.project.copy());self.project=self.redo_stack.pop();self.dirty=True
            elif action=='add':
                kind=req['kind']
                defaults={'clock':dict(name='Ora',x=57,y=144,width=366,height=108,size=90),'date':dict(name='Data',x=158,y=258,width=164,height=40,size=30),'analog':dict(name='Lancette',x=60,y=60,width=360,height=360,color='#6ce5c1',second_hand=not self.aod),'number':dict(name='Dato',x=166,y=340,width=148,height=46,size=30),'text':dict(name='Testo',x=140,y=100,width=200,height=40,size=24),'rect':dict(name='Rettangolo'),'circle':dict(name='Cerchio')}
                defaults['pointer']=dict(name='Lancetta piccola',x=180,y=180,width=120,height=120,source='second',color='#f7be69',second_length=40,second_width=3,show_ticks=False)
                if kind not in defaults:raise ValueError('Componente non supportato.')
                added=Element(kind=kind,aod=self.aod,**defaults[kind]);self.project.elements.append(added);selection=added.id
            elif action=='edit':
                e=self.element(req);changes=req['changes']
                allowed=set(Element.__dataclass_fields__)-{'id','kind'}
                if set(changes)-allowed:raise ValueError('Proprietà non supportata.')
                if req.get('variantOnly'):
                    if self.aod:raise ValueError('L’AOD è comune agli stili: togli “Modifica soltanto questo stile”.')
                    permitted=VARIANT_PROPERTIES
                    if set(changes)-permitted:raise ValueError('Questa proprietà si applica a tutte le varianti.')
                    overrides=self.project.variants[self.variant].setdefault('overrides',{}).setdefault(e.id,{})
                    overrides.update(changes)
                else:
                    for k,v in changes.items():setattr(e,k,v)
            elif action=='nudge':
                layer=self.layer(req['id']);dx=req.get('dx',0);dy=req.get('dy',0)
                if type(dx) is not int or type(dy) is not int or abs(dx)>100 or abs(dy)>100:raise ValueError('Spostamento non valido.')
                if isinstance(layer,Element):
                    resolved=next(e for e in self.project.variant_project(0 if self.aod else self.variant).elements if e.id==layer.id)
                    if not layer.locked:
                        low=-MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else 0
                        xmax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-resolved.width)
                        ymax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-resolved.height)
                        changes={'x':max(low,min(xmax,resolved.x+dx)),'y':max(low,min(ymax,resolved.y+dy))}
                        if req.get('variantOnly') and not self.aod:self.project.variants[self.variant].setdefault('overrides',{}).setdefault(layer.id,{}).update(changes)
                        else:
                            # Translate explicit positions too, so a common edit
                            # visibly moves the selected style and all others.
                            base_xmax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-layer.width)
                            base_ymax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-layer.height)
                            changes={'x':max(low,min(base_xmax,layer.x+dx)),'y':max(low,min(base_ymax,layer.y+dy))}
                            for k,v in changes.items():setattr(layer,k,v)
                            if not layer.aod:
                                for variant in self.project.variants:
                                    override=variant.get('overrides',{}).get(layer.id,{})
                                    for key,delta in [('x',dx),('y',dy)]:
                                        if key in override:
                                            size=override.get('width' if key=='x' else 'height',getattr(layer,'width' if key=='x' else 'height'))
                                            high=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-size)
                                            override[key]=max(low,min(high,override[key]+delta))
                    else:self.project=before;before=None
                else:
                    layer=normalized_slot(layer)
                    if not layer['locked']:
                        self.layer(req['id']).update(x=max(0,min(480-layer['width'],layer['x']+dx)),y=max(0,min(480-layer['height'],layer['y']+dy)))
                    else:self.project=before;before=None
            elif action=='delete':
                self.remove_layer(req['id']);selection=''
            elif action=='duplicate':
                from copy import deepcopy
                original=self.layer(req['id']);e=deepcopy(original)
                if isinstance(e,Element):e.id=identifier();e.name+=' copia';self.project.elements.append(e);selection=e.id
                else:
                    if len(self.project.complications)>=MAX_SLOTS:raise ValueError(f'Limite Studio: {MAX_SLOTS} slot.')
                    e['id']=identifier();e['name']+=' copia';self.project.complications.append(e);selection=e['id']
                self.project.sync_layer_order();self.reorder_layer(selection,req['id'],'above')
            elif action=='move-layer':
                e=self.layer(req['id']);mode=e.aod if isinstance(e,Element) else False
                order=[x.id if isinstance(x,Element) else x['id'] for x in self.project.ordered_layers(mode)]
                index=order.index(req['id']);direction=1 if int(req['direction'])>0 else -1
                if 0<=index+direction<len(order):self.reorder_layer(req['id'],order[index+direction],'above' if direction>0 else 'below')
            elif action=='reorder-layer':self.reorder_layer(req['id'],req['targetId'],req['placement'])
            elif action=='fit-image':
                e=self.element(req)
                if e.kind!='image' or req.get('fit','cover') not in ('cover','contain'):raise ValueError('Seleziona un livello immagine.')
                changes={'x':0,'y':0,'width':480,'height':480,'fit':req.get('fit','cover')}
                if req.get('variantOnly') and not self.aod:self.project.variants[self.variant].setdefault('overrides',{}).setdefault(e.id,{}).update(changes)
                else:
                    for k,v in changes.items():setattr(e,k,v)
            elif action in ('image','variant-image','hand-image'):
                el=self.import_image()
                if el:
                    if action=='image':el.aod=self.aod;selection=el.id
                    else:
                        self.project.elements.remove(el)
                        if action=='variant-image':self.project.variants[self.variant]['imageAsset']=el.asset
                        else:
                            hand=req['hand']
                            if hand not in ('hour','minute','second'):raise ValueError('Lancetta non valida.')
                            self.set_hand(req,clear_hand_changes(hand,el.asset))
            elif action=='hand-preset':
                preset=next(h for h in self.hand_presets if h['id']==req['preset'])
                self.set_hand(req,preset_changes(self.project,self.element(req),self.root,preset,req['hand'],self.hand_presets))
            elif action=='clear-hand':
                self.set_hand(req,clear_hand_changes(req['hand']))
            elif action=='font':
                filename,_=QFileDialog.getOpenFileName(self.window,'Importa font',str(self.root),'Font (*.ttf *.otf)')
                if filename:self.element(req).font_asset=self.project.add_font(Path(filename))
            elif action=='add-variant':
                if len(self.project.variants)>=5:raise ValueError('Sono disponibili fino a cinque stili.')
                from copy import deepcopy
                v=deepcopy(self.project.variants[self.variant]);v['id']=identifier();v['name']=f'Stile {len(self.project.variants)+1}'
                self.project.variants.append(v);self.variant=len(self.project.variants)-1
            elif action=='edit-variant':
                allowed={'name','accent','background','imageAsset','overrides'}
                if set(req['changes'])-allowed:raise ValueError('Proprietà variante non valida.')
                self.project.variants[self.variant].update(req['changes'])
            elif action=='delete-variant':
                if len(self.project.variants)==1:raise ValueError('Mantieni almeno uno stile.')
                self.project.variants.pop(self.variant);self.variant=0
            elif action=='select-variant':self.variant=max(0,min(int(req['index']),len(self.project.variants)-1))
            elif action=='add-slot':
                if len(self.project.complications)>=MAX_SLOTS:raise ValueError(f'Limite Studio: {MAX_SLOTS} slot.')
                n=len(self.project.complications)
                x,y=[(90,112),(280,112),(28,228),(342,228),(185,332)][n%5]
                slot=normalized_slot({'id':identifier(),'name':f'Complicazione {n+1}','x':x,'y':y,'width':110,'height':44,'size':32,
                                      'frame':'none','showLabel':False,'showUnit':False,'weatherMode':'value',
                                      'options':['none','steps','heartRate','weatherCurrentTemperature','systemSensorCompass','weatherCurrentWeather'],
                                      'default':['steps','heartRate','weatherCurrentTemperature','systemSensorCompass','weatherCurrentWeather'][n%5]})
                self.project.complications.append(slot);selection=slot['id']
            elif action=='edit-slot':
                slot=next(s for s in self.project.complications if s['id']==req['id'])
                if set(req['changes'])-{'name','x','y','width','height','size','decimals','digits','unit','color','background','frame','showLabel','showUnit','weatherMode','visible','locked','opacity','align','options','default'}:raise ValueError('Proprietà slot non valida.')
                slot.update(req['changes'])
            elif action=='slot-preview':
                slot=next(s for s in self.project.complications if s['id']==req['id'])
                if req['choice'] not in slot['options']:raise ValueError('Opzione non disponibile.')
                self.values.setdefault('__choices',{})[slot['id']]=req['choice']
            elif action=='delete-slot':self.remove_layer(req['id']);selection=''
            elif action=='settings':
                mapping={'name':'name','author':'author','version':'version','background':'background','aodEnabled':'aod_enabled','faceId':'face_id'}
                for key,value in req['changes'].items():
                    if key not in mapping:raise ValueError('Impostazione non valida.')
                    setattr(self.project,mapping[key],value)
                if self.project.aod_enabled and not any(e.aod and e.kind in ('clock','analog') for e in self.project.elements):
                    self.project.elements.append(Element(kind='analog',name='Lancette AOD',x=80,y=80,width=320,height=320,color='#808080',aod=True))
            elif action=='aod':self.aod=bool(req['value']) and self.project.aod_enabled
            elif action=='scenario':
                self.scenario=req['value'];self.values=dict(SCENARIOS[self.scenario])
            elif action=='time':self.values.update({key:int(req[key]) for key in ('hour','minute','second') if key in req})
            elif action=='compiler':
                filename,_=QFileDialog.getOpenFileName(self.window,'Seleziona EasyFace 4.23',str(self.compiler.parent),'Compilatore (Compiler.exe)')
                if filename:self.compiler=Path(filename)
            elif action=='build':
                if self.worker and self.worker.isRunning():raise ValueError('Compilazione già in corso.')
                destination=QFileDialog.getExistingDirectory(self.window,'Cartella di esportazione',str(self.root/'dist'))
                if destination:
                    self.worker=BuildTask(self.project,self.compiler,Path(destination))
                    self.worker.progress.connect(lambda message:self.send(progress=message))
                    self.worker.finished_build.connect(self.build_complete);self.worker.start()
            elif action=='show-output' and self.output:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output)))
            elif action=='export-preview':
                filename,_=QFileDialog.getSaveFileName(self.window,'Salva anteprima',str(self.root/'preview.png'),'PNG (*.png)')
                if filename:Path(filename).write_bytes(png_bytes(render(self.project.variant_project(0 if self.aod else self.variant),self.values,self.aod)))
            if before:
                self.project.sync_layer_order()
                errors=self.project.validate()
                if errors:raise ValueError('\n'.join(errors))
                if self.project.metadata()!=before.metadata():
                    self.undo_stack.append(before);self.undo_stack=self.undo_stack[-40:];self.redo_stack=[];self.dirty=True
            reply={'state':self.state()}
            if selection is not None:reply['selectedLayer']=selection
            return json.dumps(reply,ensure_ascii=False)
        except Exception as exc:
            if before:self.project=before;self.variant=min(self.variant,len(self.project.variants)-1)
            return json.dumps({'error':str(exc)},ensure_ascii=False)

    def build_complete(self,path,error):
        if path:self.output=Path(path)
        self.send(state=self.state(),error=error,progress='ZIP pronto: '+path if path else 'Compilazione interrotta.',buildDone=bool(path))

    def set_hand(self,req,changes):
        if req.get('hand') not in ('hour','minute','second'):raise ValueError('Lancetta non valida.')
        e=self.element(req)
        if e.kind not in ('analog','pointer'):raise ValueError('Seleziona un livello lancette.')
        if req.get('variantOnly') and not self.aod:self.project.variants[self.variant].setdefault('overrides',{}).setdefault(e.id,{}).update(changes)
        else:
            for k,v in changes.items():setattr(e,k,v)
            if not e.aod:
                for variant in self.project.variants:
                    override=variant.get('overrides',{}).get(e.id,{})
                    for key in changes:override.pop(key,None)


class MainWindow(QMainWindow):
    def __init__(self,*,smoke=False):
        super().__init__()
        self.setWindowTitle('S5 Studio 0.8 — Xiaomi Watch S5');self.resize(1440,920);self.setMinimumSize(1120,760)
        self.view=QWebEngineView(self);self.view.setPage(LocalPage(self.view));self.setCentralWidget(self.view)
        self.bridge=StudioBridge(self,smoke=smoke)
        self.channel=QWebChannel(self.view.page());self.channel.registerObject('studio',self.bridge);self.view.page().setWebChannel(self.channel)
        base=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else self.bridge.root
        self.view.setUrl(QUrl.fromLocalFile(str(base/'frontend/index.html')))
        if not smoke:QTimer.singleShot(1800,self.bridge.offer_recovery)

    def show_editor(self):
        self.showMaximized()

    def closeEvent(self,event):
        if self.bridge.worker and self.bridge.worker.isRunning():event.ignore();return
        if self.bridge.smoke or self.bridge.confirm_leave():
            self.bridge.timer.stop()
            if not self.bridge.smoke:self.bridge.recovery.unlink(missing_ok=True)
            event.accept()
        else:event.ignore()


def launch():
    app=QApplication.instance() or QApplication(sys.argv);app.setApplicationName('S5 Studio')
    window=MainWindow();window.show_editor();return app.exec()
