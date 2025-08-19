import sys
from PyQt6 import QtWidgets
from gui.main_window import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.showMaximized()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
