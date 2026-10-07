"""Observed sources and hand presets from the user's local corpus, not a SDK claim."""
from functools import lru_cache
import hashlib,json,re,struct
from pathlib import Path

SOURCE_LABELS={
 'weatherCurrentWeather':'Meteo · condizione','weatherCurrentTemperature':'Temperatura °C','weatherCurrentTemperatureFahrenheit':'Temperatura °F',
 'weatherTodayTemperatureMax':'Temperatura massima','weatherTodayTemperatureMin':'Temperatura minima','weatherCurrentHumidity':'Umidità',
 'weatherCurrentWindLevel':'Vento · intensità','weatherCurrentWindDirection':'Vento · direzione','weatherCurrentUVIndex':'Indice UV',
 'weatherCurrentAirQualityIndex':'Qualità aria','weatherCurrentPressure':'Pressione meteo',
 'systemSensorCompass':'Bussola · gradi','systemSensorFusionAltitude':'Altitudine','systemSensorAtmosphericPressure':'Pressione atmosferica',
 'healthHeartRate':'Pulsazioni','healthHeartRateMax':'Pulsazioni massime','healthHeartRateMin':'Pulsazioni minime','healthOxygenSpO2':'SpO₂',
 'healthStepCount':'Passi','healthStepTarget':'Obiettivo passi','healthStepProgress':'Progresso passi','healthStepKiloMeter':'Distanza passi',
 'healthCalorieValue':'Calorie','healthCalorieTarget':'Obiettivo calorie','healthCalorieProgress':'Progresso calorie',
 'healthExerciseProgress':'Progresso movimento','healthExerciseDuration':'Durata movimento','healthStandCount':'Ore in piedi',
 'healthStandProgress':'Progresso ore in piedi','healthSleepDuration':'Durata sonno','healthSleepTargetProgress':'Progresso sonno','healthPressureIndex':'Stress',
 'dateMonth':'Mese','dateDay':'Giorno','dateWeek':'Giorno settimana','dateYear':'Anno','dateLunarDay':'Giorno lunare',
 'dateLunarStringMonth':'Mese lunare','dateLunarStringDay':'Data lunare','dateMoon':'Fase lunare',
 'timeHour':'Ore','timeMinute':'Minuti','timeSecond':'Secondi','systemStatusBattery':'Batteria','systemStatusBluetooth':'Bluetooth',
 'miscdateYestarday':'Data precedente','miscdateTomorrow':'Data successiva',
 'dateDayLow':'Giorno · unità','dateDayHigh':'Giorno · decine',
 'timeHourHigh':'Ore · decine','timeHourLow':'Ore · unità',
 'timeMinuteHigh':'Minuti · decine','timeMinuteLow':'Minuti · unità',
 'timeSecondHigh':'Secondi · decine','timeSecondLow':'Secondi · unità',
 'weatherCurrentSunRiseHour':'Alba · ore','weatherCurrentSunRiseMinute':'Alba · minuti',
 'weatherCurrentSunSetHour':'Tramonto · ore','weatherCurrentSunSetMinute':'Tramonto · minuti',
 'miscIsPM':'Pomeriggio (PM)','miscTimeSection':'Fascia oraria',
}


def directory_stride(data):
    entry=168+4*(data[24]+data[29]);count=data[28]
    if not count:raise ValueError('Zero schermate.')
    first=struct.unpack_from('<I',data,entry+12)[0]
    protocol=struct.unpack_from('<I',data,16)[0]
    if first==entry+88*count:stride=88
    elif protocol in (0x900,0x903):stride=176
    elif protocol==0x800 and first>=entry+160*count:stride=160
    else:raise ValueError('Directory binaria non riconosciuta.')
    return entry,stride

def directory_bases(data):
    entry,stride=directory_stride(data);bases=[];pos=entry
    for _ in range(data[28]):
        if pos+stride>len(data):raise ValueError('Directory troncata.')
        bases.append(pos)
        # Vendor theme tail: palette bytes aligned to four, with AOD in bit 0.
        extra=struct.unpack_from('<I',data,pos+stride-4)[0]&~3 if stride!=88 else 0
        if extra>4096:raise ValueError('Palette del tema fuori limite.')
        pos+=stride+extra
    return bases

def read_tables(data,screen=0):
    entry,stride=directory_stride(data);base=directory_bases(data)[screen]
    result=[[] for _ in range(12)]
    for index in range(12 if stride==176 else 10):
        count,offset=struct.unpack_from('<II',data,base+8+index*8)
        if count>10000 or offset+count*16>len(data):raise ValueError('Tabella fuori dal binario.')
        for row in range(count):
            uid,flags,pos,length=struct.unpack_from('<IIII',data,offset+16*row)
            if pos+length>len(data):raise ValueError('Risorsa fuori dal binario.')
            result[index].append((uid,flags,data[pos:pos+length]))
    return result


def resource_path(base:Path,src:str):
    if not src or Path(src).is_absolute() or '..' in Path(src).parts:raise ValueError('Percorso risorsa non valido.')
    path=base/'resources'/src
    if path.is_file():return path
    encoded=''.join(f'#U{ord(c):04x}' if ord(c)>127 else c for c in src)
    path=base/'resources'/encoded
    if path.is_file():return path
    raise ValueError('Risorsa mancante: '+src)


def create_library(root:Path,catalog:dict):
    sources={};errors=[]
    for face in catalog['watchfaces']:
        base=root/face['base'];binary_path=base/'resource.bin'
        if not binary_path.exists():continue
        data=binary_path.read_bytes()
        try:
            entry,stride=directory_stride(data)
            resources={}
            for n in range(data[28]):
                for index,rows in enumerate(read_tables(data,n)):
                    for uid,flags,payload in rows:resources[uid]=(index,payload)
            mapping={name:int(uid,16) for name,uid in re.findall(r'^([^:\r\n]+):\s*([a-fA-F0-9]+)\s*$',(base/'uidmap.map').read_text(encoding='utf-8'),re.M)}
        except Exception as exc:errors.append({'face':face['folder'],'error':str(exc)});continue
        for node in face['resources']:
            source=node.get('source');uid=mapping.get(node.get('name'))
            if not source or uid not in resources or resources[uid][0]!=7:continue
            payload=resources[uid][1]
            code=payload[:2].hex().upper()
            item=sources.setdefault(source,{'label':SOURCE_LABELS.get(source,source),'codes':{},'evidence':[]})
            item['codes'][code]=item['codes'].get(code,0)+1
            item['evidence'].append({'face':face['folder'],'resource':node['name'],'type':node['tag'],'uid':hex(uid),'code':code})
    for source,item in sources.items():
        item['code']=max(item['codes'],key=item['codes'].get)
        # Digit subfields have a fixed binding, independently confirmed in the
        # other faces. LLATH reuses resource names in several uidmap sections.
        explicit={'timeHourHigh':'0A11','timeHourLow':'0911','timeMinuteHigh':'1211','timeMinuteLow':'1111'}
        if source in explicit and explicit[source] in item['codes']:item['code']=explicit[source]
        item['bindingStatus']='observed-in-user-corpus'
    weather={}
    for face in catalog['watchfaces']:
        weather_node=next((n for n in face['resources'] if n.get('source')=='weatherCurrentWeather' and n['tag']=='DataItemImageValues'),None)
        if not weather_node:continue
        array=next((n for n in face['resources'] if n.get('name')==weather_node.get('ref','')[1:]),None)
        if not array:continue
        for choice,image in zip(weather_node['items'],array['items']):
            bitmap=resource_path(root/face['base'],image['src']).read_bytes()
            digest=hashlib.sha256(bitmap).hexdigest();target=root/'data/weather-presets'/f'{digest[:24]}.png'
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bitmap)
            weather[choice['value']]={'path':str(target.relative_to(root)),'sha256':digest,'face':face['folder']}
        break
    from .hand_catalog import extract_hand_models
    hands,hand_report=extract_hand_models(root,catalog)
    errors+=hand_report['errors']
    result={'schemaVersion':2,'sources':sources,'hands':hands,'handCatalogSummary':{k:v for k,v in hand_report.items() if k not in ('coverage','errors')},'weatherIcons':weather,'errors':errors,'watchfaceCount':len(catalog['watchfaces'])}
    target=root/'data/watchface-library.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    from .compass_catalog import create_compass_catalog
    create_compass_catalog(root,result)
    return result


@lru_cache(maxsize=1)
def library():
    from .paths import resource_root
    root=resource_root()
    path=root/'data/watchface-library.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'sources':{},'hands':[]}
