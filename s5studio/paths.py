"""Read-only bundled resources and writable user documents are separate."""
from pathlib import Path
import os
import sys


def resource_root():
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def application_root():
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else resource_root()


def user_data_root():
    if not getattr(sys, 'frozen', False):
        return resource_root() / 'data'
    return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local')) / 'S5Studio'


def default_compiler():
    return resource_root() / 'tools/easyface-4.23/Compiler.exe'
