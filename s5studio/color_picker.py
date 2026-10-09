"""One color dialog for every editor context, including an explicit no-color."""
import re
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


def choose_graphic_color(element,key,parent):
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QCheckBox,QColorDialog,QDialog
    state=graphic_color_state(element,key)
    dialog=QColorDialog(QColor(state['color']),parent)
    dialog.setWindowTitle('Select Color')
    dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog,True)
    original=QCheckBox('Nessun colore',dialog)
    original.setObjectName('studio-original-color');original.setChecked(state['original'])
    help_text={'original':'Mantieni i colori e la trasparenza originali della grafica.',
               'cap':'Nascondi soltanto il tappo centrale, mantenendo tutte le lancette.',
               'accent':'Non applicare un colore accento.',
               'fill':'Rendi trasparente questo colore.','hand':'Rendi trasparente la lancetta disegnata.'}[state['mode']]
    original.setToolTip(help_text)
    from PySide6.QtWidgets import QLabel
    help_label=QLabel(help_text,dialog);help_label.setWordWrap(True)
    dialog.layout().insertWidget(0,help_label)
    dialog.layout().insertWidget(0,original)
    dialog.currentColorChanged.connect(lambda _:original.setChecked(False))
    if dialog.exec()!=QDialog.DialogCode.Accepted:return None
    return graphic_color_changes(element,key,None if original.isChecked() else dialog.selectedColor().name())
