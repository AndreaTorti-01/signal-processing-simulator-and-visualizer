from PyQt6 import QtWidgets, QtCore
from scipy.signal import dimpulse
import numpy as np

class FilterInfoWidget(QtWidgets.QWidget):
    filter_changed = QtCore.pyqtSignal(list, list)

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8,4,8,4)
        layout.setSpacing(6)

        def add_section(title, widget):
            lbl = QtWidgets.QLabel(title)
            f = lbl.font(); f.setBold(True); lbl.setFont(f)
            layout.addWidget(lbl)
            layout.addWidget(widget, 1)

        self.num_edit = QtWidgets.QTextEdit()
        self.den_edit = QtWidgets.QTextEdit()
        self.impulse_edit = QtWidgets.QTextEdit()
        
        for w in (self.num_edit, self.den_edit, self.impulse_edit):
            w.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
            w.setPlaceholderText("comma separated: 1.0, -0.5, 0.2 ...")
            w.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            w.setMinimumHeight(70)

        add_section("H(z) Numerator Coeffs (b):", self.num_edit)
        add_section("H(z) Denominator Coeffs (a):", self.den_edit)
        add_section("Impulse Response h[n]:", self.impulse_edit)

        btn_row = QtWidgets.QHBoxLayout()
        self.apply_button = QtWidgets.QPushButton("Apply Text → Zeros/Poles")
        btn_row.addStretch(1)
        btn_row.addWidget(self.apply_button)
        layout.addLayout(btn_row)

        self.apply_button.clicked.connect(self.on_apply)

        # Track last applied values to detect user-origin changes
        self._last_num = []
        self._last_den = []
        self._last_impulse = []

    def _format_coeffs(self, coeffs):
        return ", ".join(f"{c:.4f}" for c in coeffs)

    def _parse_list(self, text):
        parts = [p.strip() for p in text.replace('\n', ' ').split(',') if p.strip()]
        if not parts:
            return []
        out = []
        for p in parts:
            try:
                out.append(float(p))
            except ValueError:
                pass
        return out

    def update_info(self, zeros, poles):
        # Compute polynomial coefficients (descending powers) from zeros/poles
        num_coeffs = np.poly(zeros) if len(zeros) > 0 else np.array([1.0])
        den_coeffs = np.poly(poles) if len(poles) > 0 else np.array([1.0])

        # Impulse response: if IIR, use dimpulse; if FIR (den=1 & len small) just numerator padded
        if len(den_coeffs) == 1 and den_coeffs[0] != 0 and len(num_coeffs) <= 64:
            # Convert polynomial coeffs (descending) to time-domain h[n] with h[k] = coeffs[k]
            # Note: For FIR defined as b0 + b1 z^{-1}+..., polynomial vector here is b0..bM-1 in descending vs typical; we output original order b0..bM-1
            h = num_coeffs.astype(float)
        else:
            system = (num_coeffs, den_coeffs, 1)
            try:
                t, h_seq = dimpulse(system, n=64)
                h = h_seq[0].flatten()
            except Exception:
                h = np.zeros(32)

        # Only overwrite text if widget not being actively edited (has focus) to preserve user edits
        if not self.num_edit.hasFocus():
            self.num_edit.setPlainText(self._format_coeffs(num_coeffs.real))
        if not self.den_edit.hasFocus():
            self.den_edit.setPlainText(self._format_coeffs(den_coeffs.real))
        if not self.impulse_edit.hasFocus():
            self.impulse_edit.setPlainText(self._format_coeffs(h.real))

        self._last_num = list(num_coeffs.real)
        self._last_den = list(den_coeffs.real)
        self._last_impulse = list(h.real)

    def on_apply(self):
        # Determine source of change priority: impulse > numerator/denominator
        user_impulse = self._parse_list(self.impulse_edit.toPlainText())
        user_num = self._parse_list(self.num_edit.toPlainText())
        user_den = self._parse_list(self.den_edit.toPlainText())

        try:
            if user_impulse and (len(user_impulse) != len(self._last_impulse) or any(abs(a-b) > 1e-6 for a,b in zip(user_impulse, self._last_impulse))):
                # Treat impulse as FIR numerator, denominator = [1]
                num = np.array(user_impulse, dtype=float)
                den = np.array([1.0])
            else:
                num = np.array(user_num if user_num else [1.0], dtype=float)
                den = np.array(user_den if user_den else [1.0], dtype=float)
            # Derive zeros/poles from poly coefficients (descending powers)
            # Ensure leading coeff non-zero
            if abs(num[0]) < 1e-12:
                # strip leading zeros
                nz = np.flatnonzero(np.abs(num) > 1e-12)
                if nz.size:
                    num = num[nz[0]:]
                else:
                    num = np.array([1.0])
            if abs(den[0]) < 1e-12:
                nz = np.flatnonzero(np.abs(den) > 1e-12)
                if nz.size:
                    den = den[nz[0]:]
                else:
                    den = np.array([1.0])
            zeros = np.roots(num) if len(num) > 1 else []
            poles = np.roots(den) if len(den) > 1 else []
            self.filter_changed.emit(list(zeros), list(poles))
        except Exception:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg_box.setText("Failed to apply coefficients.")
            msg_box.setInformativeText("Check numeric formatting.")
            msg_box.setWindowTitle("Apply Error")
            msg_box.exec()
