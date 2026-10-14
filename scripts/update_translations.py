"""Extract Qt/HTML/JS messages, preserve catalogs, and optionally compile QM."""
import argparse
import ast
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
IDENTICAL_ENGLISH={'XIAOMI WATCH S5  ·  46 MM','Snap','Zoom','Scenario',
    '{v0}{v1} — S5 Studio {v2}','EasyFace Compiler 4.23','S5 Studio 2.8 — Xiaomi Watch S5',
    'Bluetooth','Ctrl+N','Ctrl+O','Ctrl+S','Ctrl+Shift+S','Ctrl+Y','Ctrl+Z',
    'Firmware','Font (px)','Fonts','Mi Fitness mod','SpO₂','Stress','PNG (*.png)',
    'S5 Studio 2.9 — Xiaomi Watch S5'}


def message(value):
    value=html.unescape(value).strip()
    visible=re.sub(r'\{\w+\}', '', value)
    if not visible or not re.search(r'[A-Za-zÀ-ž]',visible):return None
    if value.startswith(('[', '%','button[')) or re.search(r'\b(?:data-[\w-]+|type|id|min|max|step)=',value):return None
    if '\n' in value and re.search(r'QWidget\s*\{|QLabel#|font-family:',value):return None
    if value in ('use strict','button:not(:disabled)','input,textarea,select,[contenteditable=true]','input,textarea,select,button,[contenteditable=true]','input[type=color]'):return None
    if re.search(r'\b(?:card|controls)\b.*\bp-\d',value):return None
    if re.fullmatch(r'[a-zA-Z0-9_.:/#-]+',value) and not re.fullmatch(r'[A-ZÀ-Ž][a-zà-ž]+',value):return None
    if value.startswith(('.', '#', 'data:', 'qrc:', 'file:', 'http', 'assets/', 'text-', 'bg-', 'flex ', 'input ', 'btn ')):return None
    if re.search(r'[<>]|=>|\b(?:function|const|return)\b|\$\{',value):return None
    return value


class TextMessages(HTMLParser):
    def __init__(self,found):super().__init__(convert_charrefs=True);self.found=found;self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        for key,value in attrs:
            if key=='data-i18n' and value:self.found.add(html.unescape(value).strip());continue
            if key in ('title','alt','placeholder','aria-label','data-i18n') and value:
                item=message(value)
                if item:self.found.add(item)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
    def handle_data(self,value):
        if not self.skip:
            item=message(value)
            if item:self.found.add(item)


def js_strings(source):
    """Lex strings/templates including nested interpolation; never execute JS."""
    values=[];length=len(source)
    def code(i,closing=False):
        depth=1
        while i<length:
            c=source[i]
            if source.startswith('//',i):
                end=source.find('\n',i);i=length if end<0 else end;continue
            if source.startswith('/*',i):
                end=source.find('*/',i+2);i=length if end<0 else end+2;continue
            if c in "\"'`":i=string(i);continue
            if c=='/':
                before=source[:i].rstrip()
                if not before or before[-1] in '=(:,[!&|?{;' or before.endswith('return'):
                    i+=1;group=False
                    while i<length:
                        if source[i]=='\\':i+=2;continue
                        if source[i]=='[':group=True
                        if source[i]==']':group=False
                        if source[i]=='/' and not group:i+=1;break
                        i+=1
                    while i<length and source[i].isalpha():i+=1
                    continue
            if closing:
                if c=='{':depth+=1
                if c=='}':
                    depth-=1
                    if not depth:return i+1
            i+=1
        return i
    def string(i):
        quote=source[i];i+=1;parts=[];parameter=0
        while i<length:
            if source[i]=='\\':
                i+=1
                if i<length:parts.append({'n':'\n','t':'\t','r':'\r'}.get(source[i],source[i]));i+=1
                continue
            if source[i]==quote:values.append(''.join(parts));return i+1
            if quote=='`' and source.startswith('${',i):
                parts.append('{v'+str(parameter)+'}');parameter+=1;i=code(i+2,True);continue
            parts.append(source[i]);i+=1
        return i
    code(0)
    return values


def collect():
    found=set();qt_dynamic=set()
    TextMessages(found).feed((ROOT/'frontend/index.html').read_text(encoding='utf8'))
    for path in (ROOT/'frontend').glob('*.js'):
        if path.name=='i18n.js':continue
        for value in js_strings(path.read_text(encoding='utf8')):
            if '<' in value and '>' in value:TextMessages(found).feed(value)
            else:
                item=message(value)
                if item:found.add(item)
    for name in ['ui.py','web_ui.py','color_picker.py','source_help.py','motion.py','disk_catalog.py']:
        tree=ast.parse((ROOT/'s5studio'/name).read_text(encoding='utf8'))
        docstrings={id(part.body[0].value) for part in ast.walk(tree) if isinstance(part,(ast.Module,ast.ClassDef,ast.FunctionDef)) and part.body and isinstance(part.body[0],ast.Expr) and isinstance(part.body[0].value,ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and id(node) not in docstrings:
                item=message(node.value)
                if item:
                    found.add(item)
                    if name=='ui.py':qt_dynamic.add(item)
    # These presentation strings are composed by Python, so literals alone
    # cannot recover their final message boundaries.
    sys.path.insert(0,str(ROOT))
    from s5studio.render import SCENARIOS
    from s5studio.model import SOURCES
    from s5studio.source_help import source_choices
    from s5studio.moon_disk import LABEL as moon_label
    labels,descriptions=source_choices(SOURCES)
    found.update([*SCENARIOS,*labels.values(),*descriptions.values(),moon_label])
    # Preserve whole formatted validation/error messages shown by the bridge.
    # Placeholder values remain opaque (paths, project/layer names, IDs).
    for path in (ROOT/'s5studio').glob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            call=node.exc if isinstance(node,ast.Raise) else node if isinstance(node,ast.Call) else None
            if not isinstance(call,ast.Call) or not call.args:continue
            error=isinstance(call.func,ast.Name) and call.func.id in ('ValueError','FileNotFoundError','RuntimeError')
            validation=isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id in ('errors','issues') and call.func.attr=='append'
            progress=isinstance(call.func,ast.Name) and call.func.id in ('progress','notify')
            if not error and not validation and not progress:continue
            argument=call.args[0]
            if isinstance(argument,ast.JoinedStr):
                parts=[];index=0
                for part in argument.values:
                    if isinstance(part,ast.Constant):parts.append(str(part.value))
                    else:parts.append('{v'+str(index)+'}');index+=1
                item=message(''.join(parts))
            elif isinstance(argument,ast.Constant) and isinstance(argument.value,str):item=message(argument.value)
            else:item=None
            if item:found.add(item)
    library=ROOT/'data/watchface-library.json'
    if library.is_file():
        for value in json.loads(library.read_text(encoding='utf8')).get('sources',{}).values():
            if value.get('label'):found.add(value['label']);qt_dynamic.add(value['label'])
    return found,qt_dynamic


def update(compile_qm=False):
    found,dynamic=collect();locales=ROOT/'locales';locales.mkdir(exist_ok=True)
    def read(path):
        return json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
    italian={**read(locales/'it.json'),**{key:key for key in sorted(found)}}
    english={key:value for key,value in read(locales/'en.json').items()}
    for key in italian:english.setdefault(key,key)
    chinese={key:value for key,value in read(locales/'zh.json').items()}
    for key in italian:chinese.setdefault(key,key)
    catalogs={'it':italian,'en':english,'zh':chinese}
    # Changed placeholders must never be silently dropped by a translation.
    for language,catalog in catalogs.items():
        for key,value in catalog.items():
            if key in italian and set(re.findall(r'\{\w+\}',key))!=set(re.findall(r'\{\w+\}',value)):
                raise ValueError('Translation placeholders differ ('+language+'): '+key)
    for language,catalog in catalogs.items():
        (locales/(language+'.json')).write_text(json.dumps(dict(sorted(catalog.items())),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    target=ROOT/'translations';target.mkdir(exist_ok=True)
    supplement=target/'ui_strings.py'
    supplement.write_text('# Generated by scripts/update_translations.py; edit TS/JSON catalogs instead.\nfrom PySide6.QtCore import QT_TRANSLATE_NOOP\nMESSAGES = [\n'+
                          ''.join('    QT_TRANSLATE_NOOP("MainWindow", '+repr(value)+'),\n' for value in sorted(dynamic))+']\n',encoding='utf8')
    import PySide6
    qt=Path(PySide6.__file__).parent
    sources=[ROOT/'s5studio'/name for name in ['ui.py','web_ui.py','color_picker.py','file_dialogs.py']]+[supplement]
    suffix='.exe' if sys.platform=='win32' else ''
    subprocess.run([str(qt/('lupdate'+suffix)),*map(str,sources),'-source-language','it','-ts',
                    *[str(target/('s5studio_'+code+'.ts')) for code in catalogs]],check=True)
    for language,catalog in catalogs.items():
        path=target/('s5studio_'+language+'.ts');tree=ET.parse(path);tree.getroot().set('language','zh_CN' if language=='zh' else language);tree.getroot().set('sourcelanguage','it')
        for entry in tree.findall('.//message'):
            source=entry.findtext('source') or '';translation=entry.find('translation')
            if translation is None:translation=ET.SubElement(entry,'translation')
            if translation.get('type') in ('obsolete','vanished'):continue
            value=source if language=='it' else catalog.get(source,source[:len(source)-len(source.lstrip())]+catalog.get(source.strip(),source.strip())+source[len(source.rstrip()):])
            if language=='it' or not translation.text or translation.get('type')=='unfinished' or (language=='zh' and translation.text==source and value!=source):translation.text=value
            if language=='it' or value!=source or source in IDENTICAL_ENGLISH or source in ('Select Color','S5 Studio','Always On Display') or not re.search(r'[A-Za-zÀ-ž]',source):
                translation.attrib.pop('type',None)
            elif translation.text==source:translation.set('type','unfinished')
        ET.indent(tree,space='  ');tree.write(path,encoding='utf-8',xml_declaration=True)
        if compile_qm:subprocess.run([str(qt/('lrelease'+suffix)),str(path),'-qm',str(path.with_suffix('.qm'))],check=True)
    if compile_qm:
        for name in ('qtbase_it.qm','qtbase_zh_CN.qm'):
            qt_base=qt/'translations'/name
            if not qt_base.is_file():raise ValueError('Qt base translation missing: '+name)
            shutil.copy2(qt_base,target/name)
    result={'status':'passed','jsonMessages':len(italian),'englishMessagesDifferentFromSource':sum(english.get(k)!=k for k in italian),
            'chineseMessagesDifferentFromSource':sum(chinese.get(k)!=k for k in italian),
            'qtBaseTs':'translations/s5studio_it.ts','compiled':compile_qm,'existingCatalogEntriesPreserved':True}
    print(json.dumps(result,ensure_ascii=False,indent=2));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compile',action='store_true')
    update(parser.parse_args().compile)
