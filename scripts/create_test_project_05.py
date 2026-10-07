"""Create the reproducible five-style / five-slot hardware test project."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from s5studio.model import template,normalized_slot
from s5studio.render import render,png_bytes

p=template('Analogico')
p.name='S5 Analogico Libero'
p.author='S5 Studio'
p.background='#080f1b'
for e in p.elements:
    if e.kind=='analog' and not e.aod:
        e.x=e.y=36;e.width=e.height=408
        e.hour_length=25;e.minute_length=39;e.second_length=43
    elif e.name=='Firma':
        e.x=150;e.y=76;e.width=180;e.height=24;e.size=17;e.text='S5 LIBERO';e.color='#6ce5c1'
    elif e.kind=='date' and not e.aod:
        e.x=170;e.y=418;e.width=140;e.height=28;e.size=19

p.variants=[{'id':key,'name':name,'accent':color,'background':'#080f1b','imageAsset':'','overrides':{}}
            for key,name,color in [('mint','Menta','#6ce5c1'),('blue','Azzurro','#58aaff'),
                                   ('orange','Arancio','#ffb357'),('violet','Viola','#b790ff'),
                                   ('white','Bianco','#eaf1fa')]]
options=['none','healthStepCount','healthHeartRate','weatherCurrentTemperature','systemSensorCompass',
         'weatherCurrentWeather','systemStatusBattery','healthCalorieValue','healthOxygenSpO2',
         'healthSleepDuration','healthExerciseDuration','weatherCurrentHumidity','systemSensorAtmosphericPressure',
         'systemSensorFusionAltitude','healthStepKiloMeter']
for i,(x,y,w,h,default) in enumerate([(85,112,135,80,'healthStepCount'),(260,112,135,80,'healthHeartRate'),
                                    (32,242,128,78,'weatherCurrentTemperature'),(320,242,128,78,'systemSensorCompass'),
                                    (176,332,128,78,'weatherCurrentWeather')]):
    p.complications.append(normalized_slot({'id':f'slot{i+1}','name':f'Slot {i+1}','x':x,'y':y,
                                            'width':w,'height':h,'size':28,'background':'#101c2d',
                                            'options':options,'default':default}))
errors=p.validate()
if errors:raise ValueError('\n'.join(errors))
path=ROOT/'projects/S5_Analogico_Libero_0.5.s5faceproj'
p.save(path,png_bytes(render(p)))
for i in range(5):
    (ROOT/'docs/screenshots'/f'S5-Analogico-Libero-stile-{i+1}.png').write_bytes(png_bytes(render(p.variant_project(i))))
print(f'{path}\nID personale: {p.face_id}; cinque stili; cinque slot; quindici scelte per slot.')
