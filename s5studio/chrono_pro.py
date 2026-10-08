"""Editor simulation for the opt-in Crono-Pro; never touches user assets."""
import math
from .motion import pro_enabled, lua_element, lua_value
from .lua_runtime import pro_views


class ProPreview:
    duration=480

    def __init__(self):
        self.state='rest';self.elapsed=0;self.started=0;self.transition=None

    def bindings(self,project):
        return [v for e in project.elements if e.visible and not e.aod and lua_element(e) for v in pro_views(e)
                if v.source not in ('studioTimeHour','studioTimeMinute','studioDecisecond')]

    def values(self,project,now,civil):
        if self.state=='running':self.elapsed=max(self.elapsed,now-self.started)
        views=self.bindings(project);result={}
        for v in views:
            if v.source=='studioIntegratedSecond':
                value=civil if v.smooth_seconds else math.floor(civil)
                if self.state=='ready':value=0
                elif self.state in ('running','stopped'):value=math.floor(self.elapsed/1000)%60
            elif self.state in ('running','stopped'):
                value=lua_value(v.source,self.elapsed,False)
                if v.source=='studioChronoDecisecond':value=value/10*v.value_range
                value+=v.value_start
            else:value=v.value_start
            result[v.id]=value
        if self.transition:
            t=self.transition;fraction=min(1,max(0,(now-t['started'])/self.duration));eased=1-(1-fraction)**2
            for v in views:
                start=t['start'].get(v.id,v.value_start)
                destination=(civil if v.smooth_seconds else math.floor(civil)) if v.source=='studioIntegratedSecond' and self.state=='resetting' else v.value_start
                delta=destination-start
                if v.angle_range:
                    period=v.value_range*360/abs(v.angle_range)
                    direction=1 if v.angle_range>0 else -1
                    previous=t['targets'].get(v.id)
                    last=t['last'].get(v.id,start)
                    target=(start+direction*(direction*delta%period)) if previous is None else previous+(destination-previous+period/2)%period-period/2
                    while direction*(target-last)<-0.000001:target+=direction*period
                    t['targets'][v.id]=target;delta=target-start
                    candidate=start+delta*eased
                    if direction*(candidate-last)<0:candidate=last
                    t['last'][v.id]=candidate
                else:candidate=start+delta*eased
                result[v.id]=v.value_start+(candidate-v.value_start)%v.value_range if abs(v.angle_range)>=360 else candidate
            if fraction>=1:
                self.state='ready' if self.state=='arming' else 'rest';self.transition=None
                if self.state=='rest':self.elapsed=0
                return self.values(project,now,civil)
        return result

    def tap(self,project,now,civil):
        current=self.values(project,now,civil)
        if self.transition:return
        if self.state in ('rest','stopped'):
            self.state='arming' if self.state=='rest' else 'resetting'
            self.transition={'started':now,'start':current,'targets':{},'last':{}}
        elif self.state=='ready':self.started=now;self.elapsed=0;self.state='running'
        elif self.state=='running':self.state='stopped'

    def aod(self):
        if self.transition:
            self.state='ready' if self.state=='arming' else 'rest';self.transition=None
            if self.state=='rest':self.elapsed=0
