"""Atomic group transforms; a shared clamp preserves all relative offsets."""
from .model import Element, MAX_DESIGN_IMAGE_SIZE, normalized_slot


def layers(project, ids, variant, aod):
    if not isinstance(ids,list) or not ids or len(ids)!=len(set(ids)):raise ValueError('Selezione multipla non valida.')
    resolved=project.variant_project(0 if aod else variant)
    available={e.id:e for e in resolved.elements}
    available.update({s['id']:normalized_slot(s) for s in resolved.complications})
    result=[]
    for key in ids:
        if key not in available:raise ValueError('Livello selezionato non trovato.')
        e=available[key];get=lambda k:getattr(e,k) if isinstance(e,Element) else e[k]
        if (e.aod if isinstance(e,Element) else False)!=aod:raise ValueError('Seleziona livelli della stessa schermata.')
        if get('locked'):raise ValueError('Sblocca tutti i livelli selezionati prima di spostare il gruppo.')
        result.append((key,e))
    return result


def move(project, ids, dx, dy, variant=0, aod=False, variant_only=False):
    if any(type(v) is not int or abs(v)>8192 for v in (dx,dy)):raise ValueError('Spostamento gruppo non valido.')
    selected=layers(project,ids,variant,aod);bounds=[]
    for key,e in selected:
        bounds.append(e)
        if isinstance(e,Element) and not variant_only:
            bounds.append(next(x for x in project.elements if x.id==key))
            bounds.extend(next(x for x in project.variant_project(i).elements if x.id==key) for i in range(len(project.variants)))
    xmin=ymin=-8192;xmax=ymax=8192
    for e in bounds:
        get=lambda k:getattr(e,k) if isinstance(e,Element) else e[k]
        image=isinstance(e,Element) and e.kind=='image';low=-MAX_DESIGN_IMAGE_SIZE if image else 0
        xmin=max(xmin,low-get('x'));ymin=max(ymin,low-get('y'))
        xmax=min(xmax,(MAX_DESIGN_IMAGE_SIZE if image else max(0,480-get('width')))-get('x'))
        ymax=min(ymax,(MAX_DESIGN_IMAGE_SIZE if image else max(0,480-get('height')))-get('y'))
    if xmin>xmax or ymin>ymax:raise ValueError('Il gruppo non può essere spostato entro i limiti di tutte le varianti.')
    dx=max(xmin,min(xmax,dx));dy=max(ymin,min(ymax,dy))
    for key,e in selected:
        if not isinstance(e,Element):
            next(s for s in project.complications if s['id']==key).update(x=e['x']+dx,y=e['y']+dy)
        elif variant_only and not aod:
            project.variants[variant].setdefault('overrides',{}).setdefault(key,{}).update(x=e.x+dx,y=e.y+dy)
        else:
            base=next(x for x in project.elements if x.id==key);base.x+=dx;base.y+=dy
            for v in project.variants:
                override=v.get('overrides',{}).get(key,{})
                if 'x' in override:override['x']+=dx
                if 'y' in override:override['y']+=dy
    return dx,dy


def align(project,ids,alignment,variant=0,aod=False,variant_only=False):
    selected=layers(project,ids,variant,aod)
    def attr(e,k):return getattr(e,k) if isinstance(e,Element) else e[k]
    left=min(attr(e,'x') for _,e in selected);top=min(attr(e,'y') for _,e in selected)
    right=max(attr(e,'x')+attr(e,'width') for _,e in selected);bottom=max(attr(e,'y')+attr(e,'height') for _,e in selected)
    deltas={'left':(-left,0),'center-x':(round((480-left-right)/2),0),'right':(480-right,0),
            'top':(0,-top),'center-y':(0,round((480-top-bottom)/2)),'bottom':(0,480-bottom)}
    if alignment not in deltas:raise ValueError('Allineamento gruppo non valido.')
    return move(project,ids,*deltas[alignment],variant,aod,variant_only)
