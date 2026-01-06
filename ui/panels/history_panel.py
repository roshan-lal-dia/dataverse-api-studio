"""
History Panel - Shows recent operation history
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QGroupBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from datetime import datetime


class HistoryPanel(QWidget):
    """Operation history panel widget"""
    
    MAX_HISTORY = 20
    
    def __init__(self):
        super().__init__()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # History group
        history_group = QGroupBox("📜 Operation History")
        history_layout = QVBoxLayout()
        
        # History list
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_list)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
    
    def add_operation(self, operation_data: dict):
        """Add operation to history"""
        # Format operation for display
        op_type = operation_data.get("type", "Unknown")
        timestamp = operation_data.get("timestamp", datetime.now().isoformat())
        success = operation_data.get("success", False)
        
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp
        
        # Status icon
        status_icon = "✅" if success else "❌"
        
        # Create display text
        display_text = f"{status_icon} {time_str} - {op_type}"
        
        # Add to list
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, operation_data)
        
        self.history_list.insertItem(0, item)
        
        # Limit history size
        while self.history_list.count() > self.MAX_HISTORY:
            self.history_list.takeItem(self.history_list.count() - 1)
    
    def clear(self):
        """Clear all history"""
        self.history_list.clear()
