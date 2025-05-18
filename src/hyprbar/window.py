import sys
import signal
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QGuiApplication
from hyprbar.constants import APP_NAME
from hyprbar.util import updateQtEnvironment


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}")
        self.setObjectName(f"{APP_NAME}")
        # Set application name and class before creating QWidget
        QGuiApplication.setApplicationName(f"{APP_NAME}")
        QGuiApplication.setDesktopFileName(f"{APP_NAME}")
        QGuiApplication.setApplicationDisplayName(f"{APP_NAME}")


if __name__ == "__main__":
    updateQtEnvironment()
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())
