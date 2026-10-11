from pathlib import Path
from unittest.mock import patch

import pytest

from s5studio.file_dialogs import RememberedDialogs


def test_directory_history_survives_restart_and_separates_load_save_categories(tmp_path):
    fallback=tmp_path/'fallback';fallback.mkdir()
    images=tmp_path/'images';images.mkdir()
    projects=tmp_path/'projects';projects.mkdir()
    exports=tmp_path/'exports';exports.mkdir()
    settings=tmp_path/'user/dialog-paths.json'
    dialogs=RememberedDialogs(None,settings)
    with patch('s5studio.file_dialogs.QFileDialog.getOpenFileName',return_value=(str(images/'hand.png'),'')):
        assert dialogs.open('hand-image-open','Import',fallback,'PNG')==str(images/'hand.png')
    with patch('s5studio.file_dialogs.QFileDialog.getSaveFileName',return_value=(str(projects/'NASA.s5faceproj'),'')):
        dialogs.save('project-save','Save',fallback/'New.s5faceproj','S5')
    with patch('s5studio.file_dialogs.QFileDialog.getExistingDirectory',return_value=str(exports)):
        dialogs.directory('watchface-export','Export',fallback)
    reopened=RememberedDialogs(None,settings)
    assert reopened.initial('hand-image-open',fallback)==str(images)
    assert reopened.initial('project-save',fallback/'Different.s5faceproj',save=True)==str(projects/'Different.s5faceproj')
    assert reopened.initial('watchface-export',fallback)==str(exports)
    assert reopened.initial('project-open',fallback)==str(fallback)
    assert reopened.initial('preview-save',fallback/'preview.png',save=True)==str(fallback/'preview.png')


@pytest.mark.parametrize('kind',['open','save','directory'])
def test_cancel_preserves_folder_and_existing_settings(tmp_path,kind):
    settings=tmp_path/'paths.json';d=RememberedDialogs(None,settings)
    d.remember('category',str(tmp_path/'previous.png'));before=settings.read_bytes()
    name={'open':'getOpenFileName','save':'getSaveFileName','directory':'getExistingDirectory'}[kind]
    result='' if kind=='directory' else ('','')
    with patch('s5studio.file_dialogs.QFileDialog.'+name,return_value=result) as chooser:
        args=('category','Choose',tmp_path/'new.png','PNG') if kind!='directory' else ('category','Choose',tmp_path)
        assert getattr(d,kind)(*args)==''
        expected=tmp_path/'new.png' if kind=='save' else tmp_path
        assert chooser.call_args.args[2]==str(expected)
    assert settings.read_bytes()==before


def test_deleted_folder_and_corrupt_preferences_fall_back_to_existing_directory(tmp_path):
    settings=tmp_path/'paths.json';d=RememberedDialogs(None,settings)
    deleted=tmp_path/'deleted';deleted.mkdir();d.remember('project-save',deleted/'x.s5faceproj');deleted.rmdir()
    assert d.initial('project-save',tmp_path/'missing/New.s5faceproj',save=True)==str(tmp_path/'New.s5faceproj')
    settings.write_text('{broken',encoding='utf8')
    assert RememberedDialogs(None,settings).initial('image-open',tmp_path/'missing')==str(tmp_path)


def test_preferences_write_failure_does_not_interrupt_selected_operation(tmp_path):
    settings=tmp_path/'unwritable';settings.write_text('file',encoding='utf8')
    d=RememberedDialogs(None,settings/'paths.json')
    with patch('s5studio.file_dialogs.QFileDialog.getOpenFileName',return_value=(str(tmp_path/'image.png'),'')):
        assert d.open('image-open','Choose',tmp_path,'PNG')==str(tmp_path/'image.png')
