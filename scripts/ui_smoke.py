"""Exercise the real Qt editor offscreen, and produce reviewable screenshots."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from s5studio.ui import MainWindow

app=QApplication([])
w=MainWindow()
# Recovery belongs to interactive sessions, not this test.
w.recovery_timer.stop()
w.clear_recovery=lambda:None
w.offer_recovery=lambda:None
w.show()
app.processEvents()
out=Path(__file__).resolve().parents[1]/'docs/screenshots'
out.mkdir(parents=True,exist_ok=True)
w.grab().save(str(out/'editor.png'))
clock=next(e for e in w.project.elements if e.kind=='clock')
w.select(clock.id)
old=(clock.x,clock.y)
QTest.mousePress(w.canvas,Qt.MouseButton.LeftButton,pos=QPoint(120,195))
QTest.mouseMove(w.canvas,QPoint(150,205),10)
QTest.mouseRelease(w.canvas,Qt.MouseButton.LeftButton,pos=QPoint(150,205))
app.processEvents()
assert (clock.x,clock.y)!=old
w.undo()
assert (next(e for e in w.project.elements if e.kind=='clock').x,next(e for e in w.project.elements if e.kind=='clock').y)==old
w.redo()
assert len(w.history)==1
w.undo()
w.add_combo.setCurrentText('Numero dinamico')
w.add_element()
assert w.selected_element().kind=='number'
w.fields['source'].setCurrentIndex(w.fields['source'].findData('steps'))
assert w.selected_element().source=='steps'
w.duplicate_element()
assert w.selected_element().name.endswith('copia')
w.delete_element()
w.undo()
assert any(e.name.endswith('copia') for e in w.project.elements)
w.create_aod()
assert w.project.aod_enabled
assert any(e.aod and e.kind=='clock' for e in w.project.elements)
w.grab().save(str(out/'aod.png'))
w.mode.setCurrentIndex(0)
w.scenario.setCurrentText('Dati assenti')
assert w.canvas.values['heartRate'] is None
print('Qt smoke: drag, undo/redo, source binding, duplicate/delete, AOD, simulation passed.')
w.dirty=False
w.recovery_timer.stop()
w.close()
