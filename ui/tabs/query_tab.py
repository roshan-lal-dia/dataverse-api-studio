"""
Query Tab
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, QThread
from datetime import datetime
import json


class QueryThread(QThread):
    """Background thread for query operations"""
    
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, table_name, filter_query, select, order_by, top):
        super().__init__()
        self.client = client
        self.table_name = table_name
        self.filter_query = filter_query
        self.select = select
        self.order_by = order_by
        self.top = top
    
    def run(self):
        """Execute query"""
        try:
            select_list = [s.strip() for s in self.select.split(',')] if self.select else None
            
            result = self.client.read_multiple(
                self.table_name,
                self.filter_query if self.filter_query else None,
                select_list,
                self.top,
                self.order_by if self.order_by else None
            )
            
            if result.get("success"):
                self.success.emit(result)
            else:
                self.error.emit(result.get("error", "Unknown error"))
        
        except Exception as e:
            self.error.emit(str(e))


class QueryTab(QWidget):
    """Query operations tab"""
    
    operation_executed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.client = None
        self.query_thread = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Query configuration
        config_group = QGroupBox("Query Configuration")
        config_layout = QVBoxLayout()
        
        # Table name
        table_label = QLabel("Table Name:")
        self.table_input = QLineEdit()
        self.table_input.setPlaceholderText("e.g., account, contact")
        config_layout.addWidget(table_label)
        config_layout.addWidget(self.table_input)
        
        # Filter
        filter_label = QLabel("Filter (OData $filter):")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("e.g., revenue gt 1000000 and statecode eq 0")
        config_layout.addWidget(filter_label)
        config_layout.addWidget(self.filter_input)
        
        # Select
        select_label = QLabel("Select Fields (comma-separated):")
        self.select_input = QLineEdit()
        self.select_input.setPlaceholderText("e.g., name,revenue,websiteurl")
        config_layout.addWidget(select_label)
        config_layout.addWidget(self.select_input)
        
        # Order by
        order_label = QLabel("Order By:")
        self.order_input = QLineEdit()
        self.order_input.setPlaceholderText("e.g., revenue desc")
        config_layout.addWidget(order_label)
        config_layout.addWidget(self.order_input)
        
        # Top
        top_layout = QHBoxLayout()
        top_label = QLabel("Top (limit):")
        self.top_spin = QSpinBox()
        self.top_spin.setMinimum(1)
        self.top_spin.setMaximum(5000)
        self.top_spin.setValue(100)
        top_layout.addWidget(top_label)
        top_layout.addWidget(self.top_spin)
        top_layout.addStretch()
        config_layout.addLayout(top_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Execute button
        self.execute_button = QPushButton("🔍 Execute Query")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.clicked.connect(self._execute_query)
        self.execute_button.setEnabled(False)
        layout.addWidget(self.execute_button)
        
        layout.addStretch()
    
    def set_client(self, client):
        """Set the Dataverse client"""
        self.client = client
        self.execute_button.setEnabled(True)
    
    def _execute_query(self):
        """Execute query"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        table_name = self.table_input.text().strip()
        
        if not table_name:
            QMessageBox.warning(self, "Missing Input", "Please enter table name.")
            return
        
        # Disable button
        self.execute_button.setEnabled(False)
        self.execute_button.setText("⏳ Executing Query...")
        
        # Start query
        self.query_thread = QueryThread(
            self.client,
            table_name,
            self.filter_input.text().strip(),
            self.select_input.text().strip(),
            self.order_input.text().strip(),
            self.top_spin.value()
        )
        
        self.query_thread.success.connect(self._on_query_success)
        self.query_thread.error.connect(self._on_query_error)
        self.query_thread.start()
    
    def _on_query_success(self, result: dict):
        """Handle successful query"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("🔍 Execute Query")
        
        operation_data = {
            "type": "Query",
            "table": self.table_input.text(),
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "result": result
        }
        
        self.operation_executed.emit(operation_data)
    
    def _on_query_error(self, error_msg: str):
        """Handle query error"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("🔍 Execute Query")
        
        QMessageBox.critical(self, "Query Failed", f"Error:\n{error_msg}")
        
        operation_data = {
            "type": "Query",
            "table": self.table_input.text(),
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": error_msg
        }
        
        self.operation_executed.emit(operation_data)
