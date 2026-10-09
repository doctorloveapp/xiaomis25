"""Complications drawn and compiled from the same original Studio components."""
from io import BytesIO
import hashlib
from PIL import Image,ImageDraw
from .model import Project,Element,SOURCES,normalized_slot

ALIASES={'hour':'timeHour','minute':'timeMinute','second':'timeSecond','day':'dateDay','month':'dateMonth','batteryPercent':'systemStatusBattery','heartRate':'healthHeartRate','steps':'healthStepCount','calories':'healthCalorieValue','spo2':'healthOxygenSpO2','sleep':'healthSleepDuration','movement':'healthExerciseDuration'}
UNITS={'healthHeartRate':'bpm','healthHeartRateMax':'bpm','healthHeartRateMin':'bpm','weatherCurrentTemperature':'°C','weatherTodayTemperatureMax':'°C','weatherTodayTemperatureMin':'°C','weatherCurrentTemperatureFahrenheit':'°F','systemSensorCompass':'°','systemStatusBattery':'%','healthOxygenSpO2':'%','healthCalorieValue':'kcal','healthCalorieTarget':'kcal','weatherCurrentHumidity':'%','systemSensorFusionAltitude':'m','systemSensorAtmosphericPressure':'hPa','healthSleepDuration':'min','healthExerciseDuration':'min'}
SAMPLES={'weatherCurrentTemperature':22,'weatherCurrentTemperatureFahrenheit':72,'weatherTodayTemperatureMax':26,'weatherTodayTemperatureMin':14,'weatherCurrentHumidity':65,'weatherCurrentUVIndex':4,'weatherCurrentAirQualityIndex':38,'weatherCurrentWindLevel':3,'weatherCurrentWindDirection':180,'weatherCurrentWeather':1,'systemSensorCompass':135,'systemSensorFusionAltitude':180,'systemSensorAtmosphericPressure':1013,'healthOxygenSpO2':98,'healthSleepDuration':420,'healthExerciseDuration':35,'healthStandCount':8,'healthPressureIndex':24,'healthHeartRateMax':110,'healthHeartRateMin':58,'dateYear':2026}

def label(key):
    return 'Nessuna' if key=='none' else SOURCES[key][0]

UNITS.update(healthSleepDuration='h',healthStepKiloMeter='km')
SAMPLES.update(healthSleepDuration=8.3,healthStepKiloMeter=4.25,dateWeek=1)

def sample_values(values):
    result=dict(SAMPLES)
    if values.get('batteryPercent',0) is None:result={k:None for k in result}
    for key,value in values.items():result[ALIASES.get(key,key)]=value
    for alias,key in ALIASES.items():result[alias]=result.get(key)
    return result

def option_project(slot,key):
    from .render import png_bytes,system_font,digit_metrics
    from .colors import color_rgba
    s=normalized_slot(slot);w,h=s['width'],s['height']
    p=Project(name=label(key),background='#000000',aod_enabled=False,variants=[],complications=[])
    bitmap=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(bitmap)
    if key!='none':
        if s['frame']=='circle':draw.ellipse((1,1,w-2,h-2),fill=color_rgba(s['background']),outline=color_rgba(s['color']),width=2)
        elif s['frame']=='rounded':draw.rounded_rectangle((1,1,w-2,h-2),radius=min(16,h//4),fill=color_rgba(s['background']),outline=color_rgba(s['color']),width=1)
        title=label(key).split(' · ')[0]
        font=system_font(min(13,max(9,h//6)),False)
        while font.getlength(title)>w-10 and len(title)>3:title=title[:-2]+'…'
        if s['showLabel']:
            box=font.getbbox(title);draw.text(((w-font.getlength(title))/2,6-box[1]),title,font=font,fill=color_rgba(s['color']))
        unit=s['unit'] or UNITS.get(ALIASES.get(key,key),'%' if key.endswith('Progress') else '')
        if unit and s['showUnit']:
            box=font.getbbox(unit);draw.text(((w-font.getlength(unit))/2,h-16-box[1]),unit,font=font,fill='#a3b0c2')
    if bitmap.getbbox() or key=='none':
        data=png_bytes(bitmap);asset='assets/'+hashlib.sha256(data).hexdigest()[:24]+'.png';p.assets[asset]=data
        p.elements.append(Element(kind='image',name='Cornice',asset=asset,x=0,y=0,width=w,height=h,opacity=s['opacity']))
    top=22 if s['showLabel'] else 0
    bottom=18 if s['showUnit'] else 0
    if key=='weatherCurrentWeather' and s['weatherMode']=='icon':
        from .watchface_library import library
        import sys
        from pathlib import Path
        from .paths import resource_root
        root=resource_root()
        frames={}
        for value,icon in library().get('weatherIcons',{}).items():
            raw=(root/icon['path']).read_bytes();name='assets/'+hashlib.sha256(raw).hexdigest()[:24]+'.png';p.assets[name]=raw;frames[value]=name
        if not frames:raise ValueError('Libreria icone meteo non disponibile.')
        p.elements.append(Element(kind='image_values',name='Icona meteo',source=key,value_assets=frames,x=0,y=top,width=w,height=h-top-bottom,opacity=s['opacity']))
    elif key!='none':
        decimals=s['decimals'] if s['decimals']>=0 else {'healthSleepDuration':1,'healthStepKiloMeter':2}.get(ALIASES.get(key,key),0)
        digits=s['digits'] or max(SOURCES[key][2],decimals+3 if decimals else 1)
        if decimals and digits<decimals+2:raise ValueError('Aumenta il numero di cifre per includere i decimali.')
        e=Element(kind='number',name=label(key),source=key,digits=digits,decimals=decimals,size=s['size'],color=s['color'],x=0,y=top,width=w,height=h-top-bottom,opacity=s['opacity'],align=s['align'])
        from .calendar_labels import labels_for
        from .render import calendar_metrics
        def dimensions():
            return calendar_metrics(p,e) if labels_for(e) else (e.digits*digit_metrics(p,e)[0],digit_metrics(p,e)[1])
        while e.size>8 and (dimensions()[0]>e.width or dimensions()[1]>e.height):e.size-=1
        p.elements.append(e)
    return p

def option_image(slot,key,values):
    from .render import element_image
    s=normalized_slot(slot);p=option_project(s,key);im=Image.new('RGBA',(s['width'],s['height']))
    for e in p.elements:im.alpha_composite(element_image(p,e,sample_values(values)),(e.x,e.y))
    return im
