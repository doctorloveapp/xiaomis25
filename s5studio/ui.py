from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
import json
import sys
import traceback

from PySide6.QtCore import Qt, Signal, QThread, QTimer, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QKeySequence, QAction, QIcon, QImage, QFontDatabase
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox, QCheckBox, QListWidget, QListWidgetItem,
    QFormLayout, QGroupBox, QFileDialog, QMessageBox, QColorDialog, QScrollArea, QSplitter,
    QTabWidget, QTextEdit, QDialog, QDialogButtonBox, QSlider, QAbstractItemView)

from . import __version__
from .model import Project, Element, SOURCES, identifier, template
from .render import render, png_bytes, element_image, SCENARIOS, layout_errors
from .native import build, compiler_probe, inspect_mwz, TRANSFER_GUIDE


def app_root():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


STYLE = """
QWidget { background:#101722; color:#e8eef7; font-family:'Segoe UI'; font-size:12px; }
QMainWindow { background:#0b111b; }
QLabel#title { font-size:24px; font-weight:700; color:#ffffff; }
QLabel#subtitle { color:#91a1b7; }
QLabel#eyebrow { color:#6ce5c1; font-size:11px; font-weight:700; }
QGroupBox { background:#151e2c; border:1px solid #283447; border-radius:10px; margin-top:15px; padding:12px 8px 8px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 4px; }
QPushButton { background:#202d40; border:1px solid #34435a; border-radius:7px; padding:8px 12px; }
QPushButton:hover { background:#2c3e56; border-color:#607591; }
QPushButton:pressed { background:#3d5270; }
QPushButton:disabled { color:#6e7c8f; background:#1a2534; }
QPushButton#primary { background:#6ce5c1; color:#081b18; border:0; font-weight:700; }
QPushButton#primary:hover { background:#8cf3d4; }
QLineEdit,QSpinBox,QComboBox,QTextEdit { background:#0c1420; border:1px solid #344157; border-radius:5px; padding:5px; min-height:20px; }
QLineEdit:focus,QSpinBox:focus,QComboBox:focus { border-color:#6ce5c1; }
QComboBox QAbstractItemView { background:#172334; selection-background-color:#35534d; }
QListWidget { background:#0c1420; border:1px solid #283447; border-radius:6px; padding:4px; }
QListWidget::item { padding:9px 6px; border-radius:4px; }
QListWidget::item:selected { background:#21483f; color:#8ef4d5; }
QTabWidget::pane { border:0; }
QTabBar::tab { background:#1b2738; padding:9px 13px; margin:2px; border-radius:5px; }
QTabBar::tab:selected { background:#305047; color:#8ef4d5; }
QScrollArea { border:0; }
QSplitter::handle { background:#0b111b; width:10px; }
QCheckBox { spacing:7px; }
QStatusBar { background:#0b111b; color:#a4b4c9; }
QToolTip { background:#25364b; color:#fff; border:1px solid #607591; }
"""


def button(text, callback, primary=False):
    b=QPushButton(text)
    if primary:
        b.setObjectName("primary")
    b.clicked.connect(callback)
    return b


def pixmap(data):
    p=QPixmap()
    p.loadFromData(data,"PNG")
    return p


class Canvas(QWidget):
    selected=Signal(str)
    drag_started=Signal()
    changed=Signal()

    def __init__(self):
        super().__init__()
        self.project=template()
        self.values=dict(SCENARIOS['Normale'])
        self.selection=""
        self.aod=False
        self.zoom=1.0
        self.grid=False
        self.snap=True
        self.drag=None
        self.cached=QPixmap()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.refresh()

    def refresh(self):
        self.cached=pixmap(png_bytes(render(self.project,self.values,self.aod)))
        self.setFixedSize(round(520*self.zoom),round(520*self.zoom))
        self.update()

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.zoom,self.zoom)
        p.fillRect(QRectF(0,0,520,520),QColor('#0b111b'))
        p.setBrush(QColor('#090e16'))
        p.setPen(QPen(QColor('#34445a'),8))
        p.drawEllipse(QRectF(13,13,494,494))
        p.drawPixmap(20,20,self.cached)
        if self.grid:
            p.save()
            from PySide6.QtGui import QPainterPath
            mask=QPainterPath()
            mask.addEllipse(QRectF(20,20,480,480))
            p.setClipPath(mask)
            p.setPen(QPen(QColor(130,150,170,40),1))
            for n in range(0,481,20):
                p.drawLine(20+n,20,20+n,500)
                p.drawLine(20,20+n,500,20+n)
            p.restore()
        for e in self.project.elements:
            if e.id==self.selection and e.aod==self.aod and e.visible:
                p.setPen(QPen(QColor('#6ce5c1'),1.5,Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                rect=QRectF(e.x+20,e.y+20,e.width,e.height)
                p.drawRect(rect)
                p.setBrush(QColor('#6ce5c1'))
                for point in [rect.topLeft(),rect.topRight(),rect.bottomLeft(),rect.bottomRight()]:
                    p.drawEllipse(point,3,3)

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton:
            return
        pos=event.position()/self.zoom
        x,y=pos.x()-20,pos.y()-20
        found=None
        for e in reversed(self.project.elements):
            if e.visible and e.aod==self.aod and not e.locked and e.x<=x<=e.x+e.width and e.y<=y<=e.y+e.height:
                found=e
                break
        self.selection=found.id if found else ''
        self.selected.emit(self.selection)
        if found:
            self.drag=(found.id,x,y,found.x,found.y,False)
        self.update()

    def mouseMoveEvent(self,event):
        if not self.drag:
            return
        id,x,y,oldx,oldy,started=self.drag
        e=next((e for e in self.project.elements if e.id==id),None)
        if not e:
            return
        pos=event.position()/self.zoom
        newx=round(oldx+pos.x()-20-x)
        newy=round(oldy+pos.y()-20-y)
        if self.snap:
            newx=round(newx/10)*10
            newy=round(newy/10)*10
        newx=max(0,min(480-e.width,newx))
        newy=max(0,min(480-e.height,newy))
        if (newx,newy)!=(e.x,e.y):
            if not started:
                self.drag_started.emit()
                started=True
            e.x,e.y=newx,newy
            self.drag=(id,x,y,oldx,oldy,started)
            self.refresh()

    def mouseReleaseEvent(self,event):
        if self.drag and self.drag[-1]:
            self.changed.emit()
        self.drag=None


class BuildWorker(QThread):
    progress=Signal(str)
    finished_build=Signal(str,str)

    def __init__(self,project,compiler,destination):
        super().__init__()
        self.project=project
        self.compiler=compiler
        self.destination=destination

    def run(self):
        try:
            result=build(self.project,self.compiler,self.destination,self.progress.emit)
            self.finished_build.emit(str(result),"")
        except Exception as exc:
            self.finished_build.emit("",str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # The Windows offscreen platform has no system font collection. Loading
        # the installed UI fonts also makes automated visual checks faithful.
        import os
        fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
        for name in ('segoeui.ttf','segoeuib.ttf'):
            if (fonts/name).exists():
                QFontDatabase.addApplicationFont(str(fonts/name))
        self.root=app_root()
        self.project=template()
        self.path=None
        self.dirty=False
        self.history=[]
        self.redo_history=[]
        self.selection=next(e.id for e in self.project.elements if e.kind=='clock')
        self.refreshing=False
        self.worker=None
        self.compiler=self.root/'tools/easyface-4.23/Compiler.exe'
        self.settings_path=self.root/'data/settings.json'
        try:
            settings=json.loads(self.settings_path.read_text(encoding='utf-8'))
            if settings.get('compiler'):
                self.compiler=Path(settings['compiler'])
        except (OSError,ValueError):
            pass
        self.setWindowTitle('S5 Studio')
        self.resize(1320,900)
        self.setMinimumSize(1080,720)
        self.setStyleSheet(STYLE)
        central=QWidget()
        self.setCentralWidget(central)
        main=QVBoxLayout(central)
        main.setContentsMargins(22,18,22,8)
        head=QHBoxLayout()
        brand=QVBoxLayout()
        eyebrow=QLabel('XIAOMI WATCH S5  ·  46 MM')
        eyebrow.setObjectName('eyebrow')
        title=QLabel('Il tuo tempo. Il tuo quadrante.')
        title.setObjectName('title')
        subtitle=QLabel('Importa una foto, personalizza i dati e compila per il tuo S5.')
        subtitle.setObjectName('subtitle')
        brand.addWidget(eyebrow)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        head.addLayout(brand)
        head.addStretch()
        for label,fn in [('Apri',self.open_project),('Salva',self.save_project),('Guida',self.show_guide)]:
            head.addWidget(button(label,fn))
        self.export_button=button('Compila per S5',self.export_project,True)
        head.addWidget(self.export_button)
        main.addLayout(head)
        splitter=QSplitter(Qt.Orientation.Horizontal)
        self.workspace=splitter
        main.addWidget(splitter,1)
        left=QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(290)
        ll=QVBoxLayout(left)
        ll.setContentsMargins(0,12,0,0)
        box=QGroupBox('01  Parti da un modello')
        bl=QVBoxLayout(box)
        row=QHBoxLayout()
        self.template_combo=QComboBox()
        self.template_combo.addItems(['Digitale','Analogico','Salute'])
        row.addWidget(self.template_combo,1)
        row.addWidget(button('Nuovo',self.new_project))
        bl.addLayout(row)
        bl.addWidget(button('Importa foto come sfondo',lambda:self.import_image(True),True))
        ll.addWidget(box)
        box=QGroupBox('02  Aggiungi componenti')
        bl=QVBoxLayout(box)
        self.add_combo=QComboBox()
        self.add_combo.addItems(['Ora digitale','Data','Numero dinamico','Testo','Immagine','Lancette','Rettangolo','Cerchio'])
        bl.addWidget(self.add_combo)
        bl.addWidget(button('Aggiungi al quadrante',self.add_element))
        ll.addWidget(box)
        box=QGroupBox('Livelli')
        bl=QVBoxLayout(box)
        self.layers=QListWidget()
        self.layers.setMinimumHeight(150)
        self.layers.currentItemChanged.connect(self.layer_selected)
        bl.addWidget(self.layers,1)
        row=QHBoxLayout()
        row.addWidget(button('↑',lambda:self.reorder(1)))
        row.addWidget(button('↓',lambda:self.reorder(-1)))
        row.addWidget(button('Duplica',self.duplicate_element))
        bl.addLayout(row)
        bl.addWidget(button('Elimina componente',self.delete_element))
        ll.addWidget(box,1)
        row=QHBoxLayout()
        self.undo_button=button('Annulla',self.undo)
        self.redo_button=button('Ripeti',self.redo)
        row.addWidget(self.undo_button)
        row.addWidget(self.redo_button)
        ll.addLayout(row)
        splitter.addWidget(left)

        middle=QWidget()
        ml=QVBoxLayout(middle)
        ml.setContentsMargins(12,12,12,0)
        row=QHBoxLayout()
        self.mode=QComboBox()
        self.mode.addItems(['Quadrante attivo','Always On Display'])
        self.mode.currentIndexChanged.connect(self.change_mode)
        row.addWidget(self.mode)
        row.addStretch()
        self.grid=QCheckBox('Griglia')
        self.grid.toggled.connect(self.grid_changed)
        self.snap=QCheckBox('Snap')
        self.snap.setChecked(True)
        self.snap.toggled.connect(lambda b:setattr(self.canvas,'snap',b))
        row.addWidget(self.grid)
        row.addWidget(self.snap)
        ml.addLayout(row)
        self.canvas=Canvas()
        self.canvas.selected.connect(self.select)
        self.canvas.drag_started.connect(self.checkpoint)
        self.canvas.changed.connect(self.finish_change)
        holder=QWidget()
        hl=QVBoxLayout(holder)
        hl.addWidget(self.canvas,0,Qt.AlignmentFlag.AlignCenter)
        scroll=QScrollArea()
        scroll.setWidget(holder)
        scroll.setWidgetResizable(True)
        ml.addWidget(scroll,1)
        row=QHBoxLayout()
        label=QLabel('ANTEPRIMA CON DATI SIMULATI')
        label.setObjectName('eyebrow')
        row.addWidget(label)
        row.addStretch()
        row.addWidget(QLabel('Zoom'))
        self.zoom=QSlider(Qt.Orientation.Horizontal)
        self.zoom.setRange(65,150)
        self.zoom.setValue(100)
        self.zoom.setMaximumWidth(100)
        self.zoom.valueChanged.connect(self.zoom_changed)
        row.addWidget(self.zoom)
        ml.addLayout(row)
        self.feedback=QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setObjectName('subtitle')
        ml.addWidget(self.feedback)
        splitter.addWidget(middle)

        right=QTabWidget()
        right.setMinimumWidth(265)
        right.setMaximumWidth(340)
        properties=QWidget()
        pl=QVBoxLayout(properties)
        self.prop_group=QGroupBox('Componente selezionato')
        form=QFormLayout(self.prop_group)
        self.fields={}
        for key,label in [('name','Nome'),('text','Testo')]:
            control=QLineEdit()
            control.editingFinished.connect(self.commit_properties)
            self.fields[key]=control
            form.addRow(label,control)
        for key,label,minv,maxv in [('x','Posizione X',0,479),('y','Posizione Y',0,479),('width','Larghezza',1,480),('height','Altezza',1,480),('size','Font (px)',8,160),('digits','Cifre',1,6),('opacity','Opacità',0,255)]:
            control=QSpinBox()
            control.setRange(minv,maxv)
            control.setKeyboardTracking(False)
            control.editingFinished.connect(self.commit_properties)
            self.fields[key]=control
            form.addRow(label,control)
        self.fields['source']=QComboBox()
        for key,(label,_,_) in SOURCES.items():
            self.fields['source'].addItem(label,key)
        self.fields['source'].currentIndexChanged.connect(self.commit_properties)
        form.addRow('Dato reale',self.fields['source'])
        for key,label,values in [('align','Allineamento',[('Sinistra','left'),('Centro','center'),('Destra','right')]),('fit','Immagine',[('Ritaglia al centro','cover'),('Adatta senza taglio','contain'),('Riempi / estendi','stretch')])]:
            control=QComboBox()
            for title,value in values:
                control.addItem(title,value)
            control.currentIndexChanged.connect(self.commit_properties)
            self.fields[key]=control
            form.addRow(label,control)
        self.color_button=button('Colore',self.element_color)
        form.addRow('Colore',self.color_button)
        for key,label in [('leading_zero','Mostra zeri iniziali'),('bold','Grassetto'),('visible','Visibile'),('locked','Blocca posizione')]:
            control=QCheckBox(label)
            control.toggled.connect(self.commit_properties)
            self.fields[key]=control
            form.addRow(control)
        form.addRow(button('Importa font TTF / OTF',self.import_font))
        form.addRow(button('Centra sul quadrante',self.center_element))
        pl.addWidget(self.prop_group)
        pl.addStretch()
        ps=QScrollArea()
        ps.setWidget(properties)
        ps.setWidgetResizable(True)
        right.addTab(ps,'Proprietà')

        project_tab=QWidget()
        pl=QVBoxLayout(project_tab)
        box=QGroupBox('Il tuo progetto')
        f=QFormLayout(box)
        self.project_fields={}
        for key,label in [('name','Nome progetto'),('author','Autore'),('face_id','ID template'),('version','Versione')]:
            control=QLineEdit()
            control.editingFinished.connect(self.commit_project)
            self.project_fields[key]=control
            f.addRow(label,control)
        f.addRow(button('Colore dello sfondo',self.background_color))
        self.aod_enabled=QCheckBox('Includi AOD nella compilazione')
        self.aod_enabled.toggled.connect(self.commit_project)
        f.addRow(self.aod_enabled)
        f.addRow(button('Crea AOD essenziale',self.create_aod))
        pl.addWidget(box)
        status=QLabel('S5 46 mm · M2530W1\n480 × 480 · target 562\nPackaging: template funzionante\nID e metadati ZIP preservati\n\nI nuovi progetti usano i default del template.\nIl ZIP esportato mantiene nome, autore e versione originali anche se rinomini il progetto.\n\nProva del nuovo payload sul tuo S5: da eseguire\nBussola live: non abilitata')
        status.setWordWrap(True)
        status.setObjectName('subtitle')
        pl.addWidget(status)
        pl.addWidget(button('Seleziona compilatore…',self.select_compiler))
        pl.addWidget(button('Verifica pacchetto MWZ…',self.check_package))
        pl.addWidget(button('Registra prova sull’orologio…',self.record_hardware_test))
        pl.addWidget(button('Esporta anteprima PNG…',self.save_preview))
        pl.addStretch()
        right.addTab(project_tab,'Progetto')

        sim=QWidget()
        sl=QVBoxLayout(sim)
        box=QGroupBox('Simula i dati')
        f=QFormLayout(box)
        self.scenario=QComboBox()
        self.scenario.addItems(SCENARIOS.keys())
        self.scenario.currentTextChanged.connect(self.scenario_changed)
        f.addRow('Scenario',self.scenario)
        self.sim_fields={}
        for key,(label,_,digits) in SOURCES.items():
            spin=QSpinBox()
            spin.setRange(-1,{'hour':23,'minute':59,'second':59,'day':31,'month':12}.get(key,10**digits-1))
            spin.setSpecialValueText('--')
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(self.simulation_changed)
            f.addRow(label,spin)
            self.sim_fields[key]=spin
        sl.addWidget(box)
        note=QLabel('Questi numeri servono soltanto all’anteprima. Sul quadrante compilato i dati arrivano dal sistema dell’orologio.\n\nIl comportamento del dato assente sul firmware deve ancora essere provato.')
        note.setObjectName('subtitle')
        note.setWordWrap(True)
        sl.addWidget(note)
        sl.addStretch()
        right.addTab(sim,'Simula')
        splitter.addWidget(right)
        splitter.setSizes([240,690,300])
        self.statusBar().showMessage('Pronto. Importa un’immagine o modifica il modello iniziale.')
        for shortcut,fn in [('Ctrl+S',self.save_project),('Ctrl+Shift+S',self.save_as),('Ctrl+O',self.open_project),('Ctrl+N',self.new_project),('Ctrl+Z',self.undo),('Ctrl+Y',self.redo)]:
            action=QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(fn)
            self.addAction(action)
        self.scenario_changed('Normale')
        self.refresh()
        self.recovery_timer=QTimer(self)
        self.recovery_timer.timeout.connect(self.autosave)
        self.recovery_timer.start(20000)
        QTimer.singleShot(100,self.offer_recovery)

    def error(self,text):
        QMessageBox.warning(self,'S5 Studio',str(text))

    def checkpoint(self):
        self.history.append(self.project.copy())
        self.history=self.history[-40:]
        self.redo_history.clear()

    def finish_change(self):
        self.dirty=True
        self.refresh()

    def refresh(self):
        self.refreshing=True
        self.canvas.project=self.project
        self.canvas.selection=self.selection
        self.canvas.refresh()
        self.layers.clear()
        for e in reversed(self.project.elements):
            if e.aod!=self.canvas.aod:
                continue
            label=('◌ ' if not e.visible else '')+('▣ ' if e.locked else '')+e.name
            item=QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole,e.id)
            self.layers.addItem(item)
            if e.id==self.selection:
                self.layers.setCurrentItem(item)
        for key,control in self.project_fields.items():
            control.setText(str(getattr(self.project,key)))
        self.aod_enabled.setChecked(self.project.aod_enabled)
        self.refreshing=False
        self.show_properties()
        errors=self.project.validate()
        if not errors:
            errors=layout_errors(self.project)
        self.feedback.setText(('Da correggere: '+errors[0]) if errors else ('Trascina un componente per spostarlo. Il bordo circolare mostra l’area visibile.'))
        self.undo_button.setEnabled(bool(self.history))
        self.redo_button.setEnabled(bool(self.redo_history))
        self.setWindowTitle(f'{self.project.name}{" *" if self.dirty else ""} — S5 Studio {__version__}')

    def selected_element(self):
        return next((e for e in self.project.elements if e.id==self.selection),None)

    def select(self,id):
        self.selection=id
        self.refreshing=True
        for index in range(self.layers.count()):
            if self.layers.item(index).data(Qt.ItemDataRole.UserRole)==id:
                self.layers.setCurrentRow(index)
                break
        else:
            self.layers.clearSelection()
            self.layers.setCurrentRow(-1)
        self.refreshing=False
        self.canvas.selection=id
        self.canvas.update()
        self.show_properties()

    def layer_selected(self,current,previous):
        if not self.refreshing:
            self.select(current.data(Qt.ItemDataRole.UserRole) if current else '')

    def show_properties(self):
        e=self.selected_element()
        self.refreshing=True
        self.prop_group.setEnabled(e is not None)
        self.prop_group.setTitle('Componente selezionato' if e else 'Seleziona un componente sul canvas')
        if e:
            for key,control in self.fields.items():
                value=getattr(e,key)
                if isinstance(control,QCheckBox):
                    control.setChecked(value)
                elif isinstance(control,QComboBox):
                    control.setCurrentIndex(control.findData(value))
                elif isinstance(control,QSpinBox):
                    control.setValue(value)
                else:
                    control.setText(value)
            self.fields['text'].setEnabled(e.kind=='text')
            self.fields['source'].setEnabled(e.kind=='number')
            self.fields['digits'].setEnabled(e.kind=='number')
            self.fields['fit'].setEnabled(e.kind=='image')
            for key in ('x','y'):
                self.fields[key].setEnabled(not e.locked)
            self.color_button.setText(e.color)
        self.refreshing=False

    def commit_properties(self,*args):
        if self.refreshing:
            return
        e=self.selected_element()
        if not e:
            return
        changes={}
        for key,control in self.fields.items():
            if isinstance(control,QCheckBox):
                value=control.isChecked()
            elif isinstance(control,QComboBox):
                value=control.currentData()
            elif isinstance(control,QSpinBox):
                value=control.value()
            else:
                value=control.text()
            if getattr(e,key)!=value:
                changes[key]=value
        if changes:
            if 'source' in changes:
                changes['digits']=SOURCES[changes['source']][2]
            self.checkpoint()
            for key,value in changes.items():
                setattr(e,key,value)
            self.finish_change()

    def commit_project(self,*args):
        if self.refreshing:
            return
        changes={k:c.text() for k,c in self.project_fields.items() if getattr(self.project,k)!=c.text()}
        if self.project.aod_enabled!=self.aod_enabled.isChecked():
            changes['aod_enabled']=self.aod_enabled.isChecked()
        if changes:
            self.checkpoint()
            for k,v in changes.items():
                setattr(self.project,k,v)
            self.finish_change()

    def grid_changed(self,value):
        self.canvas.grid=value
        self.canvas.update()

    def zoom_changed(self,value):
        self.canvas.zoom=value/100
        self.canvas.refresh()

    def change_mode(self,index):
        self.canvas.aod=index==1
        self.selection=''
        self.refresh()

    def scenario_changed(self,name):
        values=SCENARIOS[name]
        for key,control in self.sim_fields.items():
            control.blockSignals(True)
            control.setValue(-1 if values.get(key) is None else values[key])
            control.blockSignals(False)
        self.simulation_changed()

    def simulation_changed(self,*args):
        self.canvas.values={key:None if c.value()==-1 else c.value() for key,c in self.sim_fields.items()}
        # Invalid time values do not feed the analogue arithmetic.
        for key in ('hour','minute'):
            if self.canvas.values.get(key) is None:
                self.canvas.values[key]=0
        self.canvas.refresh()

    def add_element(self):
        name=self.add_combo.currentText()
        if name=='Immagine':
            self.import_image(False)
            return
        types={'Ora digitale':'clock','Data':'date','Numero dinamico':'number','Testo':'text','Lancette':'analog','Rettangolo':'rect','Cerchio':'circle'}
        kind=types[name]
        e=Element(kind=kind,name=name,aod=self.canvas.aod)
        if kind=='clock':
            e.x,e.y,e.width,e.height,e.size=75,150,330,100,80
        elif kind=='analog':
            e.x,e.y,e.width,e.height=60,60,360,360
        elif kind=='date':
            e.width=160
            e.size=30
        elif kind in {'rect','circle'}:
            e.color='#6ce5c1'
            e.width,e.height=100,100 if kind=='circle' else 30
        self.checkpoint()
        self.project.elements.append(e)
        self.selection=e.id
        self.finish_change()

    def import_image(self,background=False):
        path,_=QFileDialog.getOpenFileName(self,'Scegli un’immagine','', 'Immagini (*.png *.jpg *.jpeg *.webp *.bmp *.svg)')
        if not path:
            return
        try:
            self.checkpoint()
            if Path(path).suffix.lower()=='.svg':
                from PySide6.QtSvg import QSvgRenderer
                from tempfile import TemporaryDirectory
                renderer=QSvgRenderer(path)
                if not renderer.isValid():
                    raise ValueError('SVG non valido.')
                size=renderer.defaultSize()
                size.scale(QSize(1920,1920),Qt.AspectRatioMode.KeepAspectRatio)
                image=QImage(size,QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(Qt.GlobalColor.transparent)
                painter=QPainter(image)
                renderer.render(painter)
                painter.end()
                with TemporaryDirectory() as temp:
                    converted=Path(temp)/'immagine.png'
                    image.save(str(converted),'PNG')
                    e=self.project.add_image(converted,background=background,aod=self.canvas.aod)
            else:
                e=self.project.add_image(Path(path),background=background,aod=self.canvas.aod)
            self.selection=e.id
            self.finish_change()
        except Exception as exc:
            self.error(exc)

    def import_font(self):
        e=self.selected_element()
        if not e:
            return
        path,_=QFileDialog.getOpenFileName(self,'Scegli un font','', 'Font (*.ttf *.otf)')
        if path:
            try:
                self.checkpoint()
                e.font_asset=self.project.add_font(Path(path))
                self.finish_change()
            except Exception as exc:
                self.error(exc)

    def element_color(self):
        e=self.selected_element()
        if e:
            from .color_picker import choose_graphic_color
            changes=choose_graphic_color(e,'color',self)
            if changes is not None:
                self.checkpoint()
                for key,value in changes.items():setattr(e,key,value)
                self.finish_change()

    def background_color(self):
        from .color_picker import choose_graphic_color
        changes=choose_graphic_color({'background':self.project.background},'background',self)
        if changes is not None:
            self.checkpoint()
            self.project.background=changes['background']
            self.finish_change()

    def center_element(self):
        e=self.selected_element()
        if e and not e.locked:
            self.checkpoint()
            e.x,e.y=(480-e.width)//2,(480-e.height)//2
            self.finish_change()

    def duplicate_element(self):
        e=self.selected_element()
        if e:
            self.checkpoint()
            clone=replace(e,id=identifier(),name=e.name+' copia',x=min(480-e.width,e.x+10),y=min(480-e.height,e.y+10),locked=False)
            self.project.elements.append(clone)
            self.selection=clone.id
            self.finish_change()

    def delete_element(self):
        e=self.selected_element()
        if e:
            self.checkpoint()
            self.project.elements.remove(e)
            self.selection=''
            self.finish_change()

    def reorder(self,direction):
        e=self.selected_element()
        if e:
            visible=[item for item in self.project.elements if item.aod==e.aod]
            index=visible.index(e)
            nextindex=index+direction
            if 0<=nextindex<len(visible):
                other=visible[nextindex]
                a,b=self.project.elements.index(e),self.project.elements.index(other)
                self.checkpoint()
                self.project.elements[a],self.project.elements[b]=other,e
                self.finish_change()

    def undo(self):
        if self.history and not self.busy():
            self.redo_history.append(self.project.copy())
            self.project=self.history.pop()
            self.selection=''
            self.finish_change()

    def redo(self):
        if self.redo_history and not self.busy():
            self.history.append(self.project.copy())
            self.project=self.redo_history.pop()
            self.selection=''
            self.finish_change()

    def create_aod(self):
        self.checkpoint()
        self.project.elements=[e for e in self.project.elements if not e.aod]
        self.project.elements.extend([Element(kind='clock',name='Ora AOD',aod=True,x=95,y=190,width=290,height=75,size=64),
                                      Element(kind='date',name='Data AOD',aod=True,x=166,y=282,width=148,height=34,size=26,color='#808080')])
        self.project.aod_enabled=True
        self.mode.setCurrentIndex(1)
        self.selection=next(e.id for e in self.project.elements if e.aod and e.kind=='clock')
        self.finish_change()

    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def confirm_leave(self):
        if self.busy():
            return False
        if not self.dirty:
            return True
        reply=QMessageBox.question(self,'Salva il progetto','Ci sono modifiche da salvare.',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Save)
        if reply==QMessageBox.StandardButton.Cancel:
            return False
        return self.save_project() if reply==QMessageBox.StandardButton.Save else True

    def new_project(self):
        if self.confirm_leave():
            self.project=template(self.template_combo.currentText())
            self.path=None
            self.history=[]
            self.redo_history=[]
            self.selection=''
            self.dirty=False
            self.mode.setCurrentIndex(0)
            self.clear_recovery()
            self.refresh()

    def open_project(self):
        if not self.confirm_leave():
            return
        path,_=QFileDialog.getOpenFileName(self,'Apri progetto',str(self.root/'projects'),'Progetti S5 Studio (*.s5faceproj)')
        if path:
            try:
                p=Project.load(Path(path))
                self.project=p
                self.path=Path(path)
                self.dirty=False
                self.history=[]
                self.redo_history=[]
                self.selection=''
                self.mode.setCurrentIndex(0)
                self.clear_recovery()
                self.refresh()
            except Exception as exc:
                self.error(exc)

    def save_as(self):
        return self.save_project(force_dialog=True)

    def save_project(self,checked=False,force_dialog=False):
        if self.busy():
            return False
        self.commit_properties()
        self.commit_project()
        path=self.path
        if not path or force_dialog:
            suggested=self.root/'projects'/f'{self.project.face_id}.s5faceproj'
            selected,_=QFileDialog.getSaveFileName(self,'Salva progetto',str(path or suggested),'Progetti S5 Studio (*.s5faceproj)')
            if not selected:
                return False
            path=Path(selected)
            if path.suffix.lower()!='.s5faceproj':
                path=path.with_suffix('.s5faceproj')
        try:
            self.project.save(path,png_bytes(render(self.project)))
            self.path=path
            self.dirty=False
            self.clear_recovery()
            self.refresh()
            self.statusBar().showMessage(f'Progetto salvato: {path}')
            return True
        except Exception as exc:
            self.error(exc)
            return False

    def recovery_path(self):
        return self.root/'data/recovery.s5faceproj'

    def autosave(self):
        if self.dirty and not self.busy():
            try:
                self.project.save(self.recovery_path())
            except Exception:
                pass

    def clear_recovery(self):
        self.recovery_path().unlink(missing_ok=True)

    def offer_recovery(self):
        path=self.recovery_path()
        if path.exists():
            reply=QMessageBox.question(self,'Recupera progetto','È disponibile un progetto recuperato automaticamente. Vuoi aprirlo?')
            if reply==QMessageBox.StandardButton.Yes:
                try:
                    self.project=Project.load(path)
                    self.dirty=True
                    self.refresh()
                except Exception as exc:
                    self.error(exc)
            else:
                self.clear_recovery()

    def select_compiler(self):
        path,_=QFileDialog.getOpenFileName(self,'EasyFace Compiler 4.23',str(self.compiler.parent),'Compilatore (Compiler.exe)')
        if path:
            try:
                info=compiler_probe(Path(path))
                self.compiler=Path(path)
                self.settings_path.parent.mkdir(parents=True,exist_ok=True)
                self.settings_path.write_text(json.dumps({'compiler':str(self.compiler)},indent=2),encoding='utf-8')
                self.statusBar().showMessage(f'Compilatore S5 selezionato · SHA-256 {info["sha256"][:16]}…')
            except Exception as exc:
                self.error(exc)

    def export_project(self):
        if self.busy():
            return
        self.commit_properties()
        self.commit_project()
        try:
            errors=self.project.validate()+layout_errors(self.project)
            if errors:
                raise ValueError('\n'.join(errors))
            compiler_probe(self.compiler)
        except Exception as exc:
            self.error(exc)
            return
        path=QFileDialog.getExistingDirectory(self,'Cartella per le build',str(self.root/'dist'))
        if not path:
            return
        self.export_button.setEnabled(False)
        self.workspace.setEnabled(False)
        self.worker=BuildWorker(self.project.copy(),self.compiler,Path(path))
        self.worker.progress.connect(self.statusBar().showMessage)
        self.worker.finished_build.connect(self.build_complete)
        self.worker.start()

    def build_complete(self,path,error):
        self.workspace.setEnabled(True)
        self.export_button.setEnabled(True)
        if error:
            self.statusBar().showMessage('Compilazione non completata.')
            self.error(error)
        else:
            self.statusBar().showMessage(f'Build salvata in {path}')
            self.text_dialog('Quadrante compilato',f'ZIP creato dal template quadrante_funzionante.zip.\n\nCartella: {path}\n\nCopia sul telefono il file *_TEMPLATE.zip senza estrarlo. Struttura e file preservati sono stati verificati automaticamente.\n\nL’identità del template è mantenuta: l’installazione può sostituire il quadrante originale. Capability, hashCode e manifest restano intatti; la loro coerenza con il nuovo payload e il funzionamento sul S5 vanno ancora provati.\n\nUsa le impostazioni della mod con cui hai collaudato il template. Leggi LEGGIMI.txt e build-report.json.',open_path=Path(path))

    def text_dialog(self,title,text,open_path=None):
        dialog=QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(650,480)
        layout=QVBoxLayout(dialog)
        editor=QTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(text)
        layout.addWidget(editor)
        if open_path:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            layout.addWidget(button('Apri cartella',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(open_path)))))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def show_guide(self):
        self.text_dialog('Guida rapida', '1. Scegli un modello e importa una foto come sfondo.\n2. Trascina i componenti o modifica le proprietà.\n3. Aggiungi i numeri dinamici e scegli la sorgente.\n4. Prova i valori nella scheda Simula.\n5. Salva il progetto e premi Compila per S5.\n\n'+TRANSFER_GUIDE)

    def check_package(self):
        path,_=QFileDialog.getOpenFileName(self,'Verifica pacchetto S5',str(self.root),'Pacchetti (*.mwz *.zip)')
        if path:
            try:
                result=inspect_mwz(Path(path))
                out=self.root/'data/package-reports'
                out.mkdir(parents=True,exist_ok=True)
                (out/f'{result["sha256"][:16]}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                self.text_dialog('Esito verifica MWZ',json.dumps(result,ensure_ascii=False,indent=2))
            except Exception as exc:
                self.error(exc)

    def save_preview(self):
        path,_=QFileDialog.getSaveFileName(self,'Esporta anteprima',str(self.root/'dist/preview.png'),'Immagine PNG (*.png)')
        if path:
            try:
                Path(path).write_bytes(png_bytes(render(self.project,self.canvas.values,self.canvas.aod)))
                self.statusBar().showMessage('Anteprima con dati simulati salvata.')
            except Exception as exc:
                self.error(exc)

    def record_hardware_test(self):
        dialog=QDialog(self)
        dialog.setWindowTitle('Registra una prova reale')
        layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('Registra soltanto ciò che hai osservato sul tuo orologio.'))
        form=QFormLayout()
        fields={}
        for key,label,default in [('firmware','Firmware','3.221.024'),('mod','Mi Fitness mod','V3.52.0i'),('buildSha256','SHA-256 del binario',''),('region','Regione effettiva',''),('phone','Telefono / Android','')]:
            control=QLineEdit(default)
            form.addRow(label,control)
            fields[key]=control
        outcome=QComboBox()
        outcome.addItems(['Installazione riuscita','Installazione rifiutata','Dati verificati','Errore del quadrante'])
        form.addRow('Esito',outcome)
        notes=QTextEdit()
        notes.setPlaceholderText('Dati confrontati, sleep/wake, AOD, messaggi e tempi della prova…')
        layout.addLayout(form)
        layout.addWidget(notes)
        controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(dialog.accept)
        controls.rejected.connect(dialog.reject)
        layout.addWidget(controls)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            try:
                values={k:c.text().strip() for k,c in fields.items()}
                import re
                if not re.fullmatch('[a-fA-F0-9]{64}',values['buildSha256']):
                    raise ValueError('Inserisci lo SHA-256 del resource.bin provato (nel build-report.json).')
                values.update(model='M2530W1',faceId=self.project.face_id,outcome=outcome.currentText(),notes=notes.toPlainText(),reportedBy='user',timestamp=datetime.now().astimezone().isoformat())
                target=self.root/'data/hardware-tests'
                target.mkdir(parents=True,exist_ok=True)
                (target/f'{datetime.now():%Y%m%d-%H%M%S}-{identifier()}.json').write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf-8')
                self.statusBar().showMessage('Prova registrata. Il profilo generale resta distinto dalla singola evidenza.')
            except Exception as exc:
                self.error(exc)

    def closeEvent(self,event):
        if self.busy():
            self.statusBar().showMessage('Attendi il termine della compilazione prima di chiudere.')
            event.ignore()
        elif self.confirm_leave():
            self.clear_recovery()
            event.accept()
        else:
            event.ignore()


def launch():
    app=QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('S5 Studio')
    window=MainWindow()
    window.show()
    return app.exec()
