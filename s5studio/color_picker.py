"""One color dialog for every editor context, including an explicit no-color."""
import re
from PySide6.QtWidgets import QColorDialog
from .colors import NO_COLOR


def graphic_color_state(element,key):
    def state(color,absent,role=None,mode='fill'):
        return {'color':color if re.fullmatch(r'#[a-fA-F0-9]{6}',color or '') else '#000000',
                'original':absent,'role':role,'mode':mode}
    if isinstance(element,dict):
        if key not in ('color','background','accent') or key not in element:raise ValueError('Colore non supportato.')
        return state(element[key],element[key] in ('',NO_COLOR),mode='accent' if key=='accent' else 'fill')
    if key=='color' and element.kind=='analog':
        return state(element.color,not element.show_center_cap,mode='cap')
    role=key.removesuffix('_color')
    if key in ('hour_color','minute_color','second_color') and element.kind in ('analog','pointer'):
        if element.kind=='pointer' and role!='second':raise ValueError('Colore lancetta non valido.')
        color=getattr(element,key)
        imported=bool(getattr(element,role+'_asset'))
        return state(color or element.color,color in ('',NO_COLOR) if imported else color==NO_COLOR,
                     role,mode='original' if imported else 'hand')
    if key=='color' and element.kind=='pointer':return graphic_color_state(element,'second_color')
    if key=='color' and element.kind in ('image','compass','image_values'):
        return state(element.color,not element.tint,mode='original')
    if key=='color':return state(element.color,element.color==NO_COLOR)
    if key=='border_color' and element.kind in ('rect','circle') or key=='shadow_color' and element.kind in ('rect','circle','text','number'):
        color=getattr(element,key)
        return state(color,color==NO_COLOR)
    raise ValueError('Colore non supportato.')


def graphic_color_changes(element,key,color):
    state=graphic_color_state(element,key)
    if color is not None and not re.fullmatch(r'#[a-fA-F0-9]{6}',color):raise ValueError('Colore non valido.')
    if state['mode']=='cap':return {'show_center_cap':False} if color is None else {'color':color,'show_center_cap':True}
    if state['role']:
        changes={state['role']+'_color':color if color is not None else '' if state['mode']=='original' else NO_COLOR}
        if key=='color' and color is not None:changes['color']=color
        return changes
    if state['mode']=='original':return {'tint':False} if color is None else {'color':color,'tint':True}
    return {key:color if color is not None else '' if state['mode']=='accent' else NO_COLOR}


class StudioColorDialog(QColorDialog):
    def __init__(self,state,parent):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QCheckBox,QLabel
        super().__init__(QColor(state['color']),parent)
        self.setWindowTitle(self.tr('Select Color'))
        self.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog,True)
        self.original=QCheckBox(self.tr('Nessun colore'),self)
        self.original.setObjectName('studio-original-color');self.original.setChecked(state['original'])
        help_text={'original':self.tr('Mantieni i colori e la trasparenza originali della grafica.'),
                   'cap':self.tr('Nascondi soltanto il tappo centrale, mantenendo tutte le lancette.'),
                   'accent':self.tr('Non applicare un colore accento.'),
                   'fill':self.tr('Rendi trasparente questo colore.'),
                   'hand':self.tr('Rendi trasparente la lancetta disegnata.')}[state['mode']]
        self.original.setToolTip(help_text)
        help_label=QLabel(help_text,self);help_label.setWordWrap(True)
        self.layout().insertWidget(0,help_label);self.layout().insertWidget(0,self.original)
        self.currentColorChanged.connect(lambda _:self.original.setChecked(False))


def choose_graphic_color(element,key,parent):
    from PySide6.QtWidgets import QDialog
    dialog=StudioColorDialog(graphic_color_state(element,key),parent)
    if dialog.exec()!=QDialog.DialogCode.Accepted:return None
    return graphic_color_changes(element,key,None if dialog.original.isChecked() else dialog.selectedColor().name())
