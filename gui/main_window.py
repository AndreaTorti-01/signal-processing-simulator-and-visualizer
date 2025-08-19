from PyQt6 import QtWidgets

from gui.editor import PoleZeroEditor
from gui.freq_response import FreqResponseWidget
from gui.surface import Surface3D
from gui.filter_info import FilterInfoWidget


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Interactive Pole-Zero Visualizer')
        
        # Main layout: plots on top, info on bottom
        main_layout = QtWidgets.QVBoxLayout(self)
        plots_layout = QtWidgets.QHBoxLayout()

        # Left side (controls + editor)
        left_v = QtWidgets.QVBoxLayout()
        ctrl = QtWidgets.QHBoxLayout()
        self.current_mode = 'select'

        def mk_btn(text, mode):
            b = QtWidgets.QToolButton()
            b.setText(text)
            b.setCheckable(True)
            b.clicked.connect(lambda ch: self.set_mode(mode if ch else 'select'))
            return b

        self.btn_select = mk_btn('Select/Move', 'select')
        self.btn_add_zero = mk_btn('Add Zero', 'add_zero')
        self.btn_add_pole = mk_btn('Add Pole', 'add_pole')
        self.btn_select.setChecked(True)
        for b in (self.btn_select, self.btn_add_zero, self.btn_add_pole):
            ctrl.addWidget(b)
        ctrl.addStretch(1)
        hint = QtWidgets.QLabel('Shift: snap add | Ctrl: snap move | Delete: remove')
        f = hint.font(); f.setPointSize(9); hint.setFont(f)
        left_v.addLayout(ctrl)
        left_v.addWidget(hint)

        self.editor = PoleZeroEditor(mode_provider=lambda: self.current_mode)
        left_v.addWidget(self.editor, 1)
        left_w = QtWidgets.QWidget(); left_w.setLayout(left_v)

        # Middle & Right plots
        self.freq = FreqResponseWidget()
        self.surface = Surface3D()

        plots_layout.addWidget(left_w, 2)
        plots_layout.addWidget(self.freq, 2)
        plots_layout.addWidget(self.surface, 3)
        
        # Bottom info widget
        self.info_widget = FilterInfoWidget()

        main_layout.addLayout(plots_layout, 5) # Give plots more stretch factor
        main_layout.addWidget(self.info_widget, 1)

        self.editor.updated.connect(self.recompute)
        self.info_widget.filter_changed.connect(self.on_filter_text_changed)
        self.recompute()

    def set_mode(self, mode):
        self.current_mode = mode
        for m, b in {
            'select': self.btn_select,
            'add_zero': self.btn_add_zero,
            'add_pole': self.btn_add_pole,
        }.items():
            b.blockSignals(True)
            b.setChecked(m == mode)
            b.blockSignals(False)

    def recompute(self):
        zeros = self.editor.zeros
        poles = self.editor.poles
        self.freq.update_response(zeros, poles)
        self.surface.update_surface(zeros, poles)
        self.info_widget.update_info(zeros, poles)

    def on_filter_text_changed(self, new_zeros, new_poles):
        # Use editor helper to rebuild internal lists
        self.editor.load_from_roots(new_zeros, new_poles)
        # Editor emits updated inside update_scatter; freq/surface & info refresh via recompute
