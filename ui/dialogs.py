"""
Custom dialog for displaying user-friendly validation errors
with proper sizing, scrolling, and clear action buttons
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class ValidationErrorDialog(QDialog):
    """
    User-friendly validation error dialog with scrollable content
    
    Signals:
        - apply_corrections: Emitted when user clicks "Apply Corrections"
        - proceed_anyway: Emitted when user clicks "Proceed Anyway"
        - cancel: Emitted when user clicks "Cancel"
    """
    
    apply_corrections = pyqtSignal()
    proceed_anyway = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self, parent=None, title="Validation Errors", has_corrections=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.has_corrections = has_corrections
        self.result_action = None
        
        # Set size - larger for readability
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setMaximumWidth(1000)
        self.setMaximumHeight(700)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_icon = QLabel("⚠️")
        title_font = QFont()
        title_font.setPointSize(14)
        title_icon.setFont(title_font)
        
        title_text = QLabel("Validation Issues Detected")
        title_font.setBold(True)
        title_text.setFont(title_font)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #cccccc;")
        layout.addWidget(separator)
        
        # Scrollable error content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f0f0f0;
            }
            QScrollBar::handle:vertical {
                background: #999;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)
        
        # Content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Error message text (main content)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                line-height: 1.5;
            }
        """)
        self.error_text.setMinimumHeight(250)
        content_layout.addWidget(self.error_text)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, stretch=1)
        
        # Separator before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("color: #cccccc;")
        layout.addWidget(separator2)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ddd;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #bbb;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        if self.has_corrections:
            self.apply_button = QPushButton("✅ Apply Corrections")
            self.apply_button.setMinimumWidth(150)
            self.apply_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            self.apply_button.clicked.connect(self._on_apply_corrections)
            button_layout.addWidget(self.apply_button)
        
        self.proceed_button = QPushButton("⚡ Proceed Anyway")
        self.proceed_button.setMinimumWidth(150)
        self.proceed_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a68c9;
            }
        """)
        self.proceed_button.clicked.connect(self._on_proceed)
        button_layout.addWidget(self.proceed_button)
        
        layout.addLayout(button_layout)
    
    def set_error_content(self, message: str, detailed_info: str = None):
        """
        Set the error message content
        
        Args:
            message: Main user-friendly error message
            detailed_info: Optional detailed/technical information
        """
        full_message = message
        
        if detailed_info:
            full_message += f"\n\n{'─' * 60}\nTechnical Details:\n{'─' * 60}\n{detailed_info}"
        
        self.error_text.setText(full_message)
        # Scroll to top
        self.error_text.verticalScrollBar().setValue(0)
    
    def _on_cancel(self):
        self.result_action = "cancel"
        self.cancel.emit()
        self.reject()
    
    def _on_apply_corrections(self):
        self.result_action = "apply"
        self.apply_corrections.emit()
        self.accept()
    
    def _on_proceed(self):
        self.result_action = "proceed"
        self.proceed_anyway.emit()
        self.accept()
    
    def get_result(self):
        """Get the action user selected"""
        return self.result_action
    
    @staticmethod
    def show_error(parent, title: str, message: str, detailed_info: str = None, 
                   has_corrections: bool = False) -> str:
        """
        Show validation error dialog and return user's choice
        
        Returns:
            "apply" - Apply corrections
            "proceed" - Proceed anyway
            "cancel" - Cancel operation
        """
        dialog = ValidationErrorDialog(parent, title, has_corrections)
        dialog.set_error_content(message, detailed_info)
        
        # Show dialog and return result
        dialog.exec()
        return dialog.get_result()
