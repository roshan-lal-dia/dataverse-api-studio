"""
Entity Explorer Tab - Comprehensive entity record exploration UI
Displays all attributes, values, relationships, and related records
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QGroupBox, QMessageBox, QProgressBar, QSplitter, QListWidget,
    QListWidgetItem, QHeaderView, QDialog, QSpinBox, QCheckBox, QScrollArea,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QIcon, QColor, QFont
from datetime import datetime
import json

from client.entity_explorer import EntityExplorer
from utils.entity_details_formatter import EntityDetailsFormatter


class EntityExplorerThread(QThread):
    """Background thread for entity metadata and record fetching"""
    
    progress_update = pyqtSignal(str)
    metadata_loaded = pyqtSignal(dict)
    record_loaded = pyqtSignal(dict, dict)  # record_data, attribute_metadata
    relationships_loaded = pyqtSignal(dict, dict)  # relationships, attribute_metadata
    error = pyqtSignal(str)
    completed = pyqtSignal()
    
    def __init__(self, explorer: EntityExplorer, entity_name: str, record_id: str):
        super().__init__()
        self.explorer = explorer
        self.entity_name = entity_name
        self.record_id = record_id
    
    def run(self):
        try:
            # 1. Fetch complete entity metadata
            self.progress_update.emit("📋 Loading entity metadata...")
            metadata_result = self.explorer.fetch_complete_entity_metadata(self.entity_name)
            
            if not metadata_result.get("success"):
                self.error.emit(metadata_result.get("error", "Failed to fetch metadata"))
                return
            
            self.metadata_loaded.emit(metadata_result)
            
            # 2. Fetch record data
            self.progress_update.emit(f"📦 Loading record {self.record_id}...")
            record_result = self.explorer.fetch_record_with_attributes(self.entity_name, self.record_id)
            
            if not record_result.get("success"):
                self.error.emit(record_result.get("error", "Failed to fetch record"))
                return
            
            # Get attribute metadata map
            attr_map = self.explorer.get_attribute_metadata_map(self.entity_name)
            self.record_loaded.emit(record_result.get("record", {}), attr_map)
            
            # 3. Load relationships
            self.progress_update.emit("🔗 Loading relationships...")
            self.relationships_loaded.emit(metadata_result.get("relationships", {}), attr_map)
            
            self.progress_update.emit("✅ Done!")
            self.completed.emit()
        
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


class RelatedRecordsDialog(QDialog):
    """Dialog to display related records from a relationship"""
    
    def __init__(self, parent=None, relationship_name: str = "", records: list = None):
        super().__init__(parent)
        self.setWindowTitle(f"Related Records - {relationship_name}")
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<b>{relationship_name}</b> ({len(records or [])} records)")
        layout.addWidget(header)
        
        # Table
        table = QTableWidget()
        records = records or []
        
        if records:
            # Get all unique column names
            columns = set()
            for record in records:
                columns.update(record.keys())
            
            columns = sorted([c for c in columns if not c.startswith("@")])
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                for col, column in enumerate(columns):
                    value = record.get(column, "")
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)[:50]
                    item = QTableWidgetItem(str(value))
                    table.setItem(row, col, item)
            
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class EntityExplorerTab(QWidget):
    """Entity Explorer Tab - Comprehensive record exploration"""
    
    # Signals
    authenticated = pyqtSignal(object)  # Emitted when client is set
    
    def __init__(self):
        super().__init__()
        self.explorer = None
        self.current_entity = None
        self.current_record_id = None
        self.current_metadata = None
        self.current_record_data = None
        self.current_relationships = None
        self.current_attr_metadata = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # ===== Input Section =====
        input_group = QGroupBox("🔍 Record Lookup")
        input_layout = QHBoxLayout()
        
        # Entity selector
        input_layout.addWidget(QLabel("Entity:"))
        self.entity_combo = QComboBox()
        self.entity_combo.setMinimumWidth(150)
        self.entity_combo.currentTextChanged.connect(self._on_entity_changed)
        input_layout.addWidget(self.entity_combo)
        
        # Record ID input
        input_layout.addWidget(QLabel("Record GUID:"))
        self.record_id_input = QLineEdit()
        self.record_id_input.setPlaceholderText("Enter GUID or unique identifier")
        self.record_id_input.setMinimumWidth(300)
        input_layout.addWidget(self.record_id_input)
        
        # Search button
        self.search_btn = QPushButton("🔎 Load Record")
        self.search_btn.setMinimumWidth(120)
        self.search_btn.clicked.connect(self._on_search_clicked)
        input_layout.addWidget(self.search_btn)
        
        input_layout.addStretch()
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # ===== Main Content with Splitter =====
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Entity Info
        left_group = QGroupBox("📋 Entity Information")
        left_layout = QVBoxLayout()
        
        self.entity_info_text = QTextEdit()
        self.entity_info_text.setReadOnly(True)
        self.entity_info_text.setMaximumHeight(150)
        left_layout.addWidget(self.entity_info_text)
        
        left_group.setLayout(left_layout)
        splitter.addWidget(left_group)
        
        # Center panel - Tabs for different views
        self.content_tabs = QTabWidget()
        
        # Tab 1: Attributes Table
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(6)
        self.attributes_table.setHorizontalHeaderLabels(
            ["Attribute", "Type", "Value", "Description", "Required", "Valid For"]
        )
        self.attributes_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.content_tabs.addTab(self.attributes_table, "📝 Attributes")
        
        # Tab 2: Relationships Tree
        relationships_widget = QWidget()
        rel_layout = QVBoxLayout()
        
        self.relationships_list = QListWidget()
        self.relationships_list.itemClicked.connect(self._on_relationship_clicked)
        rel_layout.addWidget(QLabel("Available Relationships:"))
        rel_layout.addWidget(self.relationships_list)
        
        relationships_widget.setLayout(rel_layout)
        self.content_tabs.addTab(relationships_widget, "🔗 Relationships")
        
        # Tab 3: JSON View
        self.json_text = QTextEdit()
        self.json_text.setReadOnly(True)
        self.json_text.setFont(QFont("Courier", 9))
        self.content_tabs.addTab(self.json_text, "📦 JSON View")
        
        # Tab 4: HTML View (for reports)
        self.html_text = QTextEdit()
        self.html_text.setReadOnly(True)
        self.content_tabs.addTab(self.html_text, "🌐 HTML Summary")
        
        splitter.addWidget(self.content_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # ===== Status and Actions =====
        status_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Action buttons
        self.save_response_btn = QPushButton("💾 Save Response")
        self.save_response_btn.clicked.connect(self._on_save_response)
        self.save_response_btn.setEnabled(False)
        status_layout.addWidget(self.save_response_btn)
        
        self.export_json_btn = QPushButton("📤 Export JSON")
        self.export_json_btn.clicked.connect(self._on_export_json)
        self.export_json_btn.setEnabled(False)
        status_layout.addWidget(self.export_json_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.setEnabled(False)
        status_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
    
    def set_client(self, explorer: EntityExplorer):
        """Set the entity explorer client"""
        self.explorer = explorer
        
        if explorer:
            # Load entity list
            self._load_entity_list()
            self.authenticated.emit(explorer)
    
    def _load_entity_list(self):
        """Load list of entities into the combo box"""
        if not self.explorer:
            return
        
        entities = self.explorer.get_entity_list(use_cache=True)
        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()
        self.entity_combo.addItems(entities)
        self.entity_combo.blockSignals(False)
        
        # Try to select 'lmdm_location' if it exists
        index = self.entity_combo.findText("lmdm_location")
        if index >= 0:
            self.entity_combo.setCurrentIndex(index)
    
    def _on_entity_changed(self, entity_name: str):
        """Called when entity selection changes"""
        self.current_entity = entity_name
        self.entity_info_text.clear()
        self.attributes_table.setRowCount(0)
        self.relationships_list.clear()
    
    def _on_search_clicked(self):
        """Search for and load a record"""
        if not self.explorer:
            QMessageBox.warning(self, "Error", "Not authenticated. Please authenticate first.")
            return
        
        entity = self.entity_combo.currentText()
        record_id = self.record_id_input.text().strip()
        
        if not entity or not record_id:
            QMessageBox.warning(self, "Error", "Please select an entity and enter a record ID.")
            return
        
        # Start loading in background
        self._load_entity_details(entity, record_id)
    
    def _load_entity_details(self, entity_name: str, record_id: str):
        """Load entity details using background thread"""
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading...")
        
        # Create and start thread
        thread = EntityExplorerThread(self.explorer, entity_name, record_id)
        thread.progress_update.connect(self._update_progress)
        thread.metadata_loaded.connect(self._on_metadata_loaded)
        thread.record_loaded.connect(self._on_record_loaded)
        thread.relationships_loaded.connect(self._on_relationships_loaded)
        thread.error.connect(self._on_load_error)
        thread.completed.connect(self._on_load_completed)
        
        self._loader_thread = thread
        thread.start()
    
    def _update_progress(self, message: str):
        """Update progress message"""
        self.status_label.setText(message)
    
    def _on_metadata_loaded(self, metadata: dict):
        """Handle metadata loaded"""
        self.current_metadata = metadata
        self.current_entity = metadata.get("entity", {}).get("LogicalName", "")
        
        # Display entity info
        entity = metadata.get("entity", {})
        info = f"""
        <b>{entity.get('DisplayName', entity.get('LogicalName'))}</b>
        <br/>Logical Name: <code>{entity.get('LogicalName')}</code>
        <br/>Entity Set: <code>{entity.get('EntitySetName')}</code>
        <br/>Primary ID: <code>{entity.get('PrimaryIdAttribute')}</code>
        <br/>Primary Name: <code>{entity.get('PrimaryNameAttribute')}</code>
        <br/>Attributes: {len(metadata.get('attributes', []))}
        """
        self.entity_info_text.setText(info)
    
    def _on_record_loaded(self, record_data: dict, attr_metadata: dict):
        """Handle record data loaded"""
        self.current_record_data = record_data
        self.current_attr_metadata = attr_metadata
        
        # Get record ID from metadata
        if self.current_metadata:
            pk_attr = self.current_metadata.get("entity", {}).get("PrimaryIdAttribute", "")
            self.current_record_id = record_data.get(pk_attr, "")
        
        # Populate attributes table
        self._populate_attributes_table(record_data, attr_metadata)
        
        # Generate JSON view
        self._generate_json_view(record_data)
    
    def _on_relationships_loaded(self, relationships: dict, attr_metadata: dict):
        """Handle relationships loaded"""
        self.current_relationships = relationships
        
        # Populate relationships list
        self._populate_relationships_list(relationships)
        
        # Generate HTML summary
        if self.current_metadata and self.current_record_data:
            self._generate_html_summary()
    
    def _populate_attributes_table(self, record_data: dict, attr_metadata: dict):
        """Populate the attributes table with record data"""
        self.attributes_table.setRowCount(0)
        
        if not self.current_metadata:
            return
        
        attributes = self.current_metadata.get("attributes", [])
        row = 0
        
        for attr in attributes:
            attr_name = attr.get("LogicalName", "")
            if not attr_name:
                continue
            
            attr_type = attr.get("AttributeType", "String")
            attr_value = record_data.get(attr_name, None)
            
            # Format the attribute row
            formatted = EntityDetailsFormatter.format_attribute_row(
                attr_name, attr, attr_value
            )
            
            # Add to table
            self.attributes_table.insertRow(row)
            
            # Attribute name with icon
            name_item = QTableWidgetItem(f"{formatted['type_icon']} {formatted['attribute_name']}")
            name_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.attributes_table.setItem(row, 0, name_item)
            
            # Type
            type_item = QTableWidgetItem(formatted["type"])
            self.attributes_table.setItem(row, 1, type_item)
            
            # Value
            value_item = QTableWidgetItem(formatted["value"])
            if formatted["value"] == "∅":
                value_item.setForeground(QColor("gray"))
            self.attributes_table.setItem(row, 2, value_item)
            
            # Description
            desc_item = QTableWidgetItem(formatted["description"])
            self.attributes_table.setItem(row, 3, desc_item)
            
            # Required
            req_item = QTableWidgetItem("✓" if formatted["required"] else "")
            if formatted["required"]:
                req_item.setForeground(QColor("red"))
            self.attributes_table.setItem(row, 4, req_item)
            
            # Valid for
            valid_text = []
            if formatted["is_valid_create"]:
                valid_text.append("C")
            if formatted["is_valid_update"]:
                valid_text.append("U")
            valid_item = QTableWidgetItem("/".join(valid_text))
            self.attributes_table.setItem(row, 5, valid_item)
            
            row += 1
    
    def _populate_relationships_list(self, relationships: dict):
        """Populate the relationships list"""
        self.relationships_list.clear()
        
        if not relationships:
            return
        
        # Many-to-One relationships
        for rel in relationships.get("many_to_one", []):
            formatted = EntityDetailsFormatter.format_relationship(rel, "many_to_one")
            item = QListWidgetItem(f"🔗 {formatted['schema_name']}")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "many_to_one", "data": rel})
            self.relationships_list.addItem(item)
        
        # One-to-Many relationships
        for rel in relationships.get("one_to_many", []):
            formatted = EntityDetailsFormatter.format_relationship(rel, "one_to_many")
            item = QListWidgetItem(f"1️⃣➡️🔢 {formatted['schema_name']}")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "one_to_many", "data": rel})
            self.relationships_list.addItem(item)
        
        # Many-to-Many relationships
        for rel in relationships.get("many_to_many", []):
            formatted = EntityDetailsFormatter.format_relationship(rel, "many_to_many")
            item = QListWidgetItem(f"🔀 {formatted['schema_name']}")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "many_to_many", "data": rel})
            self.relationships_list.addItem(item)
    
    def _on_relationship_clicked(self, item: QListWidgetItem):
        """Handle relationship selection - load related records"""
        rel_data = item.data(Qt.ItemDataRole.UserRole)
        if not rel_data or not self.explorer or not self.current_record_id:
            return
        
        rel_type = rel_data.get("type")
        rel_metadata = rel_data.get("data", {})
        
        # Load related records based on type
        if rel_type == "many_to_one":
            # This is a lookup - show the referenced record
            lookup_value = self.current_record_data.get(rel_metadata.get("ReferencingAttribute"), "")
            if lookup_value:
                entity, guid = self.explorer.extract_lookup_info_from_value(lookup_value)
                if entity and guid:
                    self.entity_combo.blockSignals(True)
                    idx = self.entity_combo.findText(entity)
                    if idx >= 0:
                        self.entity_combo.setCurrentIndex(idx)
                    self.entity_combo.blockSignals(False)
                    self.record_id_input.setText(guid)
                    self._on_search_clicked()
        
        elif rel_type in ["one_to_many", "many_to_many"]:
            # Load related records
            nav_property = rel_metadata.get("ReferencingEntityNavigationPropertyName") or rel_metadata.get("Entity1NavigationPropertyName", "")
            
            if nav_property and self.current_record_id:
                result = self.explorer.fetch_related_records(
                    self.current_entity,
                    self.current_record_id,
                    rel_metadata.get("SchemaName", ""),
                    nav_property,
                    max_records=100
                )
                
                if result.get("success"):
                    dialog = RelatedRecordsDialog(
                        self,
                        f"{rel_metadata.get('SchemaName')} - {rel_type}",
                        result.get("records", [])
                    )
                    dialog.exec()
                else:
                    QMessageBox.warning(self, "Error", result.get("error", "Failed to load related records"))
    
    def _generate_json_view(self, record_data: dict):
        """Generate JSON view of record"""
        # Filter out OData properties
        clean_data = {k: v for k, v in record_data.items() if not k.startswith("@")}
        self.json_text.setText(json.dumps(clean_data, indent=2, default=str))
    
    def _generate_html_summary(self):
        """Generate HTML summary"""
        if not self.current_metadata or not self.current_record_data:
            return
        
        # Build attributes with values list
        attributes_with_values = []
        for attr in self.current_metadata.get("attributes", []):
            attr_name = attr.get("LogicalName", "")
            if attr_name:
                attr_value = self.current_record_data.get(attr_name)
                formatted = EntityDetailsFormatter.format_attribute_row(
                    attr_name, attr, attr_value
                )
                attributes_with_values.append(formatted)
        
        # Generate HTML
        html = EntityDetailsFormatter.generate_html_summary(
            self.current_metadata,
            attributes_with_values,
            self.current_relationships or {}
        )
        
        self.html_text.setHtml(html)
    
    def _on_load_error(self, error_msg: str):
        """Handle load error"""
        QMessageBox.critical(self, "Error", error_msg)
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error: " + error_msg)
    
    def _on_load_completed(self):
        """Handle load completion"""
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Ready")
        self.refresh_btn.setEnabled(True)
        self.export_json_btn.setEnabled(True)
        self.save_response_btn.setEnabled(True)
    
    def _on_refresh_clicked(self):
        """Refresh current record"""
        if self.current_entity and self.current_record_id:
            self._load_entity_details(self.current_entity, self.current_record_id)
    
    def _on_save_response(self):
        """Save response in various formats"""
        if not self.current_metadata or not self.current_record_data:
            QMessageBox.warning(self, "Error", "No data to save")
            return
        
        # Create dialog for format selection
        dialog = QDialog(self)
        dialog.setWindowTitle("💾 Save Response")
        dialog.setGeometry(100, 100, 500, 300)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Select format to save:"))
        
        # Format options
        format_group = QGroupBox("Output Format")
        format_layout = QVBoxLayout()
        
        json_option = QPushButton("📦 JSON - Complete Response")
        json_option.setToolTip("Save complete record details as JSON")
        json_option.clicked.connect(lambda: self._save_format("json", dialog))
        format_layout.addWidget(json_option)
        
        html_option = QPushButton("🌐 HTML - Formatted Report")
        html_option.setToolTip("Save as formatted HTML report")
        html_option.clicked.connect(lambda: self._save_format("html", dialog))
        format_layout.addWidget(html_option)
        
        csv_option = QPushButton("📊 CSV - Attributes Table")
        csv_option.setToolTip("Save attributes as CSV file")
        csv_option.clicked.connect(lambda: self._save_format("csv", dialog))
        format_layout.addWidget(csv_option)
        
        txt_option = QPushButton("📄 TXT - Plain Text Summary")
        txt_option.setToolTip("Save as plain text summary")
        txt_option.clicked.connect(lambda: self._save_format("txt", dialog))
        format_layout.addWidget(txt_option)
        
        xml_option = QPushButton("📋 XML - Structured Data")
        xml_option.setToolTip("Save as XML (for ETL systems)")
        xml_option.clicked.connect(lambda: self._save_format("xml", dialog))
        format_layout.addWidget(xml_option)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _save_format(self, format_type: str, parent_dialog: QDialog):
        """Save response in the specified format"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            entity = self.current_entity or "entity"
            default_filename = f"{entity}_{self.current_record_id[:8]}_{timestamp}"
            
            # Define file filters
            filters = {
                "json": "JSON Files (*.json)",
                "html": "HTML Files (*.html)",
                "csv": "CSV Files (*.csv)",
                "txt": "Text Files (*.txt)",
                "xml": "XML Files (*.xml)"
            }
            
            # Open file dialog
            filename, _ = QFileDialog.getSaveFileName(
                parent_dialog,
                f"Save as {format_type.upper()}",
                default_filename,
                filters.get(format_type, "All Files (*.*)")
            )
            
            if not filename:
                return
            
            # Generate content based on format
            content = self._generate_content(format_type)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            parent_dialog.accept()
            QMessageBox.information(self, "Success", f"✅ Saved to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def _generate_content(self, format_type: str) -> str:
        """Generate content in the specified format"""
        # Build attributes with values list
        attributes_with_values = []
        for attr in self.current_metadata.get("attributes", []):
            attr_name = attr.get("LogicalName", "")
            if attr_name:
                attr_value = self.current_record_data.get(attr_name)
                formatted = EntityDetailsFormatter.format_attribute_row(
                    attr_name, attr, attr_value
                )
                attributes_with_values.append(formatted)
        
        if format_type == "json":
            return EntityDetailsFormatter.export_as_json(
                self.current_metadata,
                {"id": self.current_record_id},
                attributes_with_values,
                self.current_relationships or {}
            )
        
        elif format_type == "html":
            return EntityDetailsFormatter.format_as_html(
                self.current_metadata,
                {"id": self.current_record_id},
                attributes_with_values,
                self.current_relationships or {}
            )
        
        elif format_type == "csv":
            return self._generate_csv(attributes_with_values)
        
        elif format_type == "txt":
            return self._generate_text(attributes_with_values)
        
        elif format_type == "xml":
            return self._generate_xml(attributes_with_values)
        
        return ""
    
    def _generate_csv(self, attributes: list) -> str:
        """Generate CSV format"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Attribute Name", "Type", "Value", "Display Value",
            "Description", "Required", "Valid for Create", "Valid for Update"
        ])
        
        # Data rows
        for attr in attributes:
            writer.writerow([
                attr.get("attribute_name", ""),
                attr.get("type", ""),
                attr.get("value", ""),
                attr.get("formatted_value", ""),
                attr.get("description", ""),
                "Yes" if attr.get("required") else "No",
                "Yes" if attr.get("is_valid_create") else "No",
                "Yes" if attr.get("is_valid_update") else "No"
            ])
        
        return output.getvalue()
    
    def _generate_text(self, attributes: list) -> str:
        """Generate plain text format"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"ENTITY RECORD DETAILS")
        lines.append("=" * 80)
        lines.append(f"Entity: {self.current_entity}")
        lines.append(f"Record ID: {self.current_record_id}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append("ATTRIBUTES:")
        lines.append("-" * 80)
        
        for attr in attributes:
            lines.append(f"\n[{attr.get('attribute_name', '')}]")
            lines.append(f"  Type: {attr.get('type', '')}")
            lines.append(f"  Value: {attr.get('value', '')}")
            if attr.get('formatted_value'):
                lines.append(f"  Display: {attr.get('formatted_value')}")
            lines.append(f"  Description: {attr.get('description', '')}")
            lines.append(f"  Required: {'Yes' if attr.get('required') else 'No'}")
        
        if self.current_relationships:
            lines.append("\n" + "=" * 80)
            lines.append("RELATIONSHIPS:")
            lines.append("-" * 80)
            
            for rel_type, rels in self.current_relationships.items():
                lines.append(f"\n{rel_type.upper().replace('_', ' ')}:")
                for rel in rels:
                    lines.append(f"  - {rel.get('SchemaName', '')}")
        
        return "\n".join(lines)
    
    def _generate_xml(self, attributes: list) -> str:
        """Generate XML format (for ETL systems)"""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(f'<Entity name="{self.current_entity}" id="{self.current_record_id}">')
        lines.append('  <Attributes>')
        
        for attr in attributes:
            attr_name = attr.get("attribute_name", "")
            attr_type = attr.get("type", "")
            value = attr.get("value", "")
            formatted_value = attr.get("formatted_value", "")
            
            lines.append(f'    <Attribute name="{attr_name}" type="{attr_type}">')
            lines.append(f'      <Value>{self._escape_xml(value)}</Value>')
            if formatted_value and formatted_value != value:
                lines.append(f'      <DisplayValue>{self._escape_xml(formatted_value)}</DisplayValue>')
            lines.append(f'      <Required>{str(attr.get("required", False)).lower()}</Required>')
            lines.append(f'      <ValidForCreate>{str(attr.get("is_valid_create", False)).lower()}</ValidForCreate>')
            lines.append(f'      <ValidForUpdate>{str(attr.get("is_valid_update", False)).lower()}</ValidForUpdate>')
            lines.append('    </Attribute>')
        
        lines.append('  </Attributes>')
        
        if self.current_relationships:
            lines.append('  <Relationships>')
            for rel_type, rels in self.current_relationships.items():
                for rel in rels:
                    lines.append(f'    <Relationship type="{rel_type}" name="{rel.get("SchemaName", "")}"/>')
            lines.append('  </Relationships>')
        
        lines.append('</Entity>')
        return "\n".join(lines)
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        text = str(text)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return text
    
    def _on_export_json(self):
        """Export current view as JSON"""
        if not self.current_metadata or not self.current_record_data:
            QMessageBox.warning(self, "Error", "No data to export")
            return
        
        # Build attributes with values list
        attributes_with_values = []
        for attr in self.current_metadata.get("attributes", []):
            attr_name = attr.get("LogicalName", "")
            if attr_name:
                attr_value = self.current_record_data.get(attr_name)
                formatted = EntityDetailsFormatter.format_attribute_row(
                    attr_name, attr, attr_value
                )
                attributes_with_values.append(formatted)
        
        # Export as JSON
        export_json = EntityDetailsFormatter.export_as_json(
            self.current_metadata,
            {"id": self.current_record_id},
            attributes_with_values,
            self.current_relationships or {}
        )
        
        # Show in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Exported JSON - {self.current_entity}({self.current_record_id})")
        dialog.setGeometry(100, 100, 900, 700)
        
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setPlainText(export_json)
        text.setFont(QFont("Courier", 9))
        layout.addWidget(text)
        
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(export_json))
        save_btn = QPushButton("💾 Save to File")
        save_btn.clicked.connect(lambda: self._save_to_file(export_json))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Success", "Copied to clipboard!")
    
    def _save_to_file(self, text: str):
        """Save text to file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Export", "", "JSON Files (*.json);;Text Files (*.txt)"
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(text)
            QMessageBox.information(self, "Success", f"Saved to {filename}")
