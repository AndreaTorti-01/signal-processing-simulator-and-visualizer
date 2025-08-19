import pyqtgraph as pg
import numpy as np
from dsp.utils import H_eval


class FreqResponseWidget(pg.PlotWidget):
    def __init__(self):
        super().__init__()
        self.setLabel('bottom', 'ω (rad/sample)')
        self.setLabel('left', 'Amplification')
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setYRange(0, 10)
        self.curve = self.plot([], [])

    def update_response(self, zeros, poles, n=512):
        w = np.linspace(0, np.pi, n)
        ejw = np.exp(1j * w)
        H = H_eval(ejw, zeros, poles)
        mag = np.abs(H)
        self.curve.setData(w / np.pi, mag)
