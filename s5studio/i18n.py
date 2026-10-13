"""Qt Linguist catalogs and the frontend's offline JSON message catalogs."""
import json
from PySide6.QtCore import QCoreApplication, QTranslator, QLocale, QLibraryInfo
from .paths import resource_root
from .settings import language_code


def load_catalog(language):
    root = resource_root() / 'locales'
    def read(code):
        try:
            value = json.loads((root / (code + '.json')).read_text(encoding='utf-8-sig'))
            return {k: v for k, v in value.items() if isinstance(v, str)} if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}
    base = read('it')
    return {**base, **read(language_code(language))}


def install_language(language, app=None):
    app = app or QCoreApplication.instance()
    if app is None:
        raise RuntimeError('Create QApplication before installing translations.')
    code = language_code(language)
    for translator in getattr(app, '_s5_translators', []):
        app.removeTranslator(translator)
        translator.deleteLater()
    installed = []
    # Native Qt button labels/file dialogs have their own upstream catalog.
    if code == 'it':
        qt = QTranslator(app)
        if qt.load(str(resource_root() / 'translations/qtbase_it.qm')) or qt.load(
                'qtbase_it', QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
            app.installTranslator(qt); installed.append(qt)
    if code != 'it':
        studio = QTranslator(app)
        if studio.load(str(resource_root() / ('translations/s5studio_' + code + '.qm'))):
            app.installTranslator(studio); installed.append(studio)
    app._s5_translators = installed  # QTranslator must outlive installTranslator().
    app._s5_language = code
    QLocale.setDefault(QLocale(code))
    return code
