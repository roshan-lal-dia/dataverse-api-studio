"""
Results Tab
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QTabWidget, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import json
import csv


class ResultsTab(QWidget):
    """Results display tab"""
    
    def __init__(self):
        super().__init__()
        
        self.current_result = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Result display tabs
        self.result_tabs = QTabWidget()
        
        # JSON view
        json_widget = QWidget()
        json_layout = QVBoxLayout(json_widget)
        
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setPlaceholderText("Results will appear here...")
        json_layout.addWidget(self.json_display)
        
        # Table view
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        self.table_display = QTableWidget()
        self.table_display.setAlternatingRowColors(True)
        table_layout.addWidget(self.table_display)
        
        self.result_tabs.addTab(json_widget, "JSON View")
        self.result_tabs.addTab(table_widget, "Table View")
        
        layout.addWidget(self.result_tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.export_json_button = QPushButton("💾 Export JSON")
        self.export_json_button.clicked.connect(self._export_json)
        button_layout.addWidget(self.export_json_button)
        
        self.export_csv_button = QPushButton("💾 Export CSV")
        self.export_csv_button.clicked.connect(self._export_csv)
        button_layout.addWidget(self.export_csv_button)
        
        self.copy_button = QPushButton("📋 Copy to Clipboard")
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def display_result(self, operation_data: dict):
        """Display operation result"""
        self.current_result = operation_data
        
        # Display in JSON view
        json_text = json.dumps(operation_data, indent=2)
        self.json_display.setPlainText(json_text)
        
        # Display in table view if applicable
        result = operation_data.get("result", {})
        
        if "data" in result:
            data = result["data"]
            
            # Handle list of records (query results)
            if isinstance(data, list) and data:
                self._populate_table(data)
            # Handle single record
            elif isinstance(data, dict):
                self._populate_table([data])
    
    def _populate_table(self, records: list):
        """Populate table widget with records"""
        if not records:
            return
        
        # Get all unique keys
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        
        headers = sorted(list(all_keys))
        
        # Setup table
        self.table_display.setRowCount(len(records))
        self.table_display.setColumnCount(len(headers))
        self.table_display.setHorizontalHeaderLabels(headers)
        
        # Populate data
        for row_idx, record in enumerate(records):
            for col_idx, header in enumerate(headers):
                value = record.get(header, "")
                
                # Convert to string for display
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value) if value is not None else ""
                
                item = QTableWidgetItem(value_str)
                self.table_display.setItem(row_idx, col_idx, item)
        
        # Resize columns
        self.table_display.resizeColumnsToContents()
    
    def _export_json(self):
        """Export results as JSON"""
        if not self.current_result:
            QMessageBox.warning(self, "No Data", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON",
            "results.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_result, f, indent=2)
                
                QMessageBox.information(self, "Exported", f"Results exported to {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
    
    def _export_csv(self):
        """Export results as CSV"""
        if not self.current_result:
            QMessageBox.warning(self, "No Data", "No results to export.")
            return
        
        # Extract data
        result = self.current_result.get("result", {})
        data = result.get("data", [])
        
        if not data:
            QMessageBox.warning(self, "No Data", "No tabular data to export.")
            return
        
        if not isinstance(data, list):
            data = [data]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "results.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Get all keys
                all_keys = set()
                for record in data:
                    all_keys.update(record.keys())
                
                headers = sorted(list(all_keys))
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    
                    for record in data:
                        # Convert complex types to strings
                        row = {}
                        for key in headers:
                            value = record.get(key, "")
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value)
                            else:
                                row[key] = value
                        
                        writer.writerow(row)
                
                QMessageBox.information(self, "Exported", f"Results exported to {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")
    
    def _copy_to_clipboard(self):
        """Copy JSON results to clipboard"""
        from PyQt6.QtWidgets import QApplication
        
        if not self.current_result:
            QMessageBox.warning(self, "No Data", "No results to copy.")
            return
        
        json_text = json.dumps(self.current_result, indent=2)
        
        clipboard = QApplication.clipboard()
        clipboard.setText(json_text)
        
        QMessageBox.information(self, "Copied", "Results copied to clipboard.")
    
    def export_results(self):
        """Export results (called from menu)"""
        self._export_json()
