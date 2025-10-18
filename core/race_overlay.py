import random
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QFrame, QSizeGrip, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QLinearGradient

# Import updated widgets
from widgets.dashboard_section import DashboardSectionWidget
from widgets.llm_output_widget import LLMOutputWidget
from widgets.dynamic_image_panel import DynamicImagePanel


class RaceOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_pos = None
        self.sections = [] # List to hold DashboardSectionWidget instances for data updates

        # === Window setup ===
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 1400, 900)  # Adjust initial size for new layout

        # === Root layout ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)

        # === Title Bar ===
        self.title_bar_frame = QFrame()
        self.title_bar_frame.setStyleSheet("""
            background-color: rgba(50,50,50,200);
            border-radius: 6px;
        """)
        title_bar_layout = QHBoxLayout(self.title_bar_frame)
        title_bar_layout.setContentsMargins(10,5,10,5)
        
        logo_label = QLabel("F1")
        logo_label.setFont(QFont("Segoe UI", 16, QFont.ExtraBold))
        logo_label.setStyleSheet("color: #FF1801; margin-right: 15px;")
        title_bar_layout.addWidget(logo_label)

        self.title = QLabel("F1 DIGITAL TWIN DASHBOARD")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet("color: white; padding: 4px;")
        self.title.setAlignment(Qt.AlignCenter)
        title_bar_layout.addWidget(self.title)
        
        self.main_layout.addWidget(self.title_bar_frame)

        # === Main Content Area (QGridLayout) ===
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            background-color: rgba(20, 20, 25, 160);
            border-radius: 12px;
            padding: 20px;
        """)
        self.content_layout = QGridLayout(self.content_frame)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.addWidget(self.content_frame)

        # --- Main Left Panel: LLM HPC Layer Outputs ---
        self.llm_output_panel = LLMOutputWidget("LLM HPC Layer Outputs")
        self.content_layout.addWidget(self.llm_output_panel, 0, 0, 2, 1) # Row 0, Col 0, spans 2 rows, 1 col

        # --- Upper Right Panel: F1 Car Model ---
        # Using DynamicImagePanel to display the pre-rendered spinning car image
        self.car_model_panel = DynamicImagePanel(
            "F1 Car Model", 
            "assets/f1_car_spinning.png"
        )
        self.content_layout.addWidget(self.car_model_panel, 0, 1, 1, 1) # Row 0, Col 1, spans 1 row, 1 col

        # --- Middle Right Panel: F1 Car Digital Twin Data ---
        # Using DashboardSectionWidget for data display
        self.car_data_panel = DashboardSectionWidget(
            "F1 Car Digital Twin Data",
            ["speed_kph", "engine_rpm", "fuel_level"] # Simplified names for display
        )
        # Store the label reference for direct update
        self.sections.append(self.car_data_panel)
        self.content_layout.addWidget(self.car_data_panel, 1, 1, 1, 1) # Row 1, Col 1, spans 1 row, 1 col

        # --- Lower Right Panel: Realistic 3D Track Model ---
        # Using DynamicImagePanel to display the pre-rendered track image
        self.track_model_panel = DynamicImagePanel(
            "Track Visualization",
            "assets/f1_track_aerial.png"
        )
        self.content_layout.addWidget(self.track_model_panel, 2, 0, 1, 2) # Row 2, Col 0, spans 1 row, 2 cols (takes full width)

        # --- Bottom Right Panel: Track Digital Twin Data ---
        self.track_data_panel = DashboardSectionWidget(
            "Track Digital Twin Data",
            ["ambient_temp_c", "track_temp_c", "humidity_pct", "wind_speed_kph", "yellow_flags"]
        )
        # Store the label reference for direct update
        self.sections.append(self.track_data_panel)
        self.content_layout.addWidget(self.track_data_panel, 3, 0, 1, 2) # Row 3, Col 0, spans 1 row, 2 cols (takes full width)

        # === Size Grip (bottom-right corner for resizing) ===
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("background: transparent;")
        self.size_grip.setGeometry(self.width() - 20, self.height() - 20, 20, 20)
        self.size_grip.show()
        self.size_grip.raise_() # Ensure it's on top

        # === Timer for simulated updates ===
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_data)
        self.timer.start(1500) # Update every 1.5 seconds

    def update_all_data(self):
        """Update all dynamic data on the dashboard."""
        # Update LLM Outputs
        self.llm_output_panel.set_output_text(self._generate_llm_output())

        # Update Car Digital Twin Data
        self.car_data_panel.labels["speed_kph"].setText(f"{random.randint(280, 350)} km/h")
        self.car_data_panel.labels["engine_rpm"].setText(f"{random.randint(15000, 19000)} (temp {random.randint(90, 105)}°C)")
        fuel_liters = random.randint(10, 60)
        fuel_pct = int((fuel_liters / 60) * 100)
        self.car_data_panel.labels["fuel_level"].setText(f"{fuel_pct}% ({fuel_liters}/60L)")

        # Update Track Digital Twin Data
        self.track_data_panel.labels["ambient_temp_c"].setText(f"{random.randint(20, 35)}°C")
        self.track_data_panel.labels["track_temp_c"].setText(f"{random.randint(25, 50)}°C")
        self.track_data_panel.labels["humidity_pct"].setText(f"{random.randint(10, 90)}%")
        self.track_data_panel.labels["wind_speed_kph"].setText(f"{round(random.uniform(5, 40), 1)} kph")
        self.track_data_panel.labels["yellow_flags"].setText(random.choice(["None", "Sector 1", "Sector 3", "Full Track"]))


    def _generate_llm_output(self):
        """Generates a dynamic LLM-like output string."""
        outputs = [
            "• Optimize tire strategy: Medium compound for next 15 laps.",
            "• Driver feedback: Monitor turn 3 understeer.",
            "• Engine performance: Slight power curve decline, maintenance needed.",
            "• Fuel management: Rain probability increasing, target lap 40 pit for refueling.",
            "• Aerodynamic analysis: Increase front wing angle by 0.5 degrees for improved grip.",
            "• Pit window alert: Optimal pit stop window open in 2 laps, consider hard tires.",
            "• Chassis stability: Minor oscillation detected under heavy braking, advise driver.",
            "• ERS deployment: Recommend full deployment on back straight for overtake opportunity.",
            "• Track evolution: Grip level increasing, suggest pushing limits in fast corners.",
            "• Competitor analysis: Car #12 showing slower sector 2 times, capitalize on pace advantage."
        ]
        
        # Select 3-4 random unique suggestions
        selected_outputs = random.sample(outputs, k=random.randint(3, 4))
        return "\n".join(selected_outputs)

    # === Draggable from title bar ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar_frame.geometry().contains(event.pos()):
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            QApplication.quit()