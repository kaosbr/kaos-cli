from PyQt6.QtWidgets import QPushButton, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFont

class ModernButton(QPushButton):
    def __init__(self, text, primary=False, dangerous=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        
        # Samsung-inspired Color Palette
        COLOR_PRIMARY = "#0078D4"
        COLOR_HOVER = "#0086F1"
        COLOR_DANGEROUS = "#D83B01"
        COLOR_DANGEROUS_HOVER = "#EA4300"
        COLOR_BG = "#2B2B2B"
        COLOR_BG_HOVER = "#3B3B3B"
        
        style = f"""
            QPushButton {{
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 4px;
                color: #FFFFFF;
                background-color: {COLOR_BG};
                border: 1px solid #1A1A1A;
            }}
            QPushButton:hover {{
                background-color: {COLOR_BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #1A1A1A;
            }}
            QPushButton:disabled {{
                color: #666666;
                background-color: #222222;
                border: 1px solid #333333;
            }}
        """
        if primary:
            style += f"QPushButton {{ background-color: {COLOR_PRIMARY}; border: none; }} " \
                     f"QPushButton:hover {{ background-color: {COLOR_HOVER}; }}"
        elif dangerous:
            style += f"QPushButton {{ background-color: {COLOR_DANGEROUS}; border: none; }} " \
                     f"QPushButton:hover {{ background-color: {COLOR_DANGEROUS_HOVER}; }}"
        
        self.setStyleSheet(style)

class StatusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 8px;
                border: 1px solid #333333;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(70, 70)
        icon_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 35px; border: 2px solid #0078D4;")
        layout.addWidget(icon_frame)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.lbl_title = QLabel("NO DEVICE DETECTED")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        text_layout.addWidget(self.lbl_title)
        
        self.lbl_info = QLabel("Model: --- | Bit: --- | Mode: ---")
        self.lbl_info.setStyleSheet("font-size: 13px; color: #888888; font-family: 'Consolas', monospace;")
        text_layout.addWidget(self.lbl_info)

        self.lbl_subtitle = QLabel("Waiting for Samsung device connection via USB...")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #BBBBBB;")
        text_layout.addWidget(self.lbl_subtitle)
        
        layout.addLayout(text_layout)
        layout.addStretch()

    def update_status(self, connected: bool, title: str = "", info: str = "", subtitle: str = ""):
        if connected:
            self.lbl_title.setText(title)
            self.lbl_info.setText(info)
            self.lbl_subtitle.setText(subtitle)
            self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FF41;")
        else:
            self.lbl_title.setText("DISCONNECTED")
            self.lbl_info.setText("Model: --- | Bit: --- | Mode: ---")
            self.lbl_subtitle.setText("Waiting for Samsung device connection via USB...")
            self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")

class SidebarMenu(QFrame):
    item_clicked = pyqtSignal(int)

    def __init__(self, items: list, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-right: 1px solid #333333;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #BBBBBB;
                padding: 12px 20px;
                text-align: left;
                font-size: 13px;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background: #252525;
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background: #2A2A2A;
                color: #0078D4;
                font-weight: bold;
                border-left: 3px solid #0078D4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)
        
        self.buttons = []
        for i, (icon, label) in enumerate(items):
            btn = QPushButton(f"{icon}  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, x=i: self._on_click(x))
            layout.addWidget(btn)
            self.buttons.append(btn)
        
        layout.addStretch()
        
        if self.buttons:
            self._on_click(0)

    def _on_click(self, index: int):
        for i, btn in enumerate(self.buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.item_clicked.emit(index)
