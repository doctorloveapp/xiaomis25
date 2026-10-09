"""Import a mother graphic, its original shadow and the matching clock set."""
import hashlib

HANDS=('hour','minute','second')

def clear_hand_changes(hand,asset=''):
    if hand not in HANDS:raise ValueError('Lancetta non valida.')
    return {hand+'_asset':asset,hand+'_anchor_x':-1,hand+'_anchor_y':-1,
            hand+'_preset':'',hand+'_shadow_asset':'',
            hand+'_shadow_anchor_x':-1,hand+'_shadow_anchor_y':-1,
            hand+'_shadow_offset_x':0,hand+'_shadow_offset_y':0,
            hand+'_length_adjusted':False,hand+'_width_adjusted':False,
            hand+'_pivot_reference_x':-1,hand+'_pivot_reference_y':-1}

def preset_changes(project,element,root,preset,hand,presets,*,custom_root=None,custom_catalog=None):
    if hand not in HANDS or element.kind not in ('analog','pointer'):
        raise ValueError('Seleziona una lancetta valida.')
    if element.kind=='pointer' and hand!='second':raise ValueError('La lancetta piccola usa una sola grafica.')
    if element.kind=='analog' and preset['hand']!=hand:raise ValueError('Modello non adatto a questa lancetta.')
    def import_bitmap(item,custom=False):
        if custom:
            from .hand_sets import HandSetCatalog
            from .paths import user_data_root
            path=(custom_catalog or HandSetCatalog(custom_root or user_data_root()/'hand-sets')).bitmap_path(item)
        else:
            path=(root/item['assetPath']).resolve()
            if not path.is_relative_to((root/'data/hand-presets').resolve()):
                raise ValueError('Percorso del modello non valido.')
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=item['sourceSha256']:raise ValueError('Immagine del modello di lancetta alterata.')
        key='assets/'+digest[:24]+'.png';project.assets[key]=raw
        return key
    chosen={hand:preset};by_id={p['id']:p for p in presets}
    if element.kind=='analog' and hand=='hour':
        for role,identity in preset.get('setMembers',{}).items():
            member=by_id.get(identity)
            if role in HANDS and member and member['hand']==role:chosen[role]=member
    changes={}
    for role,item in chosen.items():
        changes.update(clear_hand_changes(role,import_bitmap(item,item.get('custom',False))))
        changes.update({role+'_preset':item['id'],role+'_anchor_x':item['pivot'][0],role+'_anchor_y':item['pivot'][1],
                        role+'_pivot_reference_x':item['pivot'][0],role+'_pivot_reference_y':item['pivot'][1],
                        role+'_length_adjusted':True,
                        role+'_width_adjusted':True})
        shadow=item.get('shadow')
        if shadow:
            changes.update({role+'_shadow_asset':import_bitmap(shadow,item.get('custom',False)),
                            role+'_shadow_anchor_x':shadow['pivot'][0],role+'_shadow_anchor_y':shadow['pivot'][1],
                            role+'_shadow_offset_x':shadow['offset'][0],role+'_shadow_offset_y':shadow['offset'][1]})
    if element.kind=='analog' and hand=='hour':changes['second_hand']='second' in chosen and not element.aod
    if element.kind=='pointer' and preset.get('custom'):changes['pointer_end_pivot']=False
    return changes
