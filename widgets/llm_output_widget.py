from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient

class LLMOutputWidget(QFrame):
    def __init__(self, title_text, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 250)
        self.title_text = title_text
        self.setStyleSheet("background: transparent;") # Custom painting for background

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 25, 15, 15) # Adjusted for title bar

        # Title Label (will be drawn manually)
        self._title_label = QLabel(self.title_text)
        self._title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._title_label.setStyleSheet("color: #00BFFF; margin-bottom: 5px;")
        self._title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # We don't add this to layout, drawing happens in paintEvent

        self.output_display = QTextEdit(self)
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Segoe UI", 9))
        self.output_display.setStyleSheet("""
            background-color: rgba(0,0,0,0); /* Transparent background for text area */
            color: white;
            border: none;
            padding: 5px;
        """)
        self.layout.addWidget(self.output_display)

    def set_output_text(self, text):
        self.output_display.setText(text)
        self.update() # Request repaint if custom drawing depends on text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Rounded rectangle for the panel background
        rect = self.rect().adjusted(1,1,-1,-1) # Inset slightly for border
        
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(30, 30, 35, 180))
        gradient.setColorAt(1, QColor(10, 10, 15, 180))
        painter.setBrush(QBrush(gradient))

        border_color = QColor(0, 191, 255, 120)
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(rect, 10, 10) # Rounded corners

        # Draw the title text manually
        painter.setFont(self._title_label.font())
        painter.setPen(QPen(self._title_label.palette().windowText().color()))
        title_rect = QRectF(0, 0, width, 25) # Area for title at the top
        painter.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap, self.title_text)

        super().paintEvent(event) # Let child widgets paint over it