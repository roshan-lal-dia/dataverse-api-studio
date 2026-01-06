"""
CRUD Operations Tab with integrated validation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QGroupBox, QMessageBox, QCheckBox,
    QInputDialog
)
from PyQt6.QtCore import pyqtSignal, QThread
from datetime import datetime
import json

from utils.payload_validator import PayloadValidator
from utils.error_formatter import ErrorFormatter
from ui.dialogs import ValidationErrorDialog


class CRUDOperationThread(QThread):
    """Background thread for CRUD operations"""
    
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, operation, table_name, data, record_id=None):
        super().__init__()
        self.client = client
        self.operation = operation
        self.table_name = table_name
        self.data = data
        self.record_id = record_id
    
    def run(self):
        """Execute operation"""
        try:
            result = None
            
            if self.operation == "CREATE":
                result = self.client.create_record(self.table_name, self.data)
            elif self.operation == "READ":
                result = self.client.read_record(self.table_name, self.record_id)
            elif self.operation == "UPDATE":
                result = self.client.update_record(self.table_name, self.record_id, self.data)
            elif self.operation == "DELETE":
                result = self.client.delete_record(self.table_name, self.record_id)
            
            if result and result.get("success"):
                self.success.emit(result)
            else:
                self.error.emit(result.get("error", "Unknown error"))
        
        except Exception as e:
            self.error.emit(str(e))


class CRUDTab(QWidget):
    """CRUD operations tab"""
    
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
        
        # Operation selector
        op_group = QGroupBox("Operation Type")
        op_layout = QHBoxLayout()
        
        op_label = QLabel("Select Operation:")
        self.op_combo = QComboBox()
        self.op_combo.addItems(["CREATE", "READ", "UPDATE", "DELETE"])
        self.op_combo.currentTextChanged.connect(self._on_operation_changed)
        
        op_layout.addWidget(op_label)
        op_layout.addWidget(self.op_combo, stretch=1)
        op_group.setLayout(op_layout)
        layout.addWidget(op_group)
        
        # Table name
        table_group = QGroupBox("Entity Details")
        table_layout = QVBoxLayout()
        
        table_label = QLabel("Table Name (logical name):")
        self.table_input = QLineEdit()
        self.table_input.setPlaceholderText("e.g., account, contact, lead")
        table_layout.addWidget(table_label)
        table_layout.addWidget(self.table_input)
        
        # Record ID (for READ, UPDATE, DELETE)
        self.record_id_label = QLabel("Record ID (GUID):")
        self.record_id_input = QLineEdit()
        self.record_id_input.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        table_layout.addWidget(self.record_id_label)
        table_layout.addWidget(self.record_id_input)
        
        # Validation checkbox
        validation_layout = QHBoxLayout()
        self.validate_checkbox = QCheckBox("✓ Validate payload before execution")
        self.validate_checkbox.setChecked(True)
        self.validate_checkbox.setToolTip("Check payload against metadata for required fields, types, and permissions")
        validation_layout.addWidget(self.validate_checkbox)
        validation_layout.addStretch()
        table_layout.addLayout(validation_layout)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Data JSON
        data_group = QGroupBox("Data (JSON)")
        data_layout = QVBoxLayout()
        
        self.data_editor = QTextEdit()
        self.data_editor.setPlaceholderText('{\n  "name": "Example Account",\n  "websiteurl": "https://example.com"\n}')
        self.data_editor.setMinimumHeight(200)
        data_layout.addWidget(self.data_editor)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Template selector
        template_layout = QHBoxLayout()
        template_label = QLabel("Template:")
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- No Template --")
        self.load_template_button = QPushButton("Load Template")
        self.load_template_button.clicked.connect(self._load_template)
        self.save_template_button = QPushButton("Save Template")
        self.save_template_button.clicked.connect(self._save_template)
        
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo, stretch=1)
        template_layout.addWidget(self.load_template_button)
        template_layout.addWidget(self.save_template_button)
        layout.addLayout(template_layout)
        
        # Execute button
        self.execute_button = QPushButton("✅ Execute Operation")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.clicked.connect(self._execute_operation)
        self.execute_button.setEnabled(False)
        layout.addWidget(self.execute_button)
        
        # Initial UI state
        self._on_operation_changed("CREATE")
        self._refresh_templates()
    
    def set_client(self, client):
        """Set the Dataverse client"""
        self.client = client
        self.execute_button.setEnabled(True)
    
    def _on_operation_changed(self, operation: str):
        """Handle operation type change"""
        # Show/hide record ID field based on operation
        needs_id = operation in ["READ", "UPDATE", "DELETE"]
        self.record_id_label.setVisible(needs_id)
        self.record_id_input.setVisible(needs_id)
        
        # Show/hide data field based on operation
        needs_data = operation in ["CREATE", "UPDATE"]
        self.data_editor.setVisible(needs_data)
        self.data_editor.parent().setVisible(needs_data)
    
    def _execute_operation(self):
        """Execute the selected operation"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        # Get inputs
        operation = self.op_combo.currentText()
        table_name = self.table_input.text().strip()
        record_id = self.record_id_input.text().strip()
        data_text = self.data_editor.toPlainText().strip()
        
        # Validate
        if not table_name:
            QMessageBox.warning(self, "Missing Input", "Please enter table name.")
            return
        
        if operation in ["READ", "UPDATE", "DELETE"] and not record_id:
            QMessageBox.warning(self, "Missing Input", "Please enter record ID.")
            return
        
        # Parse JSON data
        data = {}
        if operation in ["CREATE", "UPDATE"] and data_text:
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON parsing error:\n{str(e)}")
                return
        
        # Validate payload if enabled
        if self.validate_checkbox.isChecked() and operation in ["CREATE", "UPDATE"] and data:
            validation_result = self._validate_payload(table_name, data, operation)
            if not validation_result["valid"]:
                # Create user-friendly error message
                user_friendly_msg = ErrorFormatter.create_user_friendly_message(
                    validation_result["errors"],
                    validation_result.get("corrections", [])
                )
                
                # Technical details (raw errors)
                technical_details = "\n".join(validation_result["errors"])
                
                # Show dialog with proper sizing
                has_corrections = bool(validation_result.get("auto_correction_available"))
                title = "Validation Errors - Corrections Available" if has_corrections else "Validation Errors"
                
                result = ValidationErrorDialog.show_error(
                    self,
                    title=title,
                    message=user_friendly_msg,
                    detailed_info=technical_details,
                    has_corrections=has_corrections
                )
                
                if result == "apply":
                    # Use corrected payload
                    data = validation_result["corrected"]
                    self.data_editor.setPlainText(json.dumps(data, indent=2))
                elif result == "cancel":
                    return
                # "proceed" continues with original data
        
        # Disable button
        self.execute_button.setEnabled(False)
        self.execute_button.setText("⏳ Executing...")
        
        # Start operation in background
        self.operation_thread = CRUDOperationThread(
            self.client,
            operation,
            table_name,
            data,
            record_id
        )
        
        self.operation_thread.success.connect(self._on_operation_success)
        self.operation_thread.error.connect(self._on_operation_error)
        self.operation_thread.start()
    
    def _on_operation_success(self, result: dict):
        """Handle successful operation"""
        # Re-enable button
        self.execute_button.setEnabled(True)
        self.execute_button.setText("✅ Execute Operation")
        
        # Prepare operation data
        operation_data = {
            "type": f"CRUD - {self.op_combo.currentText()}",
            "table": self.table_input.text(),
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "result": result
        }
        
        # Emit signal
        self.operation_executed.emit(operation_data)
    
    def _on_operation_error(self, error_msg: str):
        """Handle operation error"""
        # Re-enable button
        self.execute_button.setEnabled(True)
        self.execute_button.setText("✅ Execute Operation")
        
        # Format error for user-friendly display
        formatted_error = ErrorFormatter.format_dataverse_error(error_msg)
        
        # Create user-friendly message
        user_message = f"{formatted_error['title']}\n\n{formatted_error['message']}"
        
        if formatted_error.get('field'):
            user_message += f"\n\nField: {formatted_error['field']}"
        
        user_message += f"\n\n💡 {formatted_error['action']}"
        
        # Show dialog with scrollable error details
        result = ValidationErrorDialog.show_error(
            self,
            title=formatted_error['title'],
            message=user_message,
            detailed_info=formatted_error['detailed_info'],
            has_corrections=False
        )
        
        # Prepare operation data for history
        operation_data = {
            "type": f"CRUD - {self.op_combo.currentText()}",
            "table": self.table_input.text(),
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": formatted_error['title'],
            "error_details": formatted_error['detailed_info']
        }
        
        # Emit signal
        self.operation_executed.emit(operation_data)
        
    
    def _refresh_templates(self):
        """Refresh template list"""
        templates = self.template_manager.list_templates()
        
        self.template_combo.clear()
        self.template_combo.addItem("-- No Template --")
        self.template_combo.addItems(templates)
    
    def _load_template(self):
        """Load selected template"""
        template_name = self.template_combo.currentText()
        
        if template_name == "-- No Template --":
            return
        
        template_data = self.template_manager.load_template(template_name)
        
        if template_data:
            # Populate fields from template
            if template_data.get("type") == "crud":
                self.op_combo.setCurrentText(template_data.get("operation", "CREATE"))
                self.table_input.setText(template_data.get("table_name", ""))
                self.record_id_input.setText(template_data.get("record_id", ""))
                
                data = template_data.get("data", {})
                self.data_editor.setPlainText(json.dumps(data, indent=2))
    
    def _save_template(self):
        """Save current configuration as template"""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get template name
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        
        if ok and name:
            # Create template
            template_data = self.template_manager.create_crud_template(
                self.op_combo.currentText(),
                self.table_input.text(),
                json.loads(self.data_editor.toPlainText()) if self.data_editor.toPlainText() else {},
                self.record_id_input.text() if self.record_id_input.text() else None
            )
            
            # Save
            if self.template_manager.save_template(name, template_data):
                self._refresh_templates()
                QMessageBox.information(self, "Saved", f"Template '{name}' saved successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to save template.")
    
    def load_data(self, json_data: dict):
        """Load data from external source (e.g., Excel mapper)"""
        self.op_combo.setCurrentText("CREATE")
        self.data_editor.setPlainText(json.dumps(json_data, indent=2))
    
    def _validate_payload(self, table_name: str, payload: dict, operation: str) -> dict:
        """
        Validate payload against metadata with autocorrect suggestions
        Returns: {"valid": bool, "errors": List[str], "corrected": dict, "corrections": List[str]}
        """
        if not self.client:
            return {"valid": True, "errors": [], "corrected": payload, "corrections": []}
        
        try:
            # Fetch entity metadata
            result = self.client.fetch_entity_attributes(table_name)
            
            if not result.get("success"):
                # Cannot validate without metadata - proceed with warning
                return {
                    "valid": True,
                    "errors": ["Warning: Could not fetch metadata for validation"],
                    "corrected": payload,
                    "corrections": []
                }
            
            # Create validator
            validator = PayloadValidator(result, entity_plural_name=None)
            
            # Try to autocorrect payload
            corrected_payload, corrections = validator.autocorrect_payload(payload)
            
            # Validate original
            is_valid, errors = validator.validate_payload(payload, operation)
            
            # If not valid, try validating corrected version
            if not is_valid:
                corrected_valid, corrected_errors = validator.validate_payload(corrected_payload, operation)
                
                # If corrections help, suggest them
                if corrected_valid and corrections:
                    return {
                        "valid": False,
                        "errors": errors,
                        "corrected": corrected_payload,
                        "corrections": corrections,
                        "auto_correction_available": True
                    }
            
            return {
                "valid": is_valid,
                "errors": errors,
                "corrected": corrected_payload if corrections else payload,
                "corrections": corrections
            }
        
        except Exception as e:
            # If validation fails, return warning but allow to proceed
            return {
                "valid": True,
                "errors": [f"Warning: Validation error: {str(e)}"],
                "corrected": payload,
                "corrections": []
            }

