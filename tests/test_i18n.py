import json
import os
from pathlib import Path
from unittest.mock import patch
import pytest

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from s5studio.settings import AppSettings,language_code
from s5studio.i18n import load_catalog,install_language

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('contents',[None,'{broken','[]','null','{"language":"unknown"}'])
def test_default_italian_and_corrupt_settings_do_not_block_startup(tmp_path,contents):
    path=tmp_path/'settings.json'
    if contents is not None:path.write_text(contents,encoding='utf8')
    assert AppSettings(path).language=='it'


@pytest.mark.parametrize('value,expected',[('en','en'),('en-GB','en'),('it_IT','it'),('de','it'),(None,'it')])
def test_language_normalization(value,expected):
    assert language_code(value)==expected


def test_settings_merge_retains_compiler_unknown_preferences_and_external_updates(tmp_path):
    path=tmp_path/'settings.json'
    path.write_text(json.dumps({'compiler':'C:/tools/Compiler.exe','custom':'keep'}),encoding='utf8')
    settings=AppSettings(path)
    settings.update(language='en')
    assert AppSettings(path).language=='en'
    other=AppSettings(path);other.update(custom='new')
    settings.update(language='it')
    assert json.loads(path.read_text())=={'compiler':'C:/tools/Compiler.exe','custom':'new','language':'it'}
    assert settings.compiler(None)==Path('C:/tools/Compiler.exe')
    settings.values['compiler']={}
    assert settings.compiler('default')=='default'


def test_failed_or_invalid_settings_write_does_not_replace_preferences(tmp_path):
    settings=AppSettings(tmp_path/'settings.json');settings.update(language='it');before=settings.path.read_bytes()
    with pytest.raises(ValueError):settings.update(language='../../evil')
    with patch.object(Path,'replace',side_effect=OSError('read-only')):
        with pytest.raises(OSError):settings.update(language='en')
    assert settings.path.read_bytes()==before and settings.language=='it'


def test_json_catalogs_preserve_source_text_placeholders_and_italian_fallback():
    it=load_catalog('it');en=load_catalog('en')
    assert len(it)>700 and set(it)==set(en)
    assert all(k==v for k,v in it.items())
    assert en['Salva progetto']=='Save project' and en['Movimento Fluido']=='Smooth Motion'
    assert en['{v0} livelli selezionati']=='{v0} selected layers'
    assert load_catalog('../../evil')==it


def test_qt_linguist_catalog_switch_and_color_dialog():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
    from s5studio.color_picker import StudioColorDialog
    app=QApplication.instance() or QApplication([])
    try:
        install_language('en',app)
        assert QCoreApplication.translate('MainWindow','Annulla')=='Undo'
        assert QCoreApplication.translate('StudioBridge','Salva progetto')=='Save project'
        dialog=StudioColorDialog({'color':'#112233','original':False,'mode':'original'},None)
        assert dialog.original.text()=='No color'
        dialog.deleteLater()
        install_language('it',app)
        assert QCoreApplication.translate('MainWindow','Annulla')=='Annulla'
    finally:install_language('it',app)


def test_lua_runtime_is_unchanged_from_tested_2_7():
    import hashlib
    manifest=json.loads((ROOT/'docs/runtime-manifest-2.7.json').read_text(encoding='utf8'))
    for path in (ROOT/'s5studio/lua').glob('*.lua'):
        assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['files'][path.relative_to(ROOT).as_posix()]


def test_legacy_qt_editor_uses_translated_text_and_stable_combo_ids(tmp_path):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication,QEvent
    from s5studio.ui import MainWindow
    app=QApplication.instance() or QApplication([])
    (tmp_path/'settings.json').write_text('{"language":"en"}',encoding='utf8')
    with patch('s5studio.settings.user_data_root',lambda:tmp_path):
        window=MainWindow()
        try:
            assert window.template_combo.itemText(0)=='Digital'
            assert window.template_combo.itemData(0)=='Digitale'
            window.add_combo.setCurrentIndex(window.add_combo.findData('Data'))
            assert window.add_combo.currentText()=='Date'
            assert window.add_combo.currentData()=='Data'
            window.add_element()
            assert window.project.elements[-1].kind=='date'
        finally:
            window.dirty=False;window.close();window.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            install_language('it',app)
