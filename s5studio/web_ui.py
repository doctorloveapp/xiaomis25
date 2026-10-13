"""Offline Tailwind editor hosted in Qt, using the same tested Python build path."""
from dataclasses import asdict
from datetime import date
from calendar import monthrange
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
from .hand_sets import HandSetCatalog,empty_draft,roles_for
from .disk_catalog import DiskCatalog,empty_disk,CATEGORIES
from .paths import application_root,resource_root,user_data_root,default_compiler
from .file_dialogs import RememberedDialogs
from .settings import AppSettings,language_code
from .i18n import install_language,load_catalog
from .moon_disk import SOURCE as MOON_SOURCE,LABEL as MOON_LABEL,defaults as moon_defaults,parse_date as parse_moon_date,preview_value as moon_preview_value,lunar_element


class BuildTask(QThread):
    progress=Signal(str)

    def __init__(self,project,compiler,destination):
        super().__init__()
        self.project=project.copy();self.compiler=compiler;self.destination=destination
        self.output='';self.error=''
        self.ready_at=None

    def run(self):
        try:self.output=str(build(self.project,self.compiler,self.destination,self.progress.emit))
        except Exception as exc:self.error=str(exc)
        finally:self.ready_at=time.perf_counter()


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
        self.project.ensure_independent_variants();self._design=None
        self.path=None;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
        self.dialogs=RememberedDialogs(window,user_data_root()/'dialog-paths.json')
        self.variant=0;self.aod=False;self.scenario='Normale';self.values=dict(SCENARIOS['Normale'])
        self.set_preview_date(self.preview_date())
        self.worker=None;self.output=None;self.smoke=smoke
        self.state_sequence=0
        self.compiler=window.settings.compiler(default_compiler()) if hasattr(window,'settings') else default_compiler()
        self.chrono_state='reset';self.chrono_elapsed=0;self.chrono_started=0;self.motion_preview=False;self.motion_started=0
        from .chrono_pro import ProPreview
        self.pro_preview=ProPreview();self.preview_pro_mode=False
        # Wait after rendering instead of keeping a permanently overdue timer
        # when a large imported bitmap costs more than the frame interval.
        self.motion_timer=QTimer(self);self.motion_timer.setInterval(200);self.motion_timer.setSingleShot(True);self.motion_timer.timeout.connect(self.preview_tick)
        self.hand_set_catalog=HandSetCatalog(user_data_root()/'hand-sets',
                bundled_root=self.resources/'resources/hand-sets',library_hands=library()['hands'],resources=self.resources)
        self.hand_set_draft=empty_draft()
        self.reload_hand_presets()
        self.disk_catalog=DiskCatalog(user_data_root()/'disks',bundled_root=self.resources/'resources/disks')
        self.disk_draft=empty_disk();self.reload_disks()
        from PIL import Image
        self.compass_presets=[]
        for preset in library().get('compasses',[]):
            with Image.open(self.resources/preset['assetPath']) as im:
                im=im.convert('RGBA');im.thumbnail((100,100))
                self.compass_presets.append({**preset,'thumbnail':'data:image/png;base64,'+base64.b64encode(png_bytes(im)).decode()})
        self.recovery=user_data_root()/'recovery-web.s5faceproj'
        self.timer=QTimer(self);self.timer.setInterval(20000);self.timer.timeout.connect(self.autosave)
        if not smoke:self.timer.start()

    def preview_date(self):
        from .complications import SAMPLES
        return date(self.values.get('dateYear',SAMPLES['dateYear']),self.values.get('month',1),self.values.get('day',1))

    @Slot(result=str)
    def get_language(self):
        return getattr(self.window,'language','it')

    @Slot(str,result=str)
    def locale(self,language):
        return json.dumps(load_catalog(language),ensure_ascii=False)

    def set_preview_date(self,value):
        self.values.update(day=value.day,month=value.month,dateYear=value.year,__moonDate=value.isoformat())

    def reload_hand_presets(self):
        self.hand_presets=[]
        from PIL import Image
        from io import BytesIO
        from .catalog_labels import display_preset
        for preset in self.hand_set_catalog.presets():
            preset=display_preset(preset)
            path=self.hand_set_catalog.bitmap_path(preset) if preset.get('custom') else self.resources/preset['assetPath']
            if not path.is_file():continue
            with Image.open(path) as im:
                im=im.convert('RGBA')
                # Gallery-only crop: the imported bitmap and its pivot stay intact.
                bounds=im.getchannel('A').getbbox()
                if bounds:im=im.crop(bounds)
                im.thumbnail((96,110));out=BytesIO();im.save(out,format='PNG')
            self.hand_presets.append({**preset,'thumbnail':'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()})

    def image_url(self,p,aod=False,*,values=None):
        return 'data:image/png;base64,'+base64.b64encode(png_bytes(render(p,self.values if values is None else values,aod))).decode()

    def reload_disks(self):
        from PIL import Image
        self.disk_presets=[]
        for summary in self.disk_catalog.summaries():
            record=self.disk_catalog.draft(summary['id']);item=next(iter(record['hands'].values()))
            with Image.open(self.disk_catalog.bitmap_path(item)) as im:
                im=im.convert('RGBA');im.thumbnail((110,110))
                thumbnail='data:image/png;base64,'+base64.b64encode(png_bytes(im)).decode()
            self.disk_presets.append({**summary,'thumbnail':thumbnail,'categoryLabel':CATEGORIES[summary['category']]})

    def state(self):
        self.state_sequence+=1
        from .complications import ALIASES
        # Lossless migration of old Studio aliases to the observed source names:
        # both keys have the same native code, but should appear only once.
        for s in self.design.complications:
            s['options']=list(dict.fromkeys(ALIASES.get(k,k) for k in s['options']))
            s['default']=ALIASES.get(s['default'],s['default'])
        selectable={'none':'Nessuna',**{k:v[0] for k,v in SOURCES.items() if k not in ALIASES}}
        resolved=self.project.variant_project(0 if self.aod else self.variant)
        self.update_pro_preview()
        from .source_help import source_choices
        pointer_sources,source_descriptions=source_choices(SOURCES)
        disk_sources={MOON_SOURCE:MOON_LABEL,**pointer_sources,'dateMoon':'Fasi lunari native · 8 stati'}
        source_descriptions[MOON_SOURCE]='Disco a due lune: una posizione al giorno su 59, indipendente dal cronografo. La data di riferimento rappresenta la luna piena con la luna in alto; puoi correggere giorni, angolo iniziale e verso.'
        from .motion import ALL_LUA_SOURCES
        from .motion import excluded_from_aod
        lua_sources={k:v[0] for k,v in ALL_LUA_SOURCES.items()}
        source_descriptions.update({
            'studioDecisecond':'Animazione continua indipendente: un giro al secondo, da 0 a 9. Non misura il tempo del cronografo e non segue Avvio, Stop o Reset, anche con Crono Pro attivo. Scala consigliata 0/10 e rotazione 360°. Per misurare il tempo trascorso scegli Decimi crono · Start/Stop/Reset. Esclusa in AOD.',
            'studioChronoHour':'Ore trascorse su 12 ore; conteggio condiviso. Crono separato 1.0 già collaudato: Avvia → Ferma → Azzera. Con Crono Pro: Prepara → Avvia → Ferma → Rientro. Primo test Pro 1.1 superato; rientri sempre orari nella 1.2.',
            'studioChronoMinute':'Minuti trascorsi del cronografo (0–59). Tap sul quadrante: Avvia → Ferma → Azzera. Esclusa in AOD.',
            'studioChronoSecond':'Secondi trascorsi del cronografo (0–59). Crono normale: Avvia → Ferma → Azzera. Crono Pro: Prepara → Avvia → Ferma → Rientro; conteggio a scatti. Esclusa in AOD.',
            'studioChronoDecisecond':'Decimi del tempo misurato dal cronografo: a zero a riposo, dieci scatti al secondo oppure rotazione fluida con target 25 fps se attivi Movimento Fluido in questa scheda. Fermi sullo stesso istante di Stop dei POST e azzerati al Reset con rientro fluido. Richiede il flag generale Crono Pro della lancetta grande secondi nello stesso stile; i secondi grandi restano a scatti durante il conteggio. Nascondere il gruppo grande non disattiva Crono Pro. Esclusa in AOD.'})
        hand_previews={e.id:{hand:preview for hand in ('hour','minute','second') if (preview:=hand_preview(e,hand,resolved))}
                       for e in resolved.elements if e.kind in ('analog','pointer')}
        disk_previews={}
        from PIL import Image
        from io import BytesIO
        for e in resolved.elements:
            if e.kind!='disk' or e.asset not in resolved.assets:continue
            raw=resolved.assets[e.asset]
            with Image.open(BytesIO(raw)) as im:size=list(im.size)
            disk_previews[e.id]={'src':'data:image/png;base64,'+base64.b64encode(raw).decode(),'size':size}
        from .source_help import DESCRIPTIONS
        source_descriptions['timeHour24']=DESCRIPTIONS['timeHour24']
        source_descriptions.update({
            'studioChronoCentisecond':'Lettura POST del Crono Pro: frazione del secondo da 00 a 99, oppure sola cifra dei centesimi da 0 a 9. Resta a zero durante il conteggio e raggiunge il valore acquisito allo Stop con animazione da 720 ms a 25 fps. La risoluzione reale dipende dal clock disponibile sul firmware. Esclusa in AOD.',
            'studioChronoMillisecond':'Lettura POST del Crono Pro: frazione del secondo da 000 a 999, oppure sola cifra dei millesimi da 0 a 9. Stesso istante di Stop per tutte le lancette; nessun aggiornamento rapido durante Running. La fase Anim del firmware non garantisce precisione di 1 ms. Esclusa in AOD.'})
        result=self.project.metadata()
        result.update(language=self.get_language(),variantIndex=self.variant,aod=self.aod,dirty=self.dirty,path=str(self.path or ''),
                      background=resolved.background,
                      stateSequence=self.state_sequence,
                      preview=self.image_url(resolved,self.aod),
                      thumbnails=[self.image_url(self.project.variant_project(i),values=SCENARIOS['Normale']) for i in range(len(self.project.variants))],
                      resolvedElements=[asdict(e) for e in resolved.elements],
                      layers=[asdict(e) if isinstance(e,Element) else {**e,'kind':'complication','aod':False}
                              for mode in (False,True) for e in resolved.ordered_layers(mode)],
                      errors=self.project.validate()+layout_errors(resolved),
                      busy=bool(self.worker and self.worker.isRunning()),output=str(self.output or ''),
                      sources={key:label for key,(label,_,_) in SOURCES.items()},scenario=self.scenario,values=self.values,
                      complications=[normalized_slot(s) for s in resolved.complications],maxSlots=MAX_SLOTS,handPresets=self.hand_presets,
                      handSets=self.hand_set_catalog.summaries(),
                      handSetDraft=self.hand_set_catalog.public_draft(self.hand_set_draft),
                      diskPresets=self.disk_presets,diskDraft=self.disk_catalog.public_draft(self.disk_draft),diskCategories=CATEGORIES,diskPreviews=disk_previews,
                      deletedDisks=self.disk_catalog.deleted_bundled(),
                      diskSources=disk_sources,moonSource=MOON_SOURCE,
                      moonPreviewDate=self.values.get('__moonDate') or date.today().isoformat(),
                      moonPositions={e.id:moon_preview_value(e,self.values) for e in resolved.elements if lunar_element(e)},
                      independentVariants=True,
                      pointerSources=pointer_sources,sourceDescriptions=source_descriptions,sourceAliases=ALIASES,handPreviews=hand_previews,compassPresets=self.compass_presets,
                      luaSources=lua_sources,
                      aodExcluded=[e.id for e in resolved.elements if e.aod and excluded_from_aod(e)],
                      chronoState=self.chrono_state,chronoElapsedMs=self.chrono_elapsed,chronoPro=self.preview_pro_mode,motionPreview=self.motion_preview,
                      complicationSources=selectable,
                      scenarios=list(SCENARIOS),
                      maxImageSize=MAX_DESIGN_IMAGE_SIZE,
                      canUndo=bool(self.undo_stack),canRedo=bool(self.redo_stack))
        return result

    def send(self,**values):self.event.emit(json.dumps(values,ensure_ascii=False))

    def preview_tick(self):
        if self.aod or self.worker:return
        now=time.monotonic_ns()//1000000
        self.values['__clockMs']=now
        self.values['__chronoMs']=now-self.chrono_started if self.chrono_state=='running' else self.chrono_elapsed
        self.values['__secondFraction']=(now-self.motion_started)/1000 if self.motion_preview else 0
        self.update_pro_preview(now)
        self.send(preview=self.image_url(self.project.variant_project(self.variant)),previewValues=self.values,chronoState=self.chrono_state,chronoElapsedMs=self.chrono_elapsed,previewSequence=self.state_sequence)
        self.resume_preview()

    def resume_preview(self):
        if not self.smoke and not self.worker and not self.aod and (self.motion_preview or self.chrono_state in ('running','arming','reading','resetting')):
            self.motion_timer.start()

    def update_pro_preview(self,now=None):
        from .motion import pro_enabled
        from .chrono_pro import ProPreview
        resolved=self.project.variant_project(self.variant);mode=pro_enabled(resolved)
        if mode!=self.preview_pro_mode:
            self.pro_preview=ProPreview();self.chrono_state='rest' if mode else 'reset'
            self.chrono_elapsed=0;self.preview_pro_mode=mode
        if mode:
            if self.aod:self.pro_preview.aod()
            now=now if now is not None else time.monotonic_ns()//1000000
            civil=((self.values.get('second') or 0)+self.values.get('__secondFraction',0))%60
            self.values['__proValues']=self.pro_preview.values(resolved,now,civil)
            self.chrono_state=self.pro_preview.state;self.chrono_elapsed=self.pro_preview.elapsed
            deciseconds=[e for e in resolved.elements if e.visible and not e.aod and e.source=='studioChronoDecisecond']
            self.motion_timer.setInterval(40 if self.pro_preview.transition or self.chrono_state=='running' and any(e.smooth_seconds for e in deciseconds) else 100 if deciseconds else 200)
        else:self.values.pop('__proValues',None);self.motion_timer.setInterval(200)

    def autosave(self):
        if self.dirty and not self.project.validate():
            try:self.project.save(self.recovery)
            except Exception:pass

    def offer_recovery(self):
        if self.smoke or not self.recovery.exists():return
        if QMessageBox.question(self.window,self.tr('Recupero progetto'),self.tr('Riprendere il progetto recuperato dopo la chiusura precedente?'))==QMessageBox.StandardButton.Yes:
            try:self.project=Project.load(self.recovery);self.dirty=True;self.send(state=self.state())
            except Exception as exc:self.send(error=str(exc))

    def confirm_leave(self):
        if self.smoke:return True
        if not self.dirty:return True
        answer=QMessageBox.question(self.window,self.tr('Progetto modificato'),self.tr('Salvare le modifiche al progetto?'),
                                    QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel)
        if answer==QMessageBox.StandardButton.Cancel:return False
        if answer==QMessageBox.StandardButton.Save:return self.save()
        return True

    def save(self):
        suggested=self.path or self.root/'projects/Il_mio_S5.s5faceproj'
        filename=self.dialogs.save('project-save',self.tr('Salva progetto'),suggested,self.tr('Progetti S5 (*.s5faceproj)'))
        if not filename:return False
        path=Path(filename)
        if path.suffix.lower()!='.s5faceproj':path=path.with_suffix('.s5faceproj')
        self.project.save(path,png_bytes(render(self.project.variant_project(self.variant))))
        self.path=path;self.dirty=False
        if not self.smoke:self.recovery.unlink(missing_ok=True)
        return True

    @property
    def design(self):
        return self._design if self._design is not None else self.project.editable_variant(self.variant,self.aod)

    def element(self,req):
        return next(e for e in self.design.elements if e.id==req['id'])

    def layer(self,key):
        for e in self.design.elements:
            if e.id==key:return e
        for slot in self.design.complications:
            if slot['id']==key:return slot
        raise ValueError(self.tr('Livello non trovato.'))

    def remove_layer(self,key):
        layer=self.layer(key)
        if isinstance(layer,Element):
            self.design.elements.remove(layer)
        else:self.design.complications.remove(layer)
        self.design.layer_order=[k for k in self.design.layer_order if k!=key]

    def reorder_layer(self,key,target,placement):
        if key==target:return
        source=self.layer(key);other=self.layer(target)
        source_aod=source.aod if isinstance(source,Element) else False
        other_aod=other.aod if isinstance(other,Element) else False
        if source_aod!=other_aod:raise ValueError(self.tr('Riordina i livelli nella stessa schermata.'))
        if placement not in ('above','below'):raise ValueError(self.tr('Posizione di riordino non valida.'))
        order=self.design.layer_order
        order.remove(key);position=order.index(target)+(placement=='above')
        order.insert(position,key)

    def import_image(self,category='image-open'):
        filename=self.dialogs.open(category,self.tr('Importa immagine'),self.root,self.tr('Immagini (*.png *.jpg *.jpeg *.webp *.bmp *.svg)'))
        if not filename:return None
        if Path(filename).suffix.lower()=='.svg':
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtGui import QImage,QPainter
            import tempfile
            svg=QSvgRenderer(filename)
            if not svg.isValid():raise ValueError(self.tr('SVG non valido.'))
            size=svg.defaultSize();size.scale(1920,1920,Qt.AspectRatioMode.KeepAspectRatio)
            image=QImage(size,QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.transparent)
            painter=QPainter(image);svg.render(painter);painter.end()
            user_data_root().mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(dir=user_data_root()) as temp:
                path=Path(temp)/'import.png';image.save(str(path));el=self.design.add_image(path)
            el.name=Path(filename).stem
            return el
        return self.design.add_image(Path(filename))

    @Slot(str,result=str)
    def command(self,raw):
        before=None;selection=None;self._design=None
        try:
            req=json.loads(raw);action=req.get('action')
            if action=='choose-color':
                if self.worker and self.worker.isRunning():raise ValueError(self.tr('Attendi la fine della compilazione.'))
                from .color_picker import choose_graphic_color
                context=req.get('context','layer')
                if context=='project':target={'background':self.design.background};edit_action='settings'
                elif context=='variant':target=self.project.variants[self.variant];edit_action='edit-variant'
                elif context=='layer':
                    target=self.layer(req['id']);edit_action='edit-slot' if isinstance(target,dict) else 'edit'
                else:raise ValueError(self.tr('Contesto colore non valido.'))
                changes=choose_graphic_color(target,req['key'],self.window)
                action='state' if changes is None else edit_action
                if changes is not None:req['changes']=changes
            mutations={'disk-preset','set-shape','move-group','align-group','add','edit','nudge','delete','duplicate','move-layer','reorder-layer','fit-image','image','font','hand-image','hand-preset','hand-pivot','compass-preset','compass-image','clear-hand','variant-image','add-variant','edit-variant','delete-variant','add-slot','edit-slot','delete-slot','settings'}
            if action in mutations:
                if self.worker and self.worker.isRunning():raise ValueError(self.tr('Attendi la fine della compilazione.'))
                self.project.ensure_independent_variants()
                before=self.project.copy()
                if action in ('variant-image','add-variant','edit-variant','delete-variant'):self.aod=False
                self._design=self.project.editable_variant(self.variant,self.aod)
                self.design.sync_layer_order()
            if action=='state':pass
            elif action=='language':
                self.window.set_language(req.get('language'))
            elif action.startswith('hand-set-'):
                self.hand_set_command(action,req)
            elif action.startswith('disk-catalog-'):
                self.disk_command(action,req)
            elif action=='disk-preset':
                e=self.element(req)
                if e.kind!='disk':raise ValueError(self.tr('Seleziona un livello Disco.'))
                for k,v in self.disk_catalog.changes(self.design,req['preset']).items():setattr(e,k,v)
            elif action=='chrono-preview':
                self.values.pop('__pointerCalibration',None)
                now=time.monotonic_ns()//1000000
                self.update_pro_preview(now)
                if self.preview_pro_mode:
                    civil=((self.values.get('second') or 0)+self.values.get('__secondFraction',0))%60
                    self.pro_preview.tap(self.project.variant_project(self.variant),now,civil)
                    self.update_pro_preview(now)
                elif self.chrono_state=='reset':self.chrono_started=now;self.chrono_state='running'
                elif self.chrono_state=='running':self.chrono_elapsed=now-self.chrono_started;self.chrono_state='stopped'
                else:self.chrono_elapsed=0;self.chrono_state='reset'
                self.values['__chronoMs']=self.chrono_elapsed if self.preview_pro_mode else now-self.chrono_started if self.chrono_state=='running' else self.chrono_elapsed
                if not self.smoke:
                    if self.motion_preview or self.chrono_state in ('running','arming','reading','resetting'):self.motion_timer.start()
                    else:self.motion_timer.stop()
            elif action=='pointer-calibration':
                element=self.element(req)
                if element.kind!='pointer' or req['pose'] not in ('start','end','live'):
                    raise ValueError(self.tr('Posizione di calibrazione non valida.'))
                poses=self.values.setdefault('__pointerCalibration',{})
                if req['pose']=='live':poses.pop(element.id,None)
                else:poses[element.id]=req['pose']
            elif action=='moon-preview':
                value=req.get('date','')
                self.set_preview_date(parse_moon_date(value) if value else date.today())
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
                    filename=self.dialogs.open('project-open',self.tr('Apri progetto'),self.root/'projects',self.tr('Progetti S5 (*.s5faceproj)'))
                    if filename:
                        self.project=Project.load(Path(filename));self.path=Path(filename);self.variant=0;self.dirty=False;self.undo_stack=[];self.redo_stack=[]
                        if not self.smoke:self.recovery.unlink(missing_ok=True)
            elif action in ('save','save-as'):
                self.save()
            elif action=='undo' and self.undo_stack:
                self.redo_stack.append(self.project.copy());self.project=self.undo_stack.pop();self.variant=min(self.variant,len(self.project.variants)-1);self.dirty=True
            elif action=='redo' and self.redo_stack:
                self.undo_stack.append(self.project.copy());self.project=self.redo_stack.pop();self.variant=min(self.variant,len(self.project.variants)-1);self.dirty=True
            elif action=='add':
                kind=req['kind']
                defaults={'clock':dict(name='Ora',x=57,y=144,width=366,height=108,size=90),'date':dict(name='Data',x=158,y=258,width=164,height=40,size=30),'analog':dict(name='Lancette',x=60,y=60,width=360,height=360,color='#6ce5c1',second_hand=not self.aod),'number':dict(name='Dato',x=166,y=340,width=148,height=46,size=30),'text':dict(name='Testo',x=140,y=100,width=200,height=40,size=24),'rect':dict(name='Rettangolo'),'circle':dict(name='Cerchio')}
                defaults['pointer']=dict(name='Lancetta piccola',x=180,y=180,width=120,height=120,source='second',color='#f7be69',show_ticks=False)
                defaults['disk']=dict(name='Disco',x=150,y=150,width=180,height=180,source='timeHour',value_range=24,angle_range=360,show_ticks=False,show_shadows=False,pointer_end_pivot=False)
                defaults['compass']=dict(name='Bussola analogica',x=180,y=180,width=120,height=120,source='systemSensorCompass',
                                         value_range=360,angle_range=-360,show_ticks=False,show_shadows=False,pointer_end_pivot=False)
                if kind not in defaults:raise ValueError(self.tr('Componente non supportato.'))
                added=Element(kind=kind,aod=self.aod,**defaults[kind]);self.design.elements.append(added);selection=added.id
                if kind=='disk':
                    preset=req.get('preset') or next((p['id'] for p in self.disk_presets if p['category']=='celestial'),self.disk_presets[0]['id'] if self.disk_presets else '')
                    if not preset:raise ValueError(self.tr('Catalogo dischi non disponibile.'))
                    for k,v in self.disk_catalog.changes(self.design,preset).items():setattr(added,k,v)
                if kind=='compass':
                    from .compass_catalog import preset_changes as compass_changes
                    preset=next((c for c in self.compass_presets if c['name']=='Ferrari' and c['kind']=='Rosa completa'),self.compass_presets[0] if self.compass_presets else None)
                    if preset is None:raise ValueError(self.tr('Catalogo bussole non disponibile.'))
                    for k,v in compass_changes(self.design,self.resources,preset).items():setattr(added,k,v)
            elif action=='set-shape':
                e=self.element(req);kind=req.get('kind')
                if e.kind not in ('rect','circle') or kind not in ('rect','circle'):raise ValueError(self.tr('Scegli una forma rettangolare o circolare.'))
                e.kind=kind
            elif action=='edit':
                e=self.element(req);changes=req['changes']
                if e.kind=='disk' and 'source' in changes and changes['source']!=e.source:
                    changes={**moon_defaults(changes['source']),**changes}
                if e.kind=='disk' and e.second_shadow_asset:
                    for axis in ('x','y'):
                        key='second_anchor_'+axis
                        if key in changes:changes['second_shadow_anchor_'+axis]=getattr(e,'second_shadow_anchor_'+axis)+changes[key]-getattr(e,key)
                if e.kind in ('analog','pointer'):
                    changes=hand_edit_changes(e,changes,self.design)
                allowed=set(Element.__dataclass_fields__)-{'id','kind'}
                if set(changes)-allowed:raise ValueError(self.tr('Proprietà non supportata.'))
                for k,v in changes.items():setattr(e,k,v)
                if {'source','month_abbreviated'} & set(changes):
                    from .calendar_labels import labels_for
                    if labels_for(e):
                        from .render import calendar_metrics
                        width,height=calendar_metrics(self.design,e)
                        e.width=min(480,max(e.width,width));e.height=min(480,max(e.height,height))
                        e.x=min(e.x,480-e.width);e.y=min(e.y,480-e.height)
            elif action=='nudge':
                layer=self.layer(req['id']);dx=req.get('dx',0);dy=req.get('dy',0)
                if type(dx) is not int or type(dy) is not int or abs(dx)>100 or abs(dy)>100:raise ValueError(self.tr('Spostamento non valido.'))
                if isinstance(layer,Element):
                    resolved=layer
                    if not layer.locked:
                        low=-MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else 0
                        xmax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-resolved.width)
                        ymax=MAX_DESIGN_IMAGE_SIZE if layer.kind=='image' else max(0,480-resolved.height)
                        changes={'x':max(low,min(xmax,resolved.x+dx)),'y':max(low,min(ymax,resolved.y+dy))}
                        for k,v in changes.items():setattr(layer,k,v)
                    else:self.project=before;before=None
                else:
                    layer=normalized_slot(layer)
                    if not layer['locked']:
                        self.layer(req['id']).update(x=max(0,min(480-layer['width'],layer['x']+dx)),y=max(0,min(480-layer['height'],layer['y']+dy)))
                    else:self.project=before;before=None
            elif action in ('move-group','align-group'):
                from .selection import move,align
                args=(self.design.copy() if self.design is self.project else self.design,req['ids'])
                if self.design is self.project:args[0].variants=[]
                settings=dict(aod=self.aod)
                if action=='move-group':move(*args,req['dx'],req['dy'],**settings)
                else:align(*args,req['alignment'],**settings)
                # Group transforms operate on the selected design only.
                self.design.elements=args[0].elements;self.design.complications=args[0].complications
            elif action=='delete':
                self.remove_layer(req['id']);selection=''
            elif action=='duplicate':
                from copy import deepcopy
                original=self.layer(req['id']);e=deepcopy(original)
                if isinstance(e,Element):e.id=identifier();e.name+=' copia';self.design.elements.append(e);selection=e.id
                else:
                    if len(self.design.complications)>=MAX_SLOTS:raise ValueError(self.tr('Limite Studio: {v0} slot.').format(v0=MAX_SLOTS))
                    e['id']=identifier();e['name']+=' copia';self.design.complications.append(e);selection=e['id']
                self.design.sync_layer_order();self.reorder_layer(selection,req['id'],'above')
            elif action=='move-layer':
                e=self.layer(req['id']);mode=e.aod if isinstance(e,Element) else False
                order=[x.id if isinstance(x,Element) else x['id'] for x in self.design.ordered_layers(mode)]
                index=order.index(req['id']);direction=1 if int(req['direction'])>0 else -1
                if 0<=index+direction<len(order):self.reorder_layer(req['id'],order[index+direction],'above' if direction>0 else 'below')
            elif action=='reorder-layer':self.reorder_layer(req['id'],req['targetId'],req['placement'])
            elif action=='fit-image':
                e=self.element(req)
                if e.kind!='image' or req.get('fit','cover') not in ('cover','contain'):raise ValueError(self.tr('Seleziona un livello immagine.'))
                changes={'x':0,'y':0,'width':480,'height':480,'fit':req.get('fit','cover')}
                for k,v in changes.items():setattr(e,k,v)
            elif action in ('image','variant-image','hand-image','compass-image'):
                category={'hand-image':'hand-image-open','compass-image':'compass-image-open'}.get(action,'image-open')
                el=self.import_image(category)
                if el:
                    if action=='image':el.aod=self.aod;selection=el.id
                    else:
                        self.design.elements.remove(el)
                        if action=='variant-image':self.set_background_image(el)
                        elif action=='compass-image':
                            if self.element(req).kind!='compass':raise ValueError(self.tr('Seleziona una bussola.'))
                            self.set_compass(req,{'asset':el.asset,'compass_preset':''})
                        else:
                            hand=req['hand']
                            if hand not in ('hour','minute','second'):raise ValueError(self.tr('Lancetta non valida.'))
                            self.set_hand(req,clear_hand_changes(hand,el.asset))
            elif action=='hand-preset':
                preset=next(h for h in self.hand_presets if h['id']==req['preset'])
                self.set_hand(req,preset_changes(self.design,self.element(req),self.resources,preset,req['hand'],self.hand_presets,custom_catalog=self.hand_set_catalog))
            elif action=='hand-pivot':
                e=self.element(req)
                hand=req['hand']
                if hand not in ('hour','minute','second') or not getattr(e,hand+'_asset') or req.get('asset')!=getattr(e,hand+'_asset'):
                    raise ValueError(self.tr('Applica la grafica prima di scegliere il suo pivot.'))
                if any(type(req.get(a)) is not int or not 0<=req[a]<480 for a in ('x','y')):raise ValueError(self.tr('Clicca un punto valido nella grafica della lancetta.'))
                changes={hand+'_anchor_x':req['x'],hand+'_anchor_y':req['y']}
                self.set_hand(req,hand_edit_changes(e,changes,self.design))
            elif action=='compass-preset':
                from .compass_catalog import preset_changes as compass_changes
                preset=next(c for c in self.compass_presets if c['id']==req['preset'])
                self.set_compass(req,compass_changes(self.design,self.resources,preset))
            elif action=='clear-hand':
                self.set_hand(req,clear_hand_changes(req['hand']))
            elif action=='font':
                filename=self.dialogs.open('font-open',self.tr('Importa font'),self.root,self.tr('Font (*.ttf *.otf)'))
                if filename:self.element(req).font_asset=self.design.add_font(Path(filename))
            elif action=='add-variant':
                self.variant=self.project.add_variant(self.variant);self.aod=False;selection=''
            elif action=='edit-variant':
                allowed={'name','accent','background','imageAsset'}
                if set(req['changes'])-allowed:raise ValueError(self.tr('Proprietà variante non valida.'))
                changes=dict(req['changes']);variant=self.project.variants[self.variant]
                if changes.get('accent'):
                    old=variant.get('accent','#6ce5c1')
                    for element in self.design.elements:
                        if not element.aod and element.color.lower()==old.lower():element.color=changes['accent']
                    for slot in self.design.complications:
                        if slot['color'].lower()==old.lower():slot['color']=changes['accent']
                if 'background' in changes:self.design.background=changes['background'] or '#080f1b'
                if 'imageAsset' in changes:
                    asset=changes.pop('imageAsset')
                    if asset:
                        if asset not in self.project.assets:raise ValueError(self.tr('Sfondo variante mancante.'))
                        self.set_background_image(Element(kind='image',asset=asset))
                    else:
                        background=self.background_layer()
                        variant.pop('backgroundLayerId',None)
                        if background:self.remove_layer(background.id)
                variant.update(changes)
            elif action=='delete-variant':
                self.project.delete_variant(self.variant);self.variant=0;self.aod=False;selection=''
            elif action=='select-variant':
                self.variant=max(0,min(int(req['index']),len(self.project.variants)-1));self.aod=False;selection=''
                from .chrono_pro import ProPreview
                self.pro_preview=ProPreview();self.chrono_state='rest' if self.preview_pro_mode else 'reset'
                self.chrono_elapsed=0;self.values.pop('__proValues',None);self.values.pop('__choices',None);self.values.pop('__pointerCalibration',None)
            elif action=='add-slot':
                if len(self.design.complications)>=MAX_SLOTS:raise ValueError(self.tr('Limite Studio: {v0} slot.').format(v0=MAX_SLOTS))
                n=len(self.design.complications)
                x,y=[(90,112),(280,112),(28,228),(342,228),(185,332)][n%5]
                slot=normalized_slot({'id':identifier(),'name':f'Complicazione {n+1}','x':x,'y':y,'width':110,'height':44,'size':32,
                                      'frame':'none','showLabel':False,'showUnit':False,'weatherMode':'value',
                                      'options':['none','steps','heartRate','weatherCurrentTemperature','systemSensorCompass','weatherCurrentWeather'],
                                      'default':['steps','heartRate','weatherCurrentTemperature','systemSensorCompass','weatherCurrentWeather'][n%5]})
                self.design.complications.append(slot);selection=slot['id']
            elif action=='edit-slot':
                slot=next(s for s in self.design.complications if s['id']==req['id'])
                if set(req['changes'])-{'name','x','y','width','height','size','decimals','digits','unit','color','background','frame','showLabel','showUnit','weatherMode','visible','locked','opacity','align','options','default'}:raise ValueError(self.tr('Proprietà slot non valida.'))
                slot.update(req['changes'])
            elif action=='slot-preview':
                slot=next(s for s in self.design.complications if s['id']==req['id'])
                if req['choice'] not in slot['options']:raise ValueError(self.tr('Opzione non disponibile.'))
                self.values.setdefault('__choices',{})[slot['id']]=req['choice']
            elif action=='delete-slot':self.remove_layer(req['id']);selection=''
            elif action=='settings':
                mapping={'name':'name','author':'author','version':'version','background':'background','aodEnabled':'aod_enabled','faceId':'face_id'}
                for key,value in req['changes'].items():
                    if key not in mapping:raise ValueError(self.tr('Impostazione non valida.'))
                    setattr(self.design if key=='background' else self.project,mapping[key],value)
                if self.project.aod_enabled and not any(e.aod and e.kind in ('clock','analog') for e in self.project.elements):
                    self.project.elements.append(Element(kind='analog',name='Lancette AOD',x=80,y=80,width=320,height=320,color='#808080',aod=True))
            elif action=='aod':self.aod=bool(req['value']) and self.project.aod_enabled
            elif action=='scenario':
                self.scenario=req['value'];self.values=dict(SCENARIOS[self.scenario])
                self.set_preview_date(self.preview_date())
                self.motion_started=time.monotonic_ns()//1000000
                self.values['__secondFraction']=0
            elif action=='time':
                limits={'hour':(0,23),'minute':(0,59),'second':(0,59),'systemSensorCompass':(0,359),
                        'day':(1,31),'month':(1,12),'dateYear':(1900,2399)}
                changes={key:req[key] for key in limits if key in req}
                if any(type(v) is not int or not limits[k][0]<=v<=limits[k][1] for k,v in changes.items()):raise ValueError(self.tr('Valore di simulazione fuori intervallo.'))
                calendar_date=None
                if {'day','month','dateYear'} & changes.keys():
                    current=self.preview_date();year=changes.get('dateYear',current.year);month=changes.get('month',current.month)
                    day=changes.get('day',min(current.day,monthrange(year,month)[1]))
                    try:calendar_date=date(year,month,day)
                    except ValueError:raise ValueError(self.tr('Il giorno non esiste nel mese e anno simulati. Scegli una data valida.')) from None
                self.values.update(changes)
                if calendar_date:self.set_preview_date(calendar_date)
                if 'second' in changes:
                    # A manual second is an exact new civil-time origin, even
                    # while motion is running; never add the old elapsed phase.
                    self.motion_started=time.monotonic_ns()//1000000
                    self.values['__secondFraction']=0
            elif action=='compiler':
                filename=self.dialogs.open('compiler-open',self.tr('Seleziona EasyFace 4.23'),self.compiler.parent,self.tr('Compilatore (Compiler.exe)'))
                if filename:
                    self.compiler=Path(filename)
                    self.window.settings.update(compiler=str(self.compiler))
            elif action=='build':
                if self.worker and self.worker.isRunning():raise ValueError(self.tr('Compilazione già in corso.'))
                destination=self.dialogs.directory('watchface-export',self.tr('Cartella di esportazione'),self.root/'dist')
                if destination:
                    self.motion_timer.stop()
                    self.worker=BuildTask(self.project,self.compiler,Path(destination))
                    self.worker.progress.connect(lambda message:self.send(progress=message))
                    self.worker.finished.connect(self.build_finished);self.worker.start()
            elif action=='show-output' and self.output:QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output)))
            elif action=='export-preview':
                filename=self.dialogs.save('preview-save',self.tr('Salva anteprima'),self.root/'preview.png',self.tr('PNG (*.png)'))
                if filename:Path(filename).write_bytes(png_bytes(render(self.project.variant_project(0 if self.aod else self.variant),self.values,self.aod)))
            if before:
                if action not in ('add-variant','delete-variant'):
                    self.design.sync_layer_order();self.project.commit_variant(self.variant,self.design,self.aod)
                self.project.sync_layer_order()
                errors=self.project.validate()
                if errors:raise ValueError('\n'.join(errors))
                if self.project.metadata()!=before.metadata():
                    self.undo_stack.append(before);self.undo_stack=self.undo_stack[-40:];self.redo_stack=[];self.dirty=True
            self._design=None
            reply={'state':self.state()}
            self.resume_preview()
            if selection is not None:reply['selectedLayer']=selection
            return json.dumps(reply,ensure_ascii=False)
        except Exception as exc:
            if before:self.project=before;self.variant=min(self.variant,len(self.project.variants)-1)
            self._design=None
            return json.dumps({'error':str(exc)},ensure_ascii=False)

    @Slot()
    def build_finished(self):
        task=self.worker
        if task is None:return
        self.worker=None
        self.build_complete(task.output,task.error)
        if task.output and task.ready_at is not None:
            # File-based evidence distinguishes worker time from a delayed GUI
            # notification on the user's PC. No project or archive is changed.
            try:
                path=Path(task.output)/'build-report.json'
                report=json.loads(path.read_text(encoding='utf8'))
                report.setdefault('exportTiming',{})['guiNotificationDelaySeconds']=round(time.perf_counter()-task.ready_at,3)
                path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
            except (OSError,ValueError):pass
        task.deleteLater()
        self.resume_preview()

    def build_complete(self,path,error):
        if path:self.output=Path(path)
        self.state_sequence+=1
        # No expensive preview rendering or gallery serialization is needed to
        # mark the export complete. This version also invalidates stale replies.
        self.send(buildStatus={'stateSequence':self.state_sequence,'busy':False,'output':str(self.output or '')},
                  error=error,progress='ZIP pronto: '+path if path else 'Compilazione interrotta.',buildDone=bool(path))

    def hand_set_command(self,action,req):
        from copy import deepcopy
        draft=deepcopy(self.hand_set_draft)
        if action=='hand-set-new':draft=empty_draft()
        elif action=='hand-set-load':draft=self.hand_set_catalog.draft(req['id'])
        elif action=='hand-set-meta':
            changes=req['changes']
            if set(changes)-{'name','small','generateShadows','shadowOptions'}:raise ValueError(self.tr('Proprietà del set non valida.'))
            if 'name' in changes and (not isinstance(changes['name'],str) or len(changes['name'])>80):raise ValueError(self.tr('Nome del set troppo lungo.'))
            if 'small' in changes and type(changes['small']) is not bool:raise ValueError(self.tr('Tipo del set non valido.'))
            if changes.get('small') is False and set(draft['hands'])-set(roles_for(False)):
                raise ValueError(self.tr('Decimi, Centesimi e Millesimi appartengono ai set piccoli. Rimuovi queste grafiche prima di passare a un set principale.'))
            draft.update(changes)
        elif action in ('hand-set-image','hand-set-part','hand-set-remove'):
            role=req['role'];shadow=bool(req.get('shadow'))
            if role not in roles_for(draft['small']):raise ValueError(self.tr('Lancetta del set non valida per questo tipo di set.'))
            if shadow and role not in draft['hands']:raise ValueError(self.tr('Importa prima la lancetta, poi la sua ombra.'))
            if action=='hand-set-image':
                filename=self.dialogs.open('hand-set-shadow-open' if shadow else 'hand-set-image-open',
                        ((self.tr('Importa PNG ') + role) + ' — ombra' if shadow else ''),self.root,self.tr('Lancette PNG (*.png)'))
                if filename:
                    item=self.hand_set_catalog.stage(Path(filename))
                    if shadow:draft['hands'][role]['shadow']=item
                    else:
                        previous=draft['hands'].get(role,{})
                        if previous.get('shadow'):item['shadow']=previous['shadow']
                        draft['hands'][role]=item
            elif action=='hand-set-remove':
                if shadow:
                    if draft['hands'][role].get('shadow',{}).get('generated'):
                        raise ValueError(self.tr('Disattiva Genera ombre per rimuovere le ombre automatiche.'))
                    draft['hands'][role].pop('shadow',None)
                else:draft['hands'].pop(role,None)
            else:
                item=draft['hands'][role]['shadow'] if shadow else draft['hands'][role]
                if shadow and item.get('generated'):raise ValueError(self.tr('Il pivot automatico segue la lancetta. Regola lo spostamento nelle impostazioni Genera ombre.'))
                changes=req['changes']
                if set(changes)-({'pivot','offset'} if shadow else {'pivot'}):raise ValueError(self.tr('Proprietà della PNG non valida.'))
                item.update(changes);self.hand_set_catalog.validate_item(item)
        elif action=='hand-set-save':
            self.hand_set_catalog.save(draft);self.reload_hand_presets();draft=empty_draft()
        elif action=='hand-set-delete':
            self.hand_set_catalog.delete(req['id']);self.reload_hand_presets()
            if draft['id']==req['id']:draft=empty_draft()
        elif action=='hand-set-restore':
            self.hand_set_catalog.restore(req['id']);self.reload_hand_presets()
            if draft['id']==req['id']:draft=empty_draft()
        else:raise ValueError(self.tr('Comando set lancette non valido.'))
        self.hand_set_draft=self.hand_set_catalog.refresh_generated(draft)

    def set_hand(self,req,changes):
        if req.get('hand') not in ('hour','minute','second'):raise ValueError(self.tr('Lancetta non valida.'))
        e=self.element(req)
        if e.kind not in ('analog','pointer'):raise ValueError(self.tr('Seleziona un livello lancette.'))
        for k,v in changes.items():setattr(e,k,v)

    def disk_command(self,action,req):
        from copy import deepcopy
        draft=deepcopy(self.disk_draft);catalog=self.disk_catalog
        if action=='disk-catalog-new':draft=empty_disk()
        elif action=='disk-catalog-load':draft=catalog.draft(req['id'])
        elif action=='disk-catalog-meta':
            changes=req['changes']
            allowed={'name','category','mode','source','valueStart','valueRange','angleStart','angleRange','generateShadows','shadowOptions','moonReferenceDate','moonDayOffset'}
            if set(changes)-allowed:raise ValueError(self.tr('Proprietà disco non valida.'))
            if 'name' in changes and (not isinstance(changes['name'],str) or len(changes['name'])>80):raise ValueError(self.tr('Nome disco troppo lungo.'))
            if changes.get('mode') and changes['mode']!=draft['mode'] and draft['hands']:
                first=deepcopy(next(iter(draft['hands'].values())))
                draft['hands']={'disk' if changes['mode']=='rotation' else '0':first}
            if 'source' in changes and changes['source']!=draft['source']:
                mapping={'value_start':'valueStart','value_range':'valueRange','angle_start':'angleStart','angle_range':'angleRange','moon_reference_date':'moonReferenceDate','moon_day_offset':'moonDayOffset'}
                changes={**{mapping[k]:v for k,v in moon_defaults(changes['source']).items()},**changes}
            if changes.get('mode')=='values' and changes.get('source',draft['source'])==MOON_SOURCE:
                changes['source']='dateLunarDay'
            if changes.get('source')==MOON_SOURCE and changes.get('mode',draft['mode'])!='rotation':
                raise ValueError(self.tr('Per le fasi lunari a 59 posizioni scegli Disco rotante.'))
            draft.update(changes)
        elif action in ('disk-catalog-image','disk-catalog-part','disk-catalog-remove'):
            key=str(req.get('key','disk'));shadow=bool(req.get('shadow'))
            if draft['mode']=='rotation' and key!='disk' or draft['mode']=='values' and (not key.isdigit() or int(key)>65535):raise ValueError(self.tr('Valore dell’immagine non valido.'))
            if shadow and key not in draft['hands']:raise ValueError(self.tr('Importa prima la grafica del disco.'))
            if action=='disk-catalog-image':
                path=self.dialogs.open('disk-shadow-open' if shadow else 'disk-image-open',(self.tr('Importa PNG ') + 'ombra' if shadow else 'disco'),self.root,self.tr('Dischi PNG (*.png)'))
                if path:
                    item=catalog.stage(Path(path))
                    if shadow:draft['hands'][key]['shadow']=item
                    else:draft['hands'][key]=item
            elif action=='disk-catalog-remove':
                if shadow:draft['hands'][key].pop('shadow',None)
                else:draft['hands'].pop(key,None)
            else:
                item=draft['hands'][key]['shadow'] if shadow else draft['hands'][key]
                if shadow and item.get('generated'):raise ValueError(self.tr('Il pivot dell’ombra automatica segue il disco.'))
                changes=req['changes']
                if set(changes)-({'pivot','offset'} if shadow else {'pivot'}):raise ValueError(self.tr('Proprietà PNG non valida.'))
                item.update(changes);catalog.validate_item(item)
                # Sequence frames share one pivot; one click calibrates all.
                if draft['mode']=='values':
                    for frame in draft['hands'].values():
                        target=frame.get('shadow') if shadow else frame
                        if target:target.update(deepcopy(changes));catalog.validate_item(target)
        elif action=='disk-catalog-save':
            catalog.save(draft);self.reload_disks();draft=empty_disk()
        elif action in ('disk-catalog-delete','disk-catalog-restore'):
            (catalog.delete if action.endswith('delete') else catalog.restore)(req['id']);self.reload_disks()
            if draft['id']==req['id']:draft=empty_disk()
        else:raise ValueError(self.tr('Comando catalogo dischi non valido.'))
        self.disk_draft=catalog.refresh_generated(draft)

    def set_compass(self,req,changes):
        e=self.element(req)
        if e.kind!='compass':raise ValueError(self.tr('Seleziona un livello bussola.'))
        for k,v in changes.items():setattr(e,k,v)

    def background_layer(self):
        variant=self.project.variants[self.variant]
        normal=[e for e in self.design.ordered_layers(False) if isinstance(e,Element)]
        existing=next((e for e in normal if e.id==variant.get('backgroundLayerId')),None)
        if existing is None:
            candidates=[e for e in normal if e.kind=='image' and e.x<=0 and e.y<=0 and
                        e.x+e.width>=480 and e.y+e.height>=480]
            existing=next((e for e in candidates if e.name!='Sfondo variante'),candidates[0] if candidates else None)
        return existing

    def set_background_image(self,image):
        if self.aod:raise ValueError(self.tr('Seleziona uno stile normale per cambiarne lo sfondo.'))
        variant=self.project.variants[self.variant];existing=self.background_layer()
        if existing:
            existing.asset=image.asset;existing.visible=True;existing.opacity=255;existing.tint=False
            variant['backgroundLayerId']=existing.id
        else:
            image.name='Sfondo';image.x=image.y=0;image.width=image.height=480;image.locked=True;image.aod=False
            self.design.elements.insert(0,image);self.design.layer_order.insert(0,image.id);variant['backgroundLayerId']=image.id


class MainWindow(QMainWindow):
    def __init__(self,*,smoke=False,settings_path=None):
        super().__init__()
        self.settings=AppSettings(settings_path)
        self.language=install_language(self.settings.language)
        self.setWindowTitle(self.tr('S5 Studio 2.8 — Xiaomi Watch S5'));self.resize(1440,920);self.setMinimumSize(1120,760)
        self.view=QWebEngineView(self);self.view.setPage(LocalPage(self.view));self.setCentralWidget(self.view)
        self.bridge=StudioBridge(self,smoke=smoke)
        self.channel=QWebChannel(self.view.page());self.channel.registerObject('studio',self.bridge);self.view.page().setWebChannel(self.channel)
        base=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else self.bridge.root
        self.view.setUrl(QUrl.fromLocalFile(str(base/'frontend/index.html')))
        if not smoke:QTimer.singleShot(1800,self.bridge.offer_recovery)

    def set_language(self,language):
        self.settings.update(language=language)
        self.language=install_language(language)
        self.setWindowTitle(self.tr('S5 Studio 2.8 — Xiaomi Watch S5'))

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
