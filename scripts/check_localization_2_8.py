"""Exercise rendered Italian/English panels, sources and conditional controls."""
import json,os,sys,time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--disable-gpu'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from s5studio.web_ui import MainWindow
from s5studio.model import Element

app=QApplication([]);results={}
with TemporaryDirectory(dir=ROOT/'build',prefix='localization-audit-') as temporary:
    directory=Path(temporary)
    with patch('s5studio.web_ui.user_data_root',lambda:directory/'user'):
        w=MainWindow(smoke=True,settings_path=directory/'settings.json');w.show();page=w.view.page()
        def js(code):
            result=[];page.runJavaScript(code,result.append);deadline=time.monotonic()+25
            while not result and time.monotonic()<deadline:app.processEvents()
            if not result:raise RuntimeError(code[:200])
            return result[0]
        deadline=time.monotonic()+30
        while not js('Boolean(window.s5Ready&&state)') and time.monotonic()<deadline:app.processEvents()
        it=json.loads((ROOT/'locales/it.json').read_text(encoding='utf8'));en=json.loads((ROOT/'locales/en.json').read_text(encoding='utf8'))
        js('window.auditIt='+json.dumps(it,ensure_ascii=False)+';window.auditEn='+json.dumps(en,ensure_ascii=False)+';window.auditSources=[];true')
        # Collect original rendered text, not arbitrary JS implementation strings.
        collector="""(()=>{const found={};const skip='[data-i18n-skip],script,style,textarea,#project-title,#current-style,#editing-style,.user-content,select[data-preset],#compass-preset';const path=n=>n.id?'#'+n.id:n.parentElement?path(n.parentElement)+'/'+n.tagName+':'+Array.from(n.parentElement.children).indexOf(n):n.tagName;const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=walker.nextNode()){if(n.parentElement.closest(skip))continue;const text=n.nodeValue.trim();if(/[A-Za-zÀ-ž]/.test(text))found[path(n.parentElement)+'/text:'+Array.from(n.parentElement.childNodes).indexOf(n)]=text;}for(const n of document.querySelectorAll('[title],[placeholder],[aria-label],[alt]')){if(n.closest(skip))continue;for(const k of ['title','placeholder','aria-label','alt']){if(n.hasAttribute('data-i18n-'+k+'-skip'))continue;const text=(n.getAttribute(k)||'').trim();if(/[A-Za-zÀ-ž]/.test(text))found[path(n)+'/@'+k]=text;}}return found;})()"""
        def capture(name,code):
            js('S5I18n.configure("it",auditIt,auditIt);'+code+';S5I18n.apply();true')
            originals=json.loads(js('JSON.stringify('+collector+')'))
            js('S5I18n.configure("en",auditIt,auditEn);'+code+';S5I18n.apply();true')
            translated=json.loads(js('JSON.stringify('+collector+')'))
            results[name]=[[source,translated[key]] for key,source in originals.items() if key in translated]
        for tab in ('design','variants','slots','hands','disks','project'):capture('tab-'+tab,'setTab('+json.dumps(tab)+')')
        for kind in ('analog','pointer','compass','disk','clock','date','number','image','text','rect','circle','image_values'):
            data=Element(kind=kind,name='Custom Name').__dict__
            code='setTab("design");window.auditElement='+json.dumps(data,ensure_ascii=False)+';paintProperties(auditElement)'
            capture('kind-'+kind,code)
        for source in json.loads(js('JSON.stringify(Object.keys(state.pointerSources))')):
            code='auditElement='+json.dumps(Element(kind='pointer',name='Custom Name').__dict__)+';auditElement.source='+json.dumps(source)+';auditElement.pointer_arc=true;paintProperties(auditElement)'
            capture('pointer-'+source,code)
            capture('description-'+source,'document.getElementById("toast").textContent=state.sourceDescriptions['+json.dumps(source)+']||""')
        for source in ('dateMonth','dateWeek','dateMoon'):
            for short in (False,True):
                code='auditElement='+json.dumps(Element(kind='number',name='Custom Name').__dict__)+';auditElement.source='+json.dumps(source)+';auditElement.month_abbreviated='+json.dumps(short)+';paintProperties(auditElement)'
                capture('calendar-'+source+'-'+str(short),code)
        for status in ('rest','arming','ready','running','reading','stopped','resetting'):
            capture('chrono-'+status,'state.chronoState='+json.dumps(status)+';state.chronoElapsedMs=123456;paintChrono()')
        capture('hands-small','state.handSetDraft.small=true;paintHandSets()')
        capture('hands-shadows','state.handSetDraft.generateShadows=true;paintHandSets()')
        for source in ('timeHour','dateMoon','dateLunarDay'):
            capture('disk-source-'+source,'state.diskDraft.source='+json.dumps(source)+';paintDisks()')
        capture('disk-moon','state.diskDraft.source=state.moonSource;paintDisks()')
        capture('disk-sequence','state.diskDraft.mode="values";paintDisks()')
        capture('disk-shadows','state.diskDraft.generateShadows=true;paintDisks()')
        w.bridge.command('{"action":"add-slot"}');w.bridge.send(state=w.bridge.state())
        capture('complications-with-options','setTab("slots")')
        capture('complication-properties','setTab("design");paintProperties(state.layers.find(e=>e.kind==="complication"))')
        from io import BytesIO
        from PIL import Image
        import base64
        png=BytesIO();Image.new('RGBA',(20,100),(255,255,255,255)).save(png,format='PNG')
        item={'size':[20,100],'pivot':[10,90],'filename':'Custom Name.png',
              'preview':'data:image/png;base64,'+base64.b64encode(png.getvalue()).decode(),'offset':[2,3]}
        capture('hands-with-artwork','state.handSetDraft.hands.hour='+json.dumps(item)+';paintHandSets()')
        capture('hands-modify','state.handSetDraft.id="audit-only";paintHandSets()')
        capture('disks-with-artwork','state.diskDraft.hands["0"]='+json.dumps(item)+';diskFrame="0";paintDisks()')
        capture('disks-modify','state.diskDraft.id="audit-only";paintDisks()')
        w.close();w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
(ROOT/'build/localization-audit-2.8.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
missing={};mixed={}
import re
italian=re.compile(r'\b(?:Salva|Aggiorna|Importa|Sostituisci|Nessuna|Dato|Lancette|Rimuovi|Posizione|valori|valore|selezionati|visualizzati|livello|immagini|movimento|della|delle|dello|rimane|quadrante|Rotazione|Lettura|Calibrazione|Data attuale|Ombra|Spostamento|Mostra|nascondi)\b',re.I)
for context,pairs in results.items():
    for source,value in pairs:
        if source==value and italian.search(value):missing.setdefault(source,set()).add(context)
        elif source!=value and italian.search(value):mixed.setdefault((source,value),set()).add(context)
report={'applicationVersion':'2.8','status':'passed' if not missing and not mixed else 'failed',
        'contextsChecked':len(results),'renderedTextPairsChecked':sum(len(v) for v in results.values()),
        'contexts':list(results),'untranslatedLabels':sorted(missing),
        'mixedLanguageLabels':{source:value for source,value in mixed},
        'scope':'Rendered text and title/placeholder/aria-label/alt checks across six tabs, twelve element types, pointer sources/help, calendar, Chrono, sets, discs and complications. User-defined names and technical labels are excluded.',
        'sourceEditorTested':True,'executableLaunched':False,'watchfaceZipCreated':False}
(ROOT/'docs/localization-coverage-2.8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if missing or mixed:raise AssertionError('Untranslated or mixed-language labels detected.')
