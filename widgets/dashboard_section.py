from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient, QPolygonF

class DashboardSectionWidget(QFrame):
    """
    Custom widget to draw data sections with a hexagonal/angled background
    and content inside.
    """
    def __init__(self, title_text, variables, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 120) # Minimum size for sections
        self.title_text = title_text
        self.variables = variables
        self.labels = {} # Stores QLabels for dynamic updates

        self.setContentsMargins(15, 25, 15, 15) # Adjusted for title bar
        self.setStyleSheet("background: transparent;") # Custom painting will handle background

        # Internal layout for title and data
        internal_layout = QVBoxLayout(self)
        internal_layout.setContentsMargins(0, 0, 0, 0)
        internal_layout.setSpacing(5)

        # Title Label (will be drawn, but we keep a label for convenience)
        self._title_label = QLabel(self.title_text)
        self._title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._title_label.setStyleSheet("color: #00BFFF; margin-bottom: 5px;")
        # We'll actually draw the title directly, so this is mainly for text content
        self._title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # internal_layout.addWidget(self._title_label) # Not adding to layout, drawing manually

        data_grid = QGridLayout()
        data_grid.setSpacing(3)
        data_grid.setContentsMargins(0, 0, 0, 0) # No margins within data grid

        for i, var in enumerate(self.variables):
            name = QLabel(var.replace("_", " ").title())
            name.setFont(QFont("Segoe UI", 9))
            name.setStyleSheet("color: #AAAAAA;")
            val = QLabel("—")
            val.setFont(QFont("Segoe UI", 9))
            val.setStyleSheet("color: white;")
            data_grid.addWidget(name, i, 0, Qt.AlignLeft)
            data_grid.addWidget(val, i, 1, Qt.AlignRight)
            self.labels[var] = val
        
        internal_layout.addLayout(data_grid)
        self.setLayout(internal_layout) # Set the internal layout


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Calculate points for a roughly hexagonal shape
        # Adjust these proportions to get the desired angle/shape
        indent = min(width, height) / 8 # How much the top/bottom edges are indented
        
        # Adjust for more of a slanted rectangle effect like the image
        points = QPolygonF([
            QPointF(indent, 0),                       # Top-left corner (indented)
            QPointF(width - indent, 0),               # Top-right corner (indented)
            QPointF(width, height - indent),         # Right-bottom corner
            QPointF(width - indent, height),          # Bottom-right corner (indented)
            QPointF(indent, height),                  # Bottom-left corner (indented)
            QPointF(0, height - indent)              # Left-top corner
        ])

        path = QPainterPath()
        path.addPolygon(points)

        # Background gradient for the section
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor(30, 30, 35, 180))
        gradient.setColorAt(1, QColor(10, 10, 15, 180))
        painter.setBrush(QBrush(gradient))

        # Border color matching the image (subtle blue/grey)
        border_color = QColor(0, 191, 255, 120) # A softer blue
        painter.setPen(QPen(border_color, 2))
        painter.drawPath(path)

        # Draw the title text directly on top of the shape
        painter.setFont(self._title_label.font())
        painter.setPen(QPen(self._title_label.palette().windowText().color()))
        # Center the title at the top, allowing some padding
        title_rect = QRectF(0, 0, width, 25) # Give it a small area at the top
        painter.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap, self.title_text)

        super().paintEvent(event) # Let child widgets (Qlabel) paint over it