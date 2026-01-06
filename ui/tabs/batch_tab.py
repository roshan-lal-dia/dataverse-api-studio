"""
Batch Operations Tab with validation support and progress indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QFileDialog, QCheckBox, QProgressBar, QLabel, QComboBox, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, QThread
from datetime import datetime
from typing import Optional
import json
import re

from utils.payload_validator import PayloadValidator


class BatchOperationThread(QThread):
    """Background thread for batch operations with progress"""
    
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # (percentage, status_message)
    
    def __init__(self, client, operations):
        super().__init__()
        self.client = client
        self.operations = operations
    
    def run(self):
        """Execute batch operation"""
        try:
            self.progress.emit(0, "Starting batch operation...")
            
            self.progress.emit(30, f"Sending {len(self.operations)} operations...")
            
            result = self.client.batch_operation(self.operations)
            
            self.progress.emit(90, "Processing response...")
            
            if result.get("success"):
                self.progress.emit(100, "Completed successfully")
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
        
        # Mode selector (Manual or Bulk Operations)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Manual JSON", "Bulk Update", "Bulk Delete"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Batch operations editor (for Manual mode)
        self.editor_group = QGroupBox("Batch Operations (JSON Array)")
        editor_layout = QVBoxLayout()
        
        self.batch_editor = QTextEdit()
        self.batch_editor.setPlaceholderText('[\n  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Account 1"}},\n  {"method": "POST", "url": "/api/data/v9.2/accounts", "data": {"name": "Account 2"}}\n]')
        self.batch_editor.setMinimumHeight(300)
        editor_layout.addWidget(self.batch_editor)
        
        self.editor_group.setLayout(editor_layout)
        layout.addWidget(self.editor_group)
        
        # Bulk operations panel (for Bulk Update/Delete modes)
        self.bulk_group = QGroupBox("Bulk Operations with Filter")
        bulk_layout = QVBoxLayout()
        
        # Entity
        entity_layout = QHBoxLayout()
        entity_layout.addWidget(QLabel("Entity:"))
        self.bulk_entity_input = QLineEdit()
        self.bulk_entity_input.setPlaceholderText("e.g., account, contact")
        entity_layout.addWidget(self.bulk_entity_input)
        bulk_layout.addLayout(entity_layout)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter (OData):"))
        self.bulk_filter_input = QLineEdit()
        self.bulk_filter_input.setPlaceholderText("e.g., statecode eq 0 and revenue gt 1000000")
        filter_layout.addWidget(self.bulk_filter_input)
        bulk_layout.addLayout(filter_layout)
        
        # Update data (only for Bulk Update)
        self.update_data_label = QLabel("Update Data (JSON):")
        bulk_layout.addWidget(self.update_data_label)
        
        self.bulk_update_data = QTextEdit()
        self.bulk_update_data.setPlaceholderText('{"fieldname": "new_value"}')
        self.bulk_update_data.setMaximumHeight(100)
        bulk_layout.addWidget(self.bulk_update_data)
        
        # Preview button
        self.preview_button = QPushButton("👁️ Preview Records")
        self.preview_button.clicked.connect(self._preview_bulk_records)
        bulk_layout.addWidget(self.preview_button)
        
        # Preview results
        self.preview_label = QLabel("")
        bulk_layout.addWidget(self.preview_label)
        
        self.bulk_group.setLayout(bulk_layout)
        self.bulk_group.setVisible(False)
        layout.addWidget(self.bulk_group)
        
        # Validation checkbox
        validation_layout = QHBoxLayout()
        self.validate_checkbox = QCheckBox("✓ Validate payloads before execution")
        self.validate_checkbox.setChecked(True)
        self.validate_checkbox.setToolTip("Check each operation payload against metadata")
        validation_layout.addWidget(self.validate_checkbox)
        validation_layout.addStretch()
        layout.addLayout(validation_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_file_button = QPushButton("📂 Load from File")
        self.load_file_button.clicked.connect(self._load_from_file)
        button_layout.addWidget(self.load_file_button)
        
        self.execute_button = QPushButton("⚡ Execute Batch")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.clicked.connect(self._handle_execute)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button, stretch=1)
        
        layout.addLayout(button_layout)
        
        # Progress indicator
        progress_group = QGroupBox("Operation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
    
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
    
    def _handle_execute(self):
        """Handle execute button click based on mode"""
        mode = self.mode_combo.currentText()
        
        if mode == "Manual JSON":
            self._execute_batch()
        else:
            self._execute_bulk_operations()
    
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
        
        # Validate operations if enabled
        if self.validate_checkbox.isChecked():
            validation_result = self._validate_batch_operations(operations)
            
            if validation_result["errors"]:
                error_msg = f"Found {len(validation_result['errors'])} validation error(s):\n\n"
                error_msg += "\n".join(f"• Operation {i+1}: {err}" 
                                     for i, err in validation_result['errors'][:10])  # Show first 10
                
                if len(validation_result['errors']) > 10:
                    error_msg += f"\n... and {len(validation_result['errors']) - 10} more errors"
                
                reply = QMessageBox.warning(
                    self,
                    "Validation Errors",
                    error_msg + "\n\nDo you want to proceed anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # Disable button and show progress
        self.execute_button.setEnabled(False)
        self.execute_button.setText("⏳ Executing Batch...")
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start operation
        self.operation_thread = BatchOperationThread(self.client, operations)
        self.operation_thread.success.connect(self._on_batch_success)
        self.operation_thread.error.connect(self._on_batch_error)
        self.operation_thread.progress.connect(self._on_batch_progress)
        self.operation_thread.start()
    
    def _on_batch_progress(self, percentage: int, message: str):
        """Update progress bar"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
    
    def _on_batch_success(self, result: dict):
        """Handle successful batch operation"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("⚡ Execute Batch")
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
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
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
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
    
    def _validate_batch_operations(self, operations: list) -> dict:
        """
        Validate batch operations against metadata
        Returns: {"errors": List[Tuple[int, str]]}  # (operation_index, error_message)
        """
        errors = []
        
        if not self.client:
            return {"errors": []}
        
        try:
            for idx, operation in enumerate(operations):
                method = operation.get("method", "").upper()
                
                # Only validate POST (CREATE) and PATCH (UPDATE)
                if method not in ["POST", "PATCH"]:
                    continue
                
                # Extract entity name from URL
                url = operation.get("url", "")
                entity_name = self._extract_entity_from_url(url)
                
                if not entity_name:
                    continue
                
                # Get payload
                data = operation.get("data", {})
                
                if not data:
                    continue
                
                # Fetch metadata
                result = self.client.fetch_entity_attributes(entity_name)
                
                if not result.get("success"):
                    continue
                
                # Validate
                validator = PayloadValidator(result)
                op_type = "CREATE" if method == "POST" else "UPDATE"
                is_valid, validation_errors = validator.validate_payload(data, op_type)
                
                if not is_valid:
                    for error in validation_errors:
                        errors.append((idx, error))
        
        except Exception as e:
            # Don't fail the whole batch validation on error
            pass
        
        return {"errors": errors}
    
    def _extract_entity_from_url(self, url: str) -> Optional[str]:
        """
        Extract entity name from batch operation URL
        e.g., "/api/data/v9.2/accounts" -> "account"
        """
        try:
            # Match pattern like /api/data/v9.2/entityname or /api/data/v9.2/entityname(id)
            match = re.search(r'/api/data/v\d+\.\d+/([a-z_]+)', url, re.IGNORECASE)
            if match:
                entity_set_name = match.group(1)
                
                # Try to find logical name from entity set name
                # This is a simple reverse lookup - may not work for all irregular plurals
                if entity_set_name.endswith('s'):
                    return entity_set_name[:-1]  # Remove 's'
                elif entity_set_name.endswith('ies'):
                    return entity_set_name[:-3] + 'y'  # opportunities -> opportunity
                else:
                    return entity_set_name
        except:
            pass
        
        return None
    
    def _on_mode_changed(self, mode: str):
        """Handle mode change"""
        if mode == "Manual JSON":
            self.editor_group.setVisible(True)
            self.bulk_group.setVisible(False)
            self.load_file_button.setVisible(True)
        else:
            self.editor_group.setVisible(False)
            self.bulk_group.setVisible(True)
            self.load_file_button.setVisible(False)
            
            # Show/hide update data based on mode
            is_update = mode == "Bulk Update"
            self.update_data_label.setVisible(is_update)
            self.bulk_update_data.setVisible(is_update)
    
    def _preview_bulk_records(self):
        """Preview records that match the filter"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        entity = self.bulk_entity_input.text().strip()
        filter_query = self.bulk_filter_input.text().strip()
        
        if not entity:
            QMessageBox.warning(self, "Missing Input", "Please enter entity name.")
            return
        
        try:
            # Query with filter (limited to 10 for preview)
            result = self.client.read_multiple(
                entity,
                filter_query=filter_query if filter_query else None,
                select=None,
                top=10
            )
            
            if result.get("success"):
                records = result.get("data", [])
                count = len(records)
                self.preview_label.setText(
                    f"✅ Found {count} records (showing first 10). "
                    f"Click Execute to apply operation to all matching records."
                )
                self.preview_label.setStyleSheet("color: green;")
            else:
                self.preview_label.setText(f"❌ Error: {result.get('error', 'Unknown error')}")
                self.preview_label.setStyleSheet("color: red;")
        
        except Exception as e:
            self.preview_label.setText(f"❌ Error: {str(e)}")
            self.preview_label.setStyleSheet("color: red;")
    
    def _execute_bulk_operations(self):
        """Execute bulk update or delete based on filter"""
        mode = self.mode_combo.currentText()
        entity = self.bulk_entity_input.text().strip()
        filter_query = self.bulk_filter_input.text().strip()
        
        if not entity:
            QMessageBox.warning(self, "Missing Input", "Please enter entity name.")
            return
        
        # Confirm destructive operation
        confirm_msg = f"This will {mode.lower()} ALL records in {entity}"
        if filter_query:
            confirm_msg += f" matching filter:\n{filter_query}"
        confirm_msg += "\n\nThis operation CANNOT be undone. Continue?"
        
        reply = QMessageBox.warning(
            self,
            "Confirm Destructive Operation",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Fetch all matching records
            result = self.client.read_multiple(
                entity,
                filter_query=filter_query if filter_query else None,
                select="*",  # Get all fields for update
                top=1000  # Limit to 1000 for safety
            )
            
            if not result.get("success"):
                QMessageBox.critical(
                    self,
                    "Query Failed",
                    f"Failed to fetch records:\n{result.get('error', 'Unknown error')}"
                )
                return
            
            records = result.get("data", [])
            
            if not records:
                QMessageBox.information(self, "No Records", "No records match the filter.")
                return
            
            # Get EntitySetName
            entity_set_name = self.client.get_entity_set_name(entity)
            if not entity_set_name:
                entity_set_name = f"{entity}s"
            
            # Build batch operations
            operations = []
            
            if mode == "Bulk Delete":
                # Create DELETE operations for each record
                for record in records:
                    record_id = record.get(f"{entity}id") or record.get("id")
                    if record_id:
                        operations.append({
                            "method": "DELETE",
                            "url": f"/api/data/v9.2/{entity_set_name}({record_id})"
                        })
            
            elif mode == "Bulk Update":
                # Parse update data
                update_text = self.bulk_update_data.toPlainText().strip()
                if not update_text:
                    QMessageBox.warning(self, "Missing Data", "Please enter update data.")
                    return
                
                try:
                    update_data = json.loads(update_text)
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Invalid JSON", f"Update data parsing error:\n{str(e)}")
                    return
                
                # Create PATCH operations for each record
                for record in records:
                    record_id = record.get(f"{entity}id") or record.get("id")
                    if record_id:
                        operations.append({
                            "method": "PATCH",
                            "url": f"/api/data/v9.2/{entity_set_name}({record_id})",
                            "data": update_data
                        })
            
            if not operations:
                QMessageBox.warning(self, "No Operations", "No operations could be generated.")
                return
            
            # Show final confirmation with count
            final_confirm = QMessageBox.question(
                self,
                "Final Confirmation",
                f"About to execute {len(operations)} {mode.lower()} operations.\n\nProceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if final_confirm != QMessageBox.StandardButton.Yes:
                return
            
            # Load operations into editor and switch to manual mode for execution
            self.batch_editor.setPlainText(json.dumps(operations, indent=2))
            self.mode_combo.setCurrentText("Manual JSON")
            
            # Execute
            self._execute_batch()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to build bulk operations:\n{str(e)}")

