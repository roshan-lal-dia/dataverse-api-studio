"""
Batch Operations Tab
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, QThread
from datetime import datetime
import json


class BatchOperationThread(QThread):
    """Background thread for batch operations"""
    
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, operations):
        super().__init__()
        self.client = client
        self.operations = operations
    
    def run(self):
        """Execute batch operation"""
        try:
            result = self.client.batch_operation(self.operations)
            
            if result.get("success"):
                self.success.emit(result)
            else:
                self.error.emit(result.get("error", "Unknown error"))
        
        except Exception as e:
            self.error.emit(str(e))


class BatchTab(QWidget):
    """Batch operations tab"""
    
    operation_executed = pyqtSignal(dict)
    
    def __init__(self, template_manager):
        super().__init__()
        
        self.template_manager = template_manager
        self.client = None
        self.operation_thread = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Batch operations editor
        editor_group = QGroupBox("Batch Operations (JSON Array)")
        editor_layout = QVBoxLayout()
        
        self.batch_editor = QTextEdit()
        self.batch_editor.setPlaceholderText('[\n  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Account 1"}},\n  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Account 2"}}\n]')
        self.batch_editor.setMinimumHeight(400)
        editor_layout.addWidget(self.batch_editor)
        
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_file_button = QPushButton("📂 Load from File")
        self.load_file_button.clicked.connect(self._load_from_file)
        button_layout.addWidget(self.load_file_button)
        
        self.execute_button = QPushButton("⚡ Execute Batch")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.clicked.connect(self._execute_batch)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button, stretch=1)
        
        layout.addLayout(button_layout)
    
    def set_client(self, client):
        """Set the Dataverse client"""
        self.client = client
        self.execute_button.setEnabled(True)
    
    def _load_from_file(self):
        """Load batch operations from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Batch Operations",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.batch_editor.setPlainText(json.dumps(data, indent=2))
            
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{str(e)}")
    
    def _execute_batch(self):
        """Execute batch operations"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        # Parse JSON
        batch_text = self.batch_editor.toPlainText().strip()
        
        if not batch_text:
            QMessageBox.warning(self, "Empty Input", "Please enter batch operations.")
            return
        
        try:
            operations = json.loads(batch_text)
            
            if not isinstance(operations, list):
                QMessageBox.warning(self, "Invalid Format", "Batch operations must be a JSON array.")
                return
        
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"JSON parsing error:\n{str(e)}")
            return
        
        # Disable button
        self.execute_button.setEnabled(False)
        self.execute_button.setText("⏳ Executing Batch...")
        
        # Start operation
        self.operation_thread = BatchOperationThread(self.client, operations)
        self.operation_thread.success.connect(self._on_batch_success)
        self.operation_thread.error.connect(self._on_batch_error)
        self.operation_thread.start()
    
    def _on_batch_success(self, result: dict):
        """Handle successful batch operation"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("⚡ Execute Batch")
        
        operation_data = {
            "type": "Batch Operation",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "result": result
        }
        
        self.operation_executed.emit(operation_data)
    
    def _on_batch_error(self, error_msg: str):
        """Handle batch operation error"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("⚡ Execute Batch")
        
        QMessageBox.critical(self, "Batch Failed", f"Error:\n{error_msg}")
        
        operation_data = {
            "type": "Batch Operation",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": error_msg
        }
        
        self.operation_executed.emit(operation_data)
    
    def load_operations(self, operations: list):
        """Load operations from external source"""
        self.batch_editor.setPlainText(json.dumps(operations, indent=2))
