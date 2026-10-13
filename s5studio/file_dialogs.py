"""Persistent last directory for each editor load/save category."""
import json
from pathlib import Path

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject


class RememberedDialogs(QObject):
    def __init__(self,parent,path):
        super().__init__(parent)
        self.parent=parent;self.path=Path(path)
        try:
            data=json.loads(self.path.read_text(encoding='utf8'))
            self.folders={k:v for k,v in data.items() if isinstance(v,str)} if isinstance(data,dict) else {}
        except (OSError,ValueError):self.folders={}

    def initial(self,category,fallback,*,save=False):
        fallback=Path(fallback)
        folder=Path(self.folders[category]) if category in self.folders else None
        if folder is None or not folder.is_dir():
            folder=fallback.parent if save else fallback
            while not folder.is_dir() and folder!=folder.parent:folder=folder.parent
        return str(folder/fallback.name if save else folder)

    def remember(self,category,selected,*,directory=False):
        if not selected:return
        folder=Path(selected) if directory else Path(selected).parent
        self.folders[category]=str(folder.resolve())
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.path.with_suffix('.tmp')
            temp.write_text(json.dumps(self.folders,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            temp.replace(self.path)
        except OSError:pass # Folder preferences must not interrupt the operation.

    def open(self,category,title,fallback,filters):
        selected,_=QFileDialog.getOpenFileName(self.parent,self.tr(title),self.initial(category,fallback),self.tr(filters))
        self.remember(category,selected)
        return selected

    def save(self,category,title,fallback,filters):
        selected,_=QFileDialog.getSaveFileName(self.parent,self.tr(title),self.initial(category,fallback,save=True),self.tr(filters))
        self.remember(category,selected)
        return selected

    def directory(self,category,title,fallback):
        selected=QFileDialog.getExistingDirectory(self.parent,self.tr(title),self.initial(category,fallback))
        self.remember(category,selected,directory=True)
        return selected
