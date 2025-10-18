from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient, QPixmap

class DynamicImagePanel(QFrame):
    def __init__(self, title_text, image_path, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 200)
        self.title_text = title_text
        self.image_path = image_path
        self.setStyleSheet("background: transparent;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 25, 15, 15) # Adjusted for title bar
        self.layout.setSpacing(5)

        self._title_label = QLabel(self.title_text)
        self._title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._title_label.setStyleSheet("color: #00BFFF; margin-bottom: 5px;")
        self._title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # Not added to layout, drawn manually

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True) # Scale image to fit label
        self.layout.addWidget(self.image_label)
        self._load_and_scale_image()

    def _load_and_scale_image(self):
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            # Scale pixmap to fit the label's current size while maintaining aspect ratio
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            self.image_label.setText("Image not found: " + self.image_path)
            self.image_label.setStyleSheet("color: red;")

    def resizeEvent(self, event):
        self._load_and_scale_image() # Re-scale image on resize
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        rect = self.rect().adjusted(1,1,-1,-1)
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(30, 30, 35, 180))
        gradient.setColorAt(1, QColor(10, 10, 15, 180))
        painter.setBrush(QBrush(gradient))

        border_color = QColor(0, 191, 255, 120)
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect, 10, 10)

        # Draw the title text manually
        painter.setFont(self._title_label.font())
        painter.setPen(QPen(self._title_label.palette().windowText().color()))
        title_rect = QRectF(0, 0, width, 25)
        painter.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap, self.title_text)

        super().paintEvent(event)