from PyQt6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np

from dsp.utils import H_eval


class PoleZeroEditor(pg.GraphicsLayoutWidget):
    updated = QtCore.pyqtSignal()

    def __init__(self, mode_provider=None):
        super().__init__()
        self.mode_provider = mode_provider  # callable returning 'select'|'add_zero'|'add_pole'|'delete'

        # Plot setup
        self.plot = self.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setXRange(-1.4, 1.4)
        self.plot.setYRange(-1.4, 1.4)
        theta = np.linspace(0, 2 * np.pi, 400)
        self.unit_circle = pg.PlotDataItem(
            np.cos(theta), np.sin(theta), pen=pg.mkPen((180, 180, 180), width=1)
        )
        self.plot.addItem(self.unit_circle)

        # Data (store both members of complex conjugate pair explicitly)
        self.zeros: list[complex] = []
        self.poles: list[complex] = []

        # Scatter items
        self.zero_scatter = pg.ScatterPlotItem(
            size=12, pen=pg.mkPen('c', width=2), brush=None, symbol='o'
        )
        self.pole_scatter = pg.ScatterPlotItem(
            size=14, pen=pg.mkPen('m', width=2), brush=None, symbol='x'
        )
        self.plot.addItem(self.zero_scatter)
        self.plot.addItem(self.pole_scatter)

        # Interaction state
        self.dragging_point: tuple[str, int] | None = None  # (type, index)
        self.selected: tuple[str, int] | None = None

        # Connect mouse events via scene
        self.plot.scene().sigMouseClicked.connect(self.on_click)
        self.plot.scene().sigMouseMoved.connect(self.on_move)

    # ---------- Helpers ----------
    def update_scatter(self):
        self.zero_scatter.setData(
            [z.real for z in self.zeros], [z.imag for z in self.zeros]
        )
        self.pole_scatter.setData(
            [p.real for p in self.poles], [p.imag for p in self.poles]
        )
        self.updated.emit()

    def snap_unit(self, c: complex):
        r = abs(c)
        if r == 0:
            return c
        return c / r

    def screen_to_complex(self, pos):
        vb = self.plot.vb
        p = vb.mapSceneToView(pos)
        return complex(p.x(), p.y())

    def find_near(self, c: complex, tol=0.06):
        best = None
        found = None
        for i, z in enumerate(self.zeros):
            d = abs(c - z)
            if d < tol and (best is None or d < best):
                best = d
                found = ('zero', i, d)
        for i, p in enumerate(self.poles):
            d = abs(c - p)
            if d < tol and (best is None or d < best):
                best = d
                found = ('pole', i, d)
        return found

    # ---------- Conjugate pair handling ----------
    def add_zero_pair(self, c: complex, tol=1e-9):
        # Ensure we store positive imaginary first
        if abs(c.imag) <= tol:
            self.zeros.append(complex(c.real, 0.0))
        else:
            if c.imag < 0:
                c = c.conjugate()
            self.zeros.append(c)
            self.zeros.append(c.conjugate())

    def conjugate_index(self, idx: int, tol=1e-9):
        if not (0 <= idx < len(self.zeros)):
            return None
        z = self.zeros[idx]
        if abs(z.imag) <= tol:
            return None
        for j, w in enumerate(self.zeros):
            if j != idx and abs(w - z.conjugate()) < tol:
                return j
        return None

    def move_zero_pair(self, idx: int, new_c: complex, tol=1e-9):
        if not (0 <= idx < len(self.zeros)):
            return
        cj = self.conjugate_index(idx, tol)
        if abs(new_c.imag) <= tol:  # collapse to real
            real_c = complex(new_c.real, 0.0)
            if cj is not None:
                hi, lo = max(idx, cj), min(idx, cj)
                self.zeros.pop(hi)
                if lo >= len(self.zeros):  # just in case
                    self.zeros.append(real_c)
                else:
                    self.zeros[lo] = real_c
            else:
                self.zeros[idx] = real_c
        else:
            if new_c.imag < 0:
                new_c = new_c.conjugate()
            self.zeros[idx] = new_c
            if cj is None:
                self.zeros.append(new_c.conjugate())
            else:
                self.zeros[cj] = new_c.conjugate()

    # ---------- Events ----------
    def _delete_item(self, t: str, idx: int):
        if t == 'zero' and 0 <= idx < len(self.zeros):
            cj = self.conjugate_index(idx)
            if cj is not None:
                for k in sorted([idx, cj], reverse=True):
                    if 0 <= k < len(self.zeros):
                        self.zeros.pop(k)
            else:
                self.zeros.pop(idx)
            return True
        elif t == 'pole' and 0 <= idx < len(self.poles):
            self.poles.pop(idx)
            return True
        return False

    def keyPressEvent(self, ev: QtGui.QKeyEvent):
        if ev.key() in (QtCore.Qt.Key.Key_Backspace, QtCore.Qt.Key.Key_Delete):
            if self.selected:
                t, idx = self.selected
                self._delete_item(t, idx)
                self.selected = None
                self.update_scatter()
        else:
            super().keyPressEvent(ev)

    def on_click(self, ev):
        if ev.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        mode = self.mode_provider() if self.mode_provider else 'select'
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        c = self.screen_to_complex(ev.scenePos())
        found = self.find_near(c)
        if found and mode == 'select':
            t, idx, _ = found
            self.dragging_point = (t, idx)
            self.selected = (t, idx)
            return
        if found and mode == 'delete':
            t, idx, _ = found
            if self._delete_item(t, idx):
                self.selected = None
                self.update_scatter()
            return
        if mode in ('add_zero', 'add_pole'):
            if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
                c = self.snap_unit(c)
            if mode == 'add_zero':
                self.add_zero_pair(c)
            else:
                self.poles.append(c)
            self.update_scatter()
        else:
            self.selected = None

    def mouseReleaseEvent(self, ev):
        if self.dragging_point:
            self.dragging_point = None
        super().mouseReleaseEvent(ev)

    def on_move(self, pos):
        if self.dragging_point is None:
            return
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        c = self.screen_to_complex(pos)
        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
            c = self.snap_unit(c)
        t, idx = self.dragging_point
        if t == 'zero':
            self.move_zero_pair(idx, c)
        else:
            if 0 <= idx < len(self.poles):
                self.poles[idx] = c
        self.update_scatter()

    def load_from_roots(self, zeros, poles, tol: float = 1e-9):
        """Replace current zeros/poles from arbitrary root arrays, enforcing conjugate pairing for zeros.
        Poles are taken as-is (can extend if pairing desired)."""
        def pair_conjugates(arr):
            arr = list(arr)
            used = [False]*len(arr)
            out = []
            for i, z in enumerate(arr):
                if used[i]:
                    continue
                if abs(z.imag) <= tol:
                    out.append(complex(z.real, 0.0))
                    used[i] = True
                else:
                    # search partner
                    partner = None
                    for j in range(i+1, len(arr)):
                        if not used[j] and abs(arr[j] - z.conjugate()) < 1e-6:
                            partner = j
                            break
                    if partner is not None:
                        # canonical store positive imag first
                        zc = z if z.imag > 0 else z.conjugate()
                        out.append(zc)
                        out.append(zc.conjugate())
                        used[i] = True
                        used[partner] = True
                    else:
                        # lone complex root -> store both conj artificially
                        zc = z if z.imag > 0 else z.conjugate()
                        out.append(zc)
                        out.append(zc.conjugate())
                        used[i] = True
            return out
        self.zeros = pair_conjugates(zeros)
        self.poles = list(poles)
        self.update_scatter()
