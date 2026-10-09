"""English dynamic calendars and native numeric right/centre alignment."""
from dataclasses import replace
from pathlib import Path
import os
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET
import pytest
from PIL import Image
from s5studio.calendar_labels import WEEKDAYS, MONTHS, labels_for, sample_label
from s5studio.model import Project, Element, SOURCES
from s5studio.render import SCENARIOS, element_image, static_image, png_bytes, digit_metrics, number_parts, layout_errors
from s5studio.native import generate_fprj
from s5studio.native_graph import collect_nodes
from s5studio.watchface_library import read_tables

ROOT = Path(__file__).resolve().parents[1]


def test_all_weekdays_and_months_use_observed_native_mapping_and_default_mon():
    week = Element(kind='number', source='dateWeek')
    month = Element(kind='number', source='dateMonth')
    assert WEEKDAYS == ('SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')
    assert all(sample_label(week, {'dateWeek': i}) == word for i, word in enumerate(WEEKDAYS))
    assert sample_label(week, SCENARIOS['Normale']) == 'MON'
    assert MONTHS == ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
    assert all(sample_label(month, {'dateMonth': i}) == word for i, word in enumerate(MONTHS, 1))
    assert sample_label(replace(month, source='month'), {'dateMonth': 9}) == 'September'
    assert sample_label(month, {'month': 10}) == 'October'
    assert sample_label(week, {'dateWeek': None}) == sample_label(month, {'dateMonth': 13}) == '---'
    assert not labels_for(replace(month, kind='pointer'))
    assert not labels_for(replace(month, kind='date'))


@pytest.mark.parametrize('source,value,word', [('dateWeek', 1, 'MON'), ('dateMonth', 9, 'September'), ('month', 12, 'December')])
@pytest.mark.parametrize('align', ['left', 'center', 'right'])
def test_preview_honours_font_colour_opacity_alignment_and_names(source, value, word, align):
    project = Project()
    e = Element(kind='number', source=source, width=300, height=60, size=32, bold=True,
                color='#1234ff', opacity=127, align=align, digits=1, decimals=2, leading_zero=True)
    actual = element_image(project, e, {source: value})
    expected = static_image(project, replace(e, kind='text', text=word))
    assert png_bytes(actual) == png_bytes(expected)
    assert actual.getchannel('A').getextrema()[1] == 127


@pytest.mark.parametrize('align', ['left', 'center', 'right'])
def test_single_day_digit_aligns_to_same_units_position_as_two_digit_day(align):
    project = Project()
    e = Element(kind='number', source='dateDay', digits=2, width=148, height=46, size=30, align=align)
    single = element_image(project, e, {'dateDay': 6})
    double = element_image(project, e, {'dateDay': 16})
    cw, ch, _ = digit_metrics(project, e)
    if align == 'right':
        assert single.getbbox()[0] >= e.width - cw
        assert single.crop((e.width-cw, 0, e.width, e.height)).tobytes() == double.crop((e.width-cw, 0, e.width, e.height)).tobytes()
    elif align == 'left':
        assert single.getbbox()[2] <= cw
    else:
        assert abs((single.getbbox()[0]+single.getbbox()[2])/2-e.width/2) <= 1
    padded = element_image(project, replace(e, leading_zero=True), {'dateDay': 6})
    assert padded.getbbox()[2]-padded.getbbox()[0] > single.getbbox()[2]-single.getbbox()[0]


def test_calendar_layout_checks_longest_name_and_roundtrip_keeps_numeric_day(tmp_path):
    p = Project(elements=[Element(kind='number', source='dateMonth', width=70, height=46, size=30)])
    assert layout_errors(p)
    p.elements[0].width = 300
    assert not layout_errors(p)
    p.elements.append(Element(kind='number', source='dateDay', digits=2, align='right', width=148, height=46, size=30))
    p.save(tmp_path/'calendar.s5faceproj')
    assert Project.load(tmp_path/'calendar.s5faceproj').metadata() == p.metadata()
    source = generate_fprj(p, tmp_path/'source')
    widgets = [w for w in ET.parse(source.project_path).iter('Widget') if w.get('Shape') in ('31','32')]
    assert [w.get('Shape') for w in widgets] == ['31','32']
    assert widgets[1].get('Alignment') == '2' and widgets[1].get('Blanking') == '1'


def test_real_compiler_calendar_names_values_and_numeric_alignment(tmp_path):
    """One temporary binary validates native binding; no demo ZIP is created."""
    week = Element(kind='number', source='dateWeek', x=20, y=20, width=130, height=48, size=30)
    month = Element(kind='number', source='dateMonth', x=20, y=80, width=300, height=48, size=30)
    days = [Element(kind='number', source='dateDay', x=50, y=180+i*50, width=148, height=46, size=30, digits=2, align=a)
            for i,a in enumerate(('left','center','right'))]
    date = Element(kind='date', x=50, y=350, width=230, height=46, size=30)
    p = Project(elements=[week, month, *days, date, replace(week, id='aodweek', aod=True)], aod_enabled=True)
    source = generate_fprj(p, tmp_path/'source')
    runtime = tmp_path/'runtime';runtime.mkdir()
    for name in ('Compiler.exe','DeviceInfo.db'):
        shutil.copy2(ROOT/'tools/easyface-4.23'/name, runtime/name)
    output=tmp_path/'compiled';output.mkdir()
    env=dict(os.environ);env['PATH']=str(Path(os.environ.get('WINDIR','C:/Windows'))/'System32')
    result=subprocess.run([str(runtime/'Compiler.exe'),'-b',str(source.project_path),str(output),'calendar.face','167210065'],
                          cwd=runtime,env=env,capture_output=True,stdin=subprocess.DEVNULL,timeout=30,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0 and b'No Errors' in result.stdout+result.stderr
    data=(output/'calendar.face').read_bytes()
    tables=read_tables(data,0);nodes=collect_nodes(data,0,source.project_path)
    dynamic=[(uid,b) for uid,_,b in tables[7]]
    for (uid,b),e in zip(dynamic[:2],(week,month)):
        assert b[:2].hex().upper()==SOURCES[e.source][1]
        expected=labels_for(e)
        assert list(struct.unpack_from('<'+'i'*len(expected),b,16))==list(expected)
        assert nodes[uid]['values']==list(expected) and nodes[uid]['attrs']['source']==e.source
        array=nodes[struct.unpack_from('<I',b,8)[0]]
        for bitmap,word in zip(array['bitmaps'],expected.values()):
            from s5studio.render import calendar_image
            assert bitmap==png_bytes(calendar_image(p,e,word))
    layouts={struct.unpack_from('<I',b)[0]:struct.unpack_from('<hh',b,4) for _,_,b in tables[0]}
    for (uid,b),e in zip(dynamic[2:5],days):
        assert b[3]&3=={'left':1,'center':2,'right':0}[e.align]
        assert not b[3]&4 and nodes[uid]['attrs']['align']==e.align
        cw,_,_=digit_metrics(p,e);(_,count,x,y),=number_parts(p,e)[0]
        anchor={'left':0,'center':count*cw//2,'right':count*cw}[e.align]
        assert layouts[uid]==(e.x+x+anchor,e.y+y)
    assert all(nodes[uid]['tag']=='DataItemImageNumber' for uid,_ in dynamic[5:])
    aod_nodes=collect_nodes(data,1,tmp_path/'source/AOD/quadrante.fprj')
    assert any(n['tag']=='DataItemImageValues' and n['attrs']['source']=='dateWeek' for n in aod_nodes.values())
