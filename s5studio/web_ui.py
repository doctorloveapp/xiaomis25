"""Offline Tailwind editor hosted in Qt, using the same tested Python build path."""
from dataclasses import asdict
import base64
import json
from pathlib import Path
import sys
import time

from PySide6.QtCore import QObject,Signal,Slot,QThread,QTimer,QUrl,Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication,QMainWindow,QFileDialog,QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from .model import Project,Element,template,identifier,SOURCES,VARIANT_PROPERTIES,MAX_SLOTS,MAX_DESIGN_IMAGE_SIZE,normalized_slot
from .watchface_library import library
from .render import render,png_bytes,SCENARIOS,layout_errors,hand_preview,hand_edit_changes
from .native import build
from .hand_presets import preset_changes,clear_hand_changes
from .paths import application_root,resource_root,user_data_root,default_compiler


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

    def javaScriptConsoleMessage(self,level,message,line,source):
        if level==QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel and sys.stderr:
            print(f'Editor JavaScript: {source}:{line}: {message}',file=sys.stderr)


class StudioBridge(QObject):
    event=Signal(str)

    def __init__(self,window,*,smoke=False):
        super().__init__(window)
        self.window=window;self.root=application_root();self.resources=resource_root();self.project=template('Analogico')
        self.path=None;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
        self.variant=0;self.aod=False;self.scenario='Normale';self.values=dict(SCENARIOS['Normale'])
        self.worker=None;self.output=None;self.smoke=smoke
        self.state_sequence=0
        self.compiler=default_compiler()
        self.chrono_state='reset';self.chrono_elapsed=0;self.chrono_started=0;self.motion_preview=False;self.motion_started=0
        self.motion_timer=QTimer(self);self.motion_timer.setInterval(100);self.motion_timer.timeout.connect(self.preview_tick)
        self.hand_presets=[]
        from PIL import Image
        from io import BytesIO
        for preset in library()['hands']:
            path=self.resources/preset['assetPath']
            if not path.is_file():continue
            with Image.open(path) as im:
                im=im.convert('RGBA')
                # Gallery-only crop: the imported bitmap and its pivot stay intact.
                bounds=im.getchannel('A').getbbox()
                if bounds:im=im.crop(bounds)
                im.thumbnail((96,110));out=BytesIO();im.save(out,format='PNG')
            self.hand_presets.append({**preset,'thumbnail':'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()})
        self.compass_presets=[]
        for preset in library().get('compasses',[]):
            with Image.open(self.resources/preset['assetPath']) as im:
                im=im.convert('RGBA');im.thumbnail((100,100))
                self.compass_presets.append({**preset,'thumbnail':'data:image/png;base64,'+base64.b64encode(png_bytes(im)).decode()})
        self.recovery=user_data_root()/'recovery-web.s5faceproj'
        self.timer=QTimer(self);self.timer.setInterval(20000);self.timer.timeout.connect(self.autosave)
        if not smoke:self.timer.start()

    def image_url(self,p,aod=False):
        return 'data:image/png;base64,'+base64.b64encode(png_bytes(render(p,self.values,aod))).decode()

    def state(self):
        self.state_sequence+=1
        from .complications import ALIASES
        # Lossless migration of old Studio aliases to the observed source names:
        # both keys have the same native code, but should appear only once.
        for s in self.project.complications:
            s['options']=list(dict.fromkeys(ALIASES.get(k,k) for k in s['options']))
            s['default']=ALIASES.get(s['default'],s['default'])
        selectable={'none':'Nessuna',**{k:v[0] for k,v in SOURCES.items() if k not in ALIASES}}
        resolved=self.project.variant_project(0 if self.aod else self.variant)
        from .source_help import source_choices
        pointer_sources,source_descriptions=source_choices(SOURCES)
        from .motion import LUA_SOURCES
        from .motion import excluded_from_aod
        lua_sources={k:v[0] for k,v in LUA_SOURCES.items()}
        source_descriptions.update({
            'studioDecisecond':'Decimi da 0 a 9: intervallo 10 e rotazione 360°, un giro ogni secondo (1 Hz). Runtime Lua; esclusa in AOD.',
            'studioChronoHour':'Ore trascorse del cronografo su 12 ore. Tap sul sottoquadrante: Avvia → Ferma → Azzera. Le lancette Crono condividono il conteggio. Lua da verificare sul S5.',
            'studioChronoMinute':'Minuti trascorsi del cronografo (0–59). Tap sul sottoquadrante: Avvia → Ferma → Azzera. Esclusa in AOD.',
            'studioChronoSecond':'Secondi trascorsi del cronografo (0–59). Tap sul sottoquadrante: Avvia → Ferma → Azzera. Esclusa in AOD; Movimento Fluido abilita i valori intermedi.'})
        hand_previews={e.id:{hand:preview for hand in ('hour','minute','second') if (preview:=hand_preview(e,hand,resolved))}
                       for e in resolved.elements if e.kind in ('analog','pointer')}
        result=self.project.metadata()
        result.update(variantIndex=self.variant,aod=self.aod,dirty=self.dirty,path=str(self.path or ''),
                      stateSequence=self.state_sequence,
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
                      pointerSources=pointer_sources,sourceDescriptions=source_descriptions,sourceAliases=ALIASES,handPreviews=hand_previews,compassPresets=self.compass_presets,
                      luaSources=lua_sources,
                      aodExcluded=[e.id for e in resolved.elements if e.aod and excluded_from_aod(e)],
                      chronoState=self.chrono_state,motionPreview=self.motion_preview,
                      complicationSources=selectable,
                      scenarios=list(SCENARIOS),
                      maxImageSize=MAX_DESIGN_IMAGE_SIZE,
                      canUndo=bool(self.undo_stack),canRedo=bool(self.redo_stack))
        return result

    def send(self,**values):self.event.emit(json.dumps(values,ensure_ascii=False))

    def preview_tick(self):
        if self.aod:return
        now=time.monotonic_ns()//1000000
        self.values['__clockMs']=now
        self.values['__chronoMs']=now-self.chrono_started if self.chrono_state=='running' else self.chrono_elapsed
        self.values['__secondFraction']=(now-self.motion_started)/1000 if self.motion_preview else 0
        self.send(preview=self.image_url(self.project.variant_project(self.variant)),previewValues=self.values)

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
            user_data_root().mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(dir=user_data_root()) as temp:
                path=Path(temp)/'import.png';image.save(str(path));el=self.project.add_image(path)
            el.name=Path(filename).stem
            return el
        return self.project.add_image(Path(filename))

    @Slot(str,result=str)
    def command(self,raw):
        before=None;selection=None
        try:
            req=json.loads(raw);action=req.get('action')
            mutations={'move-group','align-group','add','edit','nudge','delete','duplicate','move-layer','reorder-layer','fit-image','image','font','hand-image','hand-preset','hand-pivot','compass-preset','compass-image','clear-hand','variant-image','add-variant','edit-variant','delete-variant','add-slot','edit-slot','delete-slot','settings'}
            if action in mutations:
                if self.worker and self.worker.isRunning():raise ValueError('Attendi la fine della compilazione.')
                before=self.project.copy()
                self.project.sync_layer_order()
            if action=='state':pass
            elif action=='chrono-preview':
                now=time.monotonic_ns()//1000000
                if self.chrono_state=='reset':self.chrono_started=now;self.chrono_state='running'
                elif self.chrono_state=='running':self.chrono_elapsed=now-self.chrono_started;self.chrono_state='stopped'
                else:self.chrono_elapsed=0;self.chrono_state='reset'
                self.values['__chronoMs']=now-self.chrono_started if self.chrono_state=='running' else self.chrono_elapsed
                if not self.smoke:
                    if self.motion_preview or self.chrono_state=='running':self.motion_timer.start()
                    else:self.motion_timer.stop()
            elif action=='motion-preview':
                self.motion_preview=bool(req.get('value'));self.motion_started=time.monotonic_ns()//1000000
                self.values['__secondFraction']=0
                if not self.smoke:
                    if self.motion_preview or self.chrono_state=='running':self.motion_timer.start()
                    else:self.motion_timer.stop()
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
                defaults['compass']=dict(name='Bussola analogica',x=180,y=180,width=120,height=120,source='systemSensorCompass',
                                         value_range=360,angle_range=-360,show_ticks=False,show_shadows=False,pointer_end_pivot=False)
                if kind not in defaults:raise ValueError('Componente non supportato.')
                added=Element(kind=kind,aod=self.aod,**defaults[kind]);self.project.elements.append(added);selection=added.id
                if kind=='compass':
                    from .compass_catalog import preset_changes as compass_changes
                    preset=next((c for c in self.compass_presets if c['name']=='Ferrari' and c['kind']=='Rosa completa'),self.compass_presets[0] if self.compass_presets else None)
                    if preset is None:raise ValueError('Catalogo bussole non disponibile.')
                    for k,v in compass_changes(self.project,self.resources,preset).items():setattr(added,k,v)
            elif action=='edit':
                e=self.element(req);changes=req['changes']
                if e.kind in ('analog','pointer'):
                    resolved=next(x for x in self.project.variant_project(0 if self.aod else self.variant).elements if x.id==e.id)
                    changes=hand_edit_changes(resolved,changes,self.project)
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
                    if e.kind in ('analog','pointer'):
                        for variant in self.project.variants:
                            overrides=variant.get('overrides',{}).get(e.id,{})
                            for k in changes:
                                if k.startswith(('hour_','minute_','second_')) or k=='pointer_end_pivot':overrides.pop(k,None)
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
            elif action in ('move-group','align-group'):
                from .selection import move,align
                args=(self.project,req['ids'])
                settings=dict(variant=self.variant,aod=self.aod,variant_only=bool(req.get('variantOnly')))
                if action=='move-group':move(*args,req['dx'],req['dy'],**settings)
                else:align(*args,req['alignment'],**settings)
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
            elif action in ('image','variant-image','hand-image','compass-image'):
                el=self.import_image()
                if el:
                    if action=='image':el.aod=self.aod;selection=el.id
                    else:
                        self.project.elements.remove(el)
                        if action=='variant-image':self.project.variants[self.variant]['imageAsset']=el.asset
                        elif action=='compass-image':
                            if self.element(req).kind!='compass':raise ValueError('Seleziona una bussola.')
                            self.set_compass(req,{'asset':el.asset,'compass_preset':''})
                        else:
                            hand=req['hand']
                            if hand not in ('hour','minute','second'):raise ValueError('Lancetta non valida.')
                            self.set_hand(req,clear_hand_changes(hand,el.asset))
            elif action=='hand-preset':
                preset=next(h for h in self.hand_presets if h['id']==req['preset'])
                self.set_hand(req,preset_changes(self.project,self.element(req),self.resources,preset,req['hand'],self.hand_presets))
            elif action=='hand-pivot':
                e=next(x for x in self.project.variant_project(0 if self.aod else self.variant).elements if x.id==req['id'])
                hand=req['hand']
                if hand not in ('hour','minute','second') or not getattr(e,hand+'_asset') or req.get('asset')!=getattr(e,hand+'_asset'):
                    raise ValueError('Applica la grafica prima di scegliere il suo pivot.')
                if any(type(req.get(a)) is not int or not 0<=req[a]<480 for a in ('x','y')):raise ValueError('Clicca un punto valido nella grafica della lancetta.')
                changes={hand+'_anchor_x':req['x'],hand+'_anchor_y':req['y']}
                self.set_hand(req,hand_edit_changes(e,changes,self.project))
            elif action=='compass-preset':
                from .compass_catalog import preset_changes as compass_changes
                preset=next(c for c in self.compass_presets if c['id']==req['preset'])
                self.set_compass(req,compass_changes(self.project,self.resources,preset))
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
            elif action=='time':
                limits={'hour':23,'minute':59,'second':59,'systemSensorCompass':359}
                changes={key:req[key] for key in limits if key in req}
                if any(type(v) is not int or not 0<=v<=limits[k] for k,v in changes.items()):raise ValueError('Valore di simulazione fuori intervallo.')
                self.values.update(changes)
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

    def set_compass(self,req,changes):
        e=self.element(req)
        if e.kind!='compass':raise ValueError('Seleziona un livello bussola.')
        if req.get('variantOnly') and not self.aod:self.project.variants[self.variant].setdefault('overrides',{}).setdefault(e.id,{}).update({k:v for k,v in changes.items() if k in VARIANT_PROPERTIES})
        else:
            for k,v in changes.items():setattr(e,k,v)
            for variant in self.project.variants:
                overrides=variant.get('overrides',{}).get(e.id,{})
                for key in changes:overrides.pop(key,None)


class MainWindow(QMainWindow):
    def __init__(self,*,smoke=False):
        super().__init__()
        self.setWindowTitle('S5 Studio 0.10 — Xiaomi Watch S5');self.resize(1440,920);self.setMinimumSize(1120,760)
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
            self.bridge.motion_timer.stop()
            if not self.bridge.smoke:self.bridge.recovery.unlink(missing_ok=True)
            event.accept()
        else:event.ignore()


def launch():
    app=QApplication.instance() or QApplication(sys.argv);app.setApplicationName('S5 Studio')
    window=MainWindow();window.show_editor();return app.exec()
