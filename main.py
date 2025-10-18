import sys
from PyQt5.QtWidgets import QApplication
from core.race_overlay import RaceOverlay

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = RaceOverlay()
    overlay.show()
    sys.exit(app.exec_())