# Zero-Pole Interactive Visualizer

![alt text](demo.gif)

An interactive multi-view GUI to place/move/delete zeros and poles on the unit circle and view:

1. Z-plane with draggable zeros (circles) and poles (crosses) constrained optionally to unit circle.
2. Real-time frequency response magnitude (|H(e^{jω})|) for ω ∈ [0, π].
3. 3D "circus tent" surface: magnitude of H(z) over a grid in the z-plane (|H(z)|) with interactive rotation.

Built with PyQt6 + pyqtgraph for performance and minimal code.

## Features
- Left panel: interactive pole-zero editor
  - Left click empty: add zero (o) (hold Shift to force on unit circle)
  - Right click empty: add pole (x) (hold Shift to force on unit circle)
  - Drag existing symbol to move (Ctrl while dragging to constrain radius=1)
  - Delete: select (click) then press Delete / Backspace
- Middle panel: frequency response updates live
- Right panel: 3D magnitude surface (log magnitude) updates on edits

## Running
```bash
pip install -r requirements.txt
python app.py
```

## Notes
- Frequency response computed on demand using vectorized NumPy.
- 3D surface kept to modest grid (e.g., 80x80) for interactivity; adjust in code.
- Stability / causal interpretation not enforced; purely algebraic visualization.
