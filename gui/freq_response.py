import pyqtgraph as pg
import numpy as np
from dsp.utils import H_eval


class FreqResponseWidget(pg.GraphicsLayoutWidget):
    """Two-panel frequency response: top amplitude (log-y), bottom phase."""

    def __init__(self):
        super().__init__()

        # Top plot: amplitude (log scale on Y)
        self.amp_plot: pg.PlotItem = self.addPlot(row=0, col=0)
        self.amp_plot.setLabel('left', 'Amplitude (log)')
        self.amp_plot.showGrid(x=True, y=True, alpha=0.3)
        self.amp_curve = self.amp_plot.plot([], [], pen=pg.mkPen('c', width=2))

        # Bottom plot: phase (radians), share X axis
        self.phase_plot: pg.PlotItem = self.addPlot(row=1, col=0)
        self.phase_plot.setLabel('left', 'Phase (rad)')
        self.phase_plot.setLabel('bottom', 'ω (rad/sample)')
        self.phase_plot.showGrid(x=True, y=True, alpha=0.3)
        self.phase_plot.setXLink(self.amp_plot)
        self.phase_curve = self.phase_plot.plot([], [], pen=pg.mkPen('m', width=2))

        # Provide sensible initial ranges
        self.amp_plot.setYRange(1e-3, 10)  # works with log-y

    def update_response(self, zeros, poles, n=1024):
        # Frequency grid [0, pi]
        w = np.linspace(0, np.pi, n)
        ejw = np.exp(1j * w)
        H = H_eval(ejw, zeros, poles)

        # Amplitude (log-y): clamp to avoid zeros/NaNs
        mag = np.abs(H)
        mag = np.where(np.isfinite(mag), mag, np.nan)
        # Replace non-positive/NaN with small epsilon to be valid for log scale
        eps = 1e-6
        mag_safe = np.copy(mag)
        invalid = ~np.isfinite(mag_safe) | (mag_safe <= 0)
        mag_safe[invalid] = eps

        # Auto y-range based on finite values
        finite_mag = mag_safe[np.isfinite(mag_safe) & (mag_safe > 0)]
        if finite_mag.size:
            ymin = max(eps, np.nanpercentile(finite_mag, 1))
            ymax = np.nanpercentile(finite_mag, 99)
            if np.isfinite(ymin) and np.isfinite(ymax) and ymax > ymin * 1.05:
                self.amp_plot.setYRange(ymin, ymax)

        x = w / np.pi  # normalize to [0,1]
        self.amp_curve.setData(x, mag_safe)

        # Phase (unwrapped radians)
        phase = np.unwrap(np.angle(H))
        # Clean any NaNs from invalid H
        phase = np.where(np.isfinite(phase), phase, np.nan)
        self.phase_curve.setData(x, phase)
