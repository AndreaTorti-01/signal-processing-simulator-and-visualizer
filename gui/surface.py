from pyqtgraph.opengl import (
    GLViewWidget,
    GLGridItem,
    GLSurfacePlotItem,
    GLLinePlotItem,
)
import numpy as np
from dsp.utils import H_eval


class Surface3D(GLViewWidget):
    def __init__(self):
        super().__init__()
        self.setCameraPosition(distance=8)
        grid = GLGridItem(); grid.scale(1, 1, 1); self.addItem(grid)
        self.surface: GLSurfacePlotItem | None = None
        self.unit_circle_line: GLLinePlotItem | None = None
        self.upper_arc_line: GLLinePlotItem | None = None
        self.resolution = 90
        self.span = 1.5  # x,y in [-span, span]

    def update_surface(self, zeros, poles):
        n = self.resolution
        x = np.linspace(-self.span, self.span, n, dtype=np.float32)
        y = np.linspace(-self.span, self.span, n, dtype=np.float32)
        X, Y = np.meshgrid(x, y, indexing='ij')
        Zc = X + 1j * Y
        
        # --- Shared Transformation for Surface and Circle ---
        def transform_h(h_vals):
            mag = np.abs(h_vals)
            mag[~np.isfinite(mag)] = 0.0
            log_mag = np.log10(np.maximum(1e-9, mag))
            return log_mag

        # Calculate log magnitude for the whole surface
        log_mag_surface = transform_h(H_eval(Zc, zeros, poles))
        
        # Normalize to keep it visually contained
        finite = np.isfinite(log_mag_surface)
        if np.any(finite):
            min_val = np.min(log_mag_surface[finite])
            max_val = np.max(log_mag_surface[finite])
            if max_val - min_val > 1e-6:
                # Apply normalization to surface
                Zsurf = (log_mag_surface - min_val) / (max_val - min_val) * 2.0 # Squash height
            else:
                Zsurf = np.zeros_like(log_mag_surface)
                Zsurf[finite] = 0
        else:
            Zsurf = np.zeros_like(log_mag_surface)

        if self.surface is None:
            self.surface = GLSurfacePlotItem(x=x, y=y, z=Zsurf, shader='shaded', smooth=False)
            self.addItem(self.surface)
        else:
            self.surface.setData(z=Zsurf)

        # --- Unit circle overlay on the surface ---
        theta = np.linspace(0, 2 * np.pi, 400)
        uc_z = np.exp(1j * theta)
        
        # Calculate and transform unit circle height using the same parameters
        log_mag_uc = transform_h(H_eval(uc_z, zeros, poles))
        
        if np.any(finite):
             # Use the same min/max from the surface for consistent scaling
            if max_val - min_val > 1e-6:
                cz = (log_mag_uc - min_val) / (max_val - min_val) * 2.0
            else:
                cz = np.zeros_like(log_mag_uc)
        else:
            cz = np.zeros_like(log_mag_uc)

        cx = np.cos(theta)
        cy = np.sin(theta)
        
        circle_pts = np.vstack([cx, cy, cz]).T.astype(np.float32)
        
        if self.unit_circle_line is None:
            self.unit_circle_line = GLLinePlotItem(
                pos=circle_pts, color=(1, 1, 1, 0.85), width=2, mode='line_strip'
            )
            self.addItem(self.unit_circle_line)
        else:
            self.unit_circle_line.setData(pos=circle_pts)

        # Highlight upper half (0..pi) on unit circle
        theta_u = np.linspace(0, np.pi, 200)
        ux = np.cos(theta_u)
        uy = np.sin(theta_u)
        uz = cz[:200] # Match the height from the full circle
        upper_pts = np.vstack([ux, uy, uz]).T.astype(np.float32)
        if self.upper_arc_line is None:
            self.upper_arc_line = GLLinePlotItem(
                pos=upper_pts, color=(1, 0.85, 0.2, 0.95), width=4, mode='line_strip'
            )
            self.addItem(self.upper_arc_line)
        else:
            self.upper_arc_line.setData(pos=upper_pts)
