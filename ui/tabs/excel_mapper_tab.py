"""
Excel/CSV Mapper Tab - Core Tier 1 feature
Maps Excel columns to Dataverse fields with datatype conversion
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QListWidget, QListWidgetItem,
    QComboBox, QTextEdit, QSpinBox, QMessageBox, QSplitter,
    QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import json

from utils.excel_processor import ExcelProcessor
from utils.json_builder import JSONBuilder


class MetadataFetchThread(QThread):
    """Background thread for fetching metadata"""
    
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, entity_name):
        super().__init__()
        self.client = client
        self.entity_name = entity_name
    
    def run(self):
        """Fetch entity attributes"""
        try:
            result = self.client.fetch_entity_attributes(self.entity_name)
            
            if result.get("success"):
                self.success.emit(result)
            else:
                self.error.emit(result.get("error", "Failed to fetch metadata"))
        
        except Exception as e:
            self.error.emit(str(e))


class ExcelMapperTab(QWidget):
    """Excel/CSV mapper tab"""
    
    load_to_crud_requested = pyqtSignal(dict)
    load_to_batch_requested = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        self.client = None
        self.excel_processor = None
        self.excel_headers = []
        self.excel_rows = []
        self.field_mappings = {}
        self.entity_attributes = []
        self.choice_mappings = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # File selection
        file_group = QGroupBox("1️⃣ Select Excel/CSV File")
        file_layout = QHBoxLayout()
        
        self.file_path_label = QLabel("No file selected")
        file_layout.addWidget(self.file_path_label, stretch=1)
        
        self.select_file_button = QPushButton("📂 Select File")
        self.select_file_button.clicked.connect(self._select_file)
        file_layout.addWidget(self.select_file_button)
        
        # Header row selector
        header_row_layout = QHBoxLayout()
        header_row_label = QLabel("Header Row:")
        self.header_row_spin = QSpinBox()
        self.header_row_spin.setMinimum(1)
        self.header_row_spin.setMaximum(100)
        self.header_row_spin.setValue(1)
        self.header_row_spin.setToolTip("Row number containing column headers")
        header_row_layout.addWidget(header_row_label)
        header_row_layout.addWidget(self.header_row_spin)
        header_row_layout.addStretch()
        
        file_group_layout = QVBoxLayout()
        file_group_layout.addLayout(file_layout)
        file_group_layout.addLayout(header_row_layout)
        file_group.setLayout(file_group_layout)
        layout.addWidget(file_group)
        
        # Entity selection
        entity_group = QGroupBox("2️⃣ Select Target Entity")
        entity_layout = QHBoxLayout()
        
        entity_label = QLabel("Entity:")
        self.entity_combo = QComboBox()
        self.entity_combo.setEditable(True)
        self.entity_combo.setPlaceholderText("Type or select entity name (e.g., account)")
        self.entity_combo.currentTextChanged.connect(self._on_entity_changed)
        entity_layout.addWidget(entity_label)
        entity_layout.addWidget(self.entity_combo, stretch=1)
        
        self.fetch_fields_button = QPushButton("🔍 Fetch Fields")
        self.fetch_fields_button.clicked.connect(self._fetch_entity_fields)
        self.fetch_fields_button.setEnabled(False)
        entity_layout.addWidget(self.fetch_fields_button)
        
        entity_group.setLayout(entity_layout)
        layout.addWidget(entity_group)
        
        # Mapping interface
        mapping_group = QGroupBox("3️⃣ Map Fields")
        mapping_layout = QHBoxLayout()
        
        # Left panel - Excel columns
        excel_panel = QWidget()
        excel_panel_layout = QVBoxLayout(excel_panel)
        excel_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        excel_label = QLabel("Excel Columns:")
        excel_panel_layout.addWidget(excel_label)
        
        self.excel_columns_list = QListWidget()
        excel_panel_layout.addWidget(self.excel_columns_list)
        
        # Preview table
        preview_label = QLabel("Preview (first 3 rows):")
        excel_panel_layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(150)
        excel_panel_layout.addWidget(self.preview_table)
        
        # Right panel - Dataverse fields
        dv_panel = QWidget()
        dv_panel_layout = QVBoxLayout(dv_panel)
        dv_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        dv_label = QLabel("Dataverse Fields:")
        dv_panel_layout.addWidget(dv_label)
        
        self.dv_fields_list = QListWidget()
        dv_panel_layout.addWidget(self.dv_fields_list)
        
        # Mapping assignment
        assign_label = QLabel("Assign mapping:")
        dv_panel_layout.addWidget(assign_label)
        
        assign_layout = QHBoxLayout()
        
        self.excel_col_combo = QComboBox()
        self.excel_col_combo.setPlaceholderText("Select Excel column")
        assign_layout.addWidget(self.excel_col_combo)
        
        arrow_label = QLabel("→")
        assign_layout.addWidget(arrow_label)
        
        self.dv_field_combo = QComboBox()
        self.dv_field_combo.setPlaceholderText("Select Dataverse field")
        assign_layout.addWidget(self.dv_field_combo)
        
        self.assign_button = QPushButton("✅ Assign")
        self.assign_button.clicked.connect(self._assign_mapping)
        assign_layout.addWidget(self.assign_button)
        
        dv_panel_layout.addLayout(assign_layout)
        
        # Current mappings display
        mappings_label = QLabel("Current Mappings:")
        dv_panel_layout.addWidget(mappings_label)
        
        self.mappings_list = QListWidget()
        dv_panel_layout.addWidget(self.mappings_list)
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(excel_panel)
        splitter.addWidget(dv_panel)
        splitter.setSizes([400, 400])
        
        mapping_layout.addWidget(splitter)
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group, stretch=1)
        
        # JSON preview
        preview_group = QGroupBox("4️⃣ JSON Preview")
        preview_layout = QVBoxLayout()
        
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setMaximumHeight(150)
        self.json_preview.setPlaceholderText("JSON preview will appear here...")
        preview_layout.addWidget(self.json_preview)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.generate_json_button = QPushButton("🔨 Generate JSON")
        self.generate_json_button.clicked.connect(self._generate_json)
        action_layout.addWidget(self.generate_json_button)
        
        self.load_crud_button = QPushButton("📝 Load to CRUD")
        self.load_crud_button.clicked.connect(self._load_to_crud)
        action_layout.addWidget(self.load_crud_button)
        
        self.load_batch_button = QPushButton("⚡ Load to Batch")
        self.load_batch_button.clicked.connect(self._load_to_batch)
        action_layout.addWidget(self.load_batch_button)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
    
    def set_client(self, client):
        """Set the metadata client"""
        self.client = client
        self.fetch_fields_button.setEnabled(True)
        
        # Populate entity list
        entities = client.get_entity_list()
        self.entity_combo.addItems(entities)
    
    def _select_file(self):
        """Select Excel/CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel or CSV File",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                self.excel_processor = ExcelProcessor(file_path)
                
                # Use specified header row (0-indexed)
                header_row = self.header_row_spin.value() - 1
                
                self.excel_headers, self.excel_rows = self.excel_processor.read_file(header_row)
                
                self.file_path_label.setText(file_path)
                
                # Populate Excel columns list
                self.excel_columns_list.clear()
                self.excel_col_combo.clear()
                
                for header in self.excel_headers:
                    self.excel_columns_list.addItem(header)
                    self.excel_col_combo.addItem(header)
                
                # Show preview
                self._show_preview()
                
                QMessageBox.information(
                    self,
                    "File Loaded",
                    f"Loaded {len(self.excel_rows)} rows with {len(self.excel_headers)} columns."
                )
            
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{str(e)}")
    
    def _show_preview(self):
        """Show preview of first few rows"""
        if not self.excel_rows:
            return
        
        preview_rows = self.excel_rows[:3]
        
        self.preview_table.setRowCount(len(preview_rows))
        self.preview_table.setColumnCount(len(self.excel_headers))
        self.preview_table.setHorizontalHeaderLabels(self.excel_headers)
        
        for row_idx, row in enumerate(preview_rows):
            for col_idx, header in enumerate(self.excel_headers):
                value = row.get(header, "")
                item = QTableWidgetItem(str(value))
                self.preview_table.setItem(row_idx, col_idx, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def _on_entity_changed(self, entity_name: str):
        """Handle entity selection change"""
        pass  # Can add auto-fetch here if desired
    
    def _fetch_entity_fields(self):
        """Fetch fields for selected entity"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        entity_name = self.entity_combo.currentText().strip()
        
        if not entity_name:
            QMessageBox.warning(self, "No Entity", "Please enter entity name.")
            return
        
        # Disable button
        self.fetch_fields_button.setEnabled(False)
        self.fetch_fields_button.setText("⏳ Fetching...")
        
        # Start metadata fetch
        self.metadata_thread = MetadataFetchThread(self.client, entity_name)
        self.metadata_thread.success.connect(self._on_metadata_fetched)
        self.metadata_thread.error.connect(self._on_metadata_error)
        self.metadata_thread.start()
    
    def _on_metadata_fetched(self, result: dict):
        """Handle successful metadata fetch"""
        self.fetch_fields_button.setEnabled(True)
        self.fetch_fields_button.setText("🔍 Fetch Fields")
        
        self.entity_attributes = result.get("attributes", [])
        
        # Populate Dataverse fields list
        self.dv_fields_list.clear()
        self.dv_field_combo.clear()
        
        for attr in self.entity_attributes:
            logical_name = attr.get("LogicalName", "")
            attr_type = attr.get("AttributeType", "")
            display_name = attr.get("DisplayName", {}).get("UserLocalizedLabel", {}).get("Label", logical_name)
            
            display_text = f"{logical_name} ({attr_type})"
            
            self.dv_fields_list.addItem(display_text)
            self.dv_field_combo.addItem(display_text, logical_name)
        
        QMessageBox.information(
            self,
            "Fields Loaded",
            f"Loaded {len(self.entity_attributes)} fields for entity '{self.entity_combo.currentText()}'."
        )
    
    def _on_metadata_error(self, error_msg: str):
        """Handle metadata fetch error"""
        self.fetch_fields_button.setEnabled(True)
        self.fetch_fields_button.setText("🔍 Fetch Fields")
        
        QMessageBox.critical(self, "Metadata Error", f"Failed to fetch fields:\n{error_msg}")
    
    def _assign_mapping(self):
        """Assign Excel column to Dataverse field"""
        excel_col = self.excel_col_combo.currentText()
        dv_field_text = self.dv_field_combo.currentText()
        
        if not excel_col or not dv_field_text:
            QMessageBox.warning(self, "Incomplete", "Please select both columns.")
            return
        
        # Extract field name and type
        dv_field = self.dv_field_combo.currentData()
        
        # Find attribute type
        attr_type = "String"
        for attr in self.entity_attributes:
            if attr.get("LogicalName") == dv_field:
                attr_type = attr.get("AttributeType", "String")
                break
        
        # Store mapping
        self.field_mappings[excel_col] = {
            "field": dv_field,
            "type": attr_type
        }
        
        # Update mappings list
        self._update_mappings_list()
        
        # Update JSON preview
        self._update_json_preview()
    
    def _update_mappings_list(self):
        """Update current mappings display"""
        self.mappings_list.clear()
        
        for excel_col, field_info in self.field_mappings.items():
            dv_field = field_info["field"]
            dv_type = field_info["type"]
            
            display_text = f"{excel_col} → {dv_field} ({dv_type})"
            self.mappings_list.addItem(display_text)
    
    def _update_json_preview(self):
        """Update JSON preview with first row"""
        if not self.excel_rows or not self.field_mappings:
            self.json_preview.setPlainText("No data or mappings available")
            return
        
        # Build JSON for first row
        try:
            json_builder = JSONBuilder(self.field_mappings, self.choice_mappings)
            result = json_builder.build_json_for_row(self.excel_rows[0])
            
            if result["success"]:
                self.json_preview.setPlainText(json.dumps(result["payload"], indent=2))
            else:
                error_text = "Errors:\n" + "\n".join(result["errors"])
                self.json_preview.setPlainText(error_text)
        
        except Exception as e:
            self.json_preview.setPlainText(f"Error generating preview: {str(e)}")
    
    def _generate_json(self):
        """Generate JSON for all rows"""
        if not self.excel_rows or not self.field_mappings:
            QMessageBox.warning(self, "Not Ready", "Please load file and create mappings first.")
            return
        
        try:
            json_builder = JSONBuilder(self.field_mappings, self.choice_mappings)
            result = json_builder.build_json_for_all_rows(self.excel_rows)
            
            summary = f"""
            Total Rows: {result['total_rows']}
            Valid Rows: {result['valid_rows']}
            Success: {result['success']}
            """
            
            if result["errors"]:
                summary += f"\n\nErrors:\n"
                for row, errors in result["errors"].items():
                    summary += f"{row}: {', '.join(errors)}\n"
            
            QMessageBox.information(self, "JSON Generated", summary)
            
            # Update preview with full result
            self.json_preview.setPlainText(json.dumps(result["payloads"][:5], indent=2) + "\n\n... (showing first 5 rows)")
        
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Failed to generate JSON:\n{str(e)}")
    
    def _load_to_crud(self):
        """Load first row to CRUD tab"""
        if not self.excel_rows or not self.field_mappings:
            QMessageBox.warning(self, "Not Ready", "Please load file and create mappings first.")
            return
        
        try:
            json_builder = JSONBuilder(self.field_mappings, self.choice_mappings)
            result = json_builder.build_json_for_row(self.excel_rows[0])
            
            if result["success"]:
                self.load_to_crud_requested.emit(result["payload"])
                QMessageBox.information(self, "Loaded", "First row loaded to CRUD tab.")
            else:
                QMessageBox.warning(self, "Errors", "Row has errors:\n" + "\n".join(result["errors"]))
        
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load:\n{str(e)}")
    
    def _load_to_batch(self):
        """Load all rows to Batch tab"""
        if not self.excel_rows or not self.field_mappings:
            QMessageBox.warning(self, "Not Ready", "Please load file and create mappings first.")
            return
        
        try:
            json_builder = JSONBuilder(self.field_mappings, self.choice_mappings)
            result = json_builder.build_json_for_all_rows(self.excel_rows)
            
            # Get entity set name (plural form)
            # Note: This uses simple pluralization. For production, fetch EntitySetName from metadata
            entity_name = self.entity_combo.currentText()
            entity_set_name = f"{entity_name}s"  # Simple pluralization
            
            # TODO: Fetch correct EntitySetName from metadata to handle irregular plurals
            # entity_def = self.client.fetch_entity_definitions()
            # entity_set_name = next((e['EntitySetName'] for e in entity_def['entities'] if e['LogicalName'] == entity_name), f"{entity_name}s")
            
            operations = []
            
            for payload in result["payloads"]:
                if payload:  # Skip empty payloads
                    operations.append({
                        "method": "POST",
                        "url": f"/api/data/v9.2/{entity_set_name}",
                        "data": payload
                    })
            
            self.load_to_batch_requested.emit(operations)
            
            QMessageBox.information(
                self,
                "Loaded",
                f"Loaded {len(operations)} operations to Batch tab."
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load:\n{str(e)}")
