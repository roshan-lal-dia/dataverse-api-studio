"""
Advanced Query Builder Tab with Visual Filter Builder
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QMessageBox, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem, QTextEdit, QTabWidget, QScrollArea,
    QCompleter, QFrame
)
from PyQt6.QtCore import pyqtSignal, QThread, Qt, QStringListModel
from PyQt6.QtGui import QFont
from datetime import datetime
import json

from utils.query_builder import (
    QueryBuilder, FilterCondition, FilterGroup, 
    FilterOperator, LogicalOperator
)


class QueryBuilderTab(QWidget):
    """Advanced query builder tab with visual filter builder"""
    
    operation_executed = pyqtSignal(dict)
    
    def __init__(self, template_manager):
        super().__init__()
        
        self.template_manager = template_manager
        self.client = None
        self.query_thread = None
        self.entity_list = []
        self.current_fields = []
        self.filter_widgets = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tabs for simple and advanced modes
        self.mode_tabs = QTabWidget()
        
        # Simple mode (existing interface)
        simple_widget = self._create_simple_mode()
        self.mode_tabs.addTab(simple_widget, "📝 Simple Mode")
        
        # Advanced visual builder
        advanced_widget = self._create_advanced_mode()
        self.mode_tabs.addTab(advanced_widget, "🎨 Visual Builder")
        
        layout.addWidget(self.mode_tabs)
        
        # Preview area
        preview_group = QGroupBox("Query Preview")
        preview_layout = QVBoxLayout()
        
        # Sub-tabs for OData and FetchXML
        self.preview_tabs = QTabWidget()
        
        self.odata_preview = QTextEdit()
        self.odata_preview.setReadOnly(True)
        self.odata_preview.setMaximumHeight(150)
        self.odata_preview.setPlaceholderText("OData query will appear here...")
        self.preview_tabs.addTab(self.odata_preview, "OData")
        
        self.fetchxml_preview = QTextEdit()
        self.fetchxml_preview.setReadOnly(True)
        self.fetchxml_preview.setMaximumHeight(150)
        self.fetchxml_preview.setPlaceholderText("FetchXML query will appear here...")
        self.preview_tabs.addTab(self.fetchxml_preview, "FetchXML")
        
        preview_layout.addWidget(self.preview_tabs)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("👁️ Preview Query")
        self.preview_button.clicked.connect(self._preview_query)
        button_layout.addWidget(self.preview_button)
        
        self.execute_button = QPushButton("🔍 Execute Query")
        self.execute_button.setMinimumHeight(40)
        self.execute_button.clicked.connect(self._execute_query)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button, stretch=1)
        
        self.save_template_button = QPushButton("💾 Save Template")
        self.save_template_button.clicked.connect(self._save_query_template)
        button_layout.addWidget(self.save_template_button)
        
        layout.addLayout(button_layout)
    
    def _create_simple_mode(self) -> QWidget:
        """Create simple mode interface"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        config_group = QGroupBox("Query Configuration")
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(15, 25, 15, 15)
        
        # Table name with autocomplete
        table_row = QHBoxLayout()
        table_label = QLabel("Entity Name:")
        table_label.setFixedWidth(180)
        self.simple_table_input = QLineEdit()
        self.simple_table_input.setPlaceholderText("e.g., account, contact")
        self.table_completer = QCompleter()
        self.simple_table_input.setCompleter(self.table_completer)
        table_row.addWidget(table_label)
        table_row.addWidget(self.simple_table_input)
        config_layout.addLayout(table_row)
        
        # Filter
        filter_row = QHBoxLayout()
        filter_label = QLabel("Filter (OData $filter):")
        filter_label.setFixedWidth(180)
        self.simple_filter_input = QLineEdit()
        self.simple_filter_input.setPlaceholderText("e.g., revenue gt 1000000 and statecode eq 0")
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.simple_filter_input)
        config_layout.addLayout(filter_row)
        
        # Select
        select_row = QHBoxLayout()
        select_label = QLabel("Select Fields:")
        select_label.setFixedWidth(180)
        self.simple_select_input = QLineEdit()
        self.simple_select_input.setPlaceholderText("e.g., name,revenue,websiteurl (comma-separated)")
        select_row.addWidget(select_label)
        select_row.addWidget(self.simple_select_input)
        config_layout.addLayout(select_row)
        
        # Order by
        order_row = QHBoxLayout()
        order_label = QLabel("Order By:")
        order_label.setFixedWidth(180)
        self.simple_order_input = QLineEdit()
        self.simple_order_input.setPlaceholderText("e.g., revenue desc")
        order_row.addWidget(order_label)
        order_row.addWidget(self.simple_order_input)
        config_layout.addLayout(order_row)
        
        # Top
        top_row = QHBoxLayout()
        top_label = QLabel("Top (limit):")
        top_label.setFixedWidth(180)
        self.simple_top_spin = QSpinBox()
        self.simple_top_spin.setMinimum(1)
        self.simple_top_spin.setMaximum(5000)
        self.simple_top_spin.setValue(100)
        self.simple_top_spin.setFixedWidth(120)
        top_row.addWidget(top_label)
        top_row.addWidget(self.simple_top_spin)
        top_row.addStretch()
        config_layout.addLayout(top_row)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Example queries
        examples_group = QGroupBox("📚 Example Queries")
        examples_layout = QVBoxLayout()
        
        examples_text = QLabel(
            "<b>Examples:</b><br>"
            "• Active accounts with revenue > $1M:<br>"
            "  <code>statecode eq 0 and revenue gt 1000000</code><br><br>"
            "• Contacts created this year:<br>"
            "  <code>createdon ge 2024-01-01</code><br><br>"
            "• Accounts with specific industry:<br>"
            "  <code>industrycode eq 1</code><br><br>"
            "• Complex filter:<br>"
            "  <code>(revenue gt 1000000 or numberofemployees gt 100) and statecode eq 0</code>"
        )
        examples_text.setWordWrap(True)
        examples_text.setTextFormat(Qt.TextFormat.RichText)
        examples_layout.addWidget(examples_text)
        
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_advanced_mode(self) -> QWidget:
        """Create advanced visual filter builder with full scroll support"""
        # Top container for the tab content
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- The Main Scroll Area ---
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # The content widget that holds all controls
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20) # More breathing room
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Section 1: Entity Selection ---
        entity_group = QGroupBox("1. Select Entity")
        entity_layout = QHBoxLayout()
        entity_layout.setContentsMargins(15, 25, 15, 15)
        entity_layout.setSpacing(10)
        
        entity_label = QLabel("Attributes from:")
        entity_label.setFixedWidth(100)
        
        self.advanced_entity_combo = QComboBox()
        self.advanced_entity_combo.setEditable(True)
        self.advanced_entity_combo.setPlaceholderText("Search entity (e.g. account)...")
        self.advanced_entity_combo.currentTextChanged.connect(self._on_entity_changed)
        
        entity_layout.addWidget(entity_label)
        entity_layout.addWidget(self.advanced_entity_combo, stretch=1)
        entity_group.setLayout(entity_layout)
        content_layout.addWidget(entity_group) # Add to scrollable content
        
        # --- Section 2: Filters ---
        filters_group = QGroupBox("2. Build Filters (Where)")
        filters_group_layout = QVBoxLayout()
        filters_group_layout.setContentsMargins(15, 25, 15, 15)
        filters_group_layout.setSpacing(10)

        # Filters container (No internal scroll area needed since page scrolls)
        self.filters_container = QWidget()
        self.filters_container.setStyleSheet("background-color: transparent;")
        
        # Layout for the container that holds rows
        self.filters_layout = QVBoxLayout(self.filters_container)
        self.filters_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filters_layout.setSpacing(8)
        
        # Instruction / Placeholder
        self.no_filters_label = QLabel("No filters added. All records will be retrieved.")
        self.no_filters_label.setStyleSheet("color: #666666; font-style: italic;")
        self.no_filters_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filters_layout.addWidget(self.no_filters_label)
        
        filters_group_layout.addWidget(self.filters_container)
        
        # Add Button
        add_filter_btn = QPushButton("➕ Add Condition")
        add_filter_btn.setFixedWidth(150)
        add_filter_btn.clicked.connect(self._add_filter_condition)
        filters_group_layout.addWidget(add_filter_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        filters_group.setLayout(filters_group_layout)
        content_layout.addWidget(filters_group) # Add to scrollable content
        
        # --- Section 3: Columns & Sorting ---
        # Note: We put this in a VBox now so it flows nicely on small screens
        # but inside a horizontal group if width permits. For consistent scroll
        # we will stack them vertically or keep side-by-side but with size constraints.
        # Let's keep side-by-side but ensure min height.
        
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(15)
        
        # Left: Columns
        fields_group = QGroupBox("3. Select Columns")
        fields_layout = QVBoxLayout()
        fields_layout.setContentsMargins(15, 25, 15, 15)
        fields_layout.setSpacing(5)
        
        fields_help = QLabel("Ctrl+Click to select multiple")
        fields_help.setStyleSheet("color: #666; font-size: 9pt;")
        fields_layout.addWidget(fields_help)
        
        self.fields_list = QListWidget()
        self.fields_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.fields_list.setAlternatingRowColors(True)
        self.fields_list.setMinimumHeight(200) # Give it good height
        fields_layout.addWidget(self.fields_list)
        
        fields_group.setLayout(fields_layout)
        bottom_row.addWidget(fields_group, stretch=3)
        
        # Right: Sorting & Limits
        options_group = QGroupBox("4. Sort & Limit")
        options_group.setMinimumWidth(300)
        options_layout = QVBoxLayout()
        options_layout.setContentsMargins(15, 25, 15, 15)
        options_layout.setSpacing(15)
        options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Order By Block
        order_container = QWidget()
        order_layout = QVBoxLayout(order_container)
        order_layout.setContentsMargins(0, 0, 0, 0)
        order_layout.setSpacing(5)
        
        order_lbl = QLabel("Order By:")
        order_lbl.setStyleSheet("font-weight: bold;")
        self.advanced_order_combo = QComboBox()
        self.advanced_order_combo.setPlaceholderText("Select field...")
        self.advanced_order_combo.setMinimumHeight(30)
        
        self.advanced_order_dir = QComboBox()
        self.advanced_order_dir.addItems(["Ascending (A-Z)", "Descending (Z-A)"])
        self.advanced_order_dir.setMinimumHeight(30)
        
        order_layout.addWidget(order_lbl)
        order_layout.addWidget(self.advanced_order_combo)
        order_layout.addWidget(self.advanced_order_dir)
        options_layout.addWidget(order_container)
        
        # Limit Block
        limit_container = QWidget()
        limit_layout = QVBoxLayout(limit_container)
        limit_layout.setContentsMargins(0, 0, 0, 0)
        limit_layout.setSpacing(5)
        
        limit_lbl = QLabel("Max Records:")
        limit_lbl.setStyleSheet("font-weight: bold;")
        self.advanced_top_spin = QSpinBox()
        self.advanced_top_spin.setRange(1, 10000)
        self.advanced_top_spin.setValue(50)
        self.advanced_top_spin.setSuffix(" rows")
        self.advanced_top_spin.setMinimumHeight(30)
        
        limit_layout.addWidget(limit_lbl)
        limit_layout.addWidget(self.advanced_top_spin)
        options_layout.addWidget(limit_container)
        
        options_layout.addStretch()
        options_group.setLayout(options_layout)
        bottom_row.addWidget(options_group, stretch=1)
        
        content_layout.addLayout(bottom_row)
        content_layout.addStretch() # Push everything up
        
        # Set the content to the scroll area
        main_scroll.setWidget(content_widget)
        
        # Add scroll area to the main container
        tab_layout.addWidget(main_scroll)
        
        return tab_container
    
    def _add_filter_condition(self):
        """Add a new filter condition widget"""
        # Hide the placeholder label if it's visible
        if hasattr(self, 'no_filters_label') and not self.no_filters_label.isHidden():
            self.no_filters_label.hide()
        
        condition_widget = QWidget()
        condition_widget.setStyleSheet("background-color: #f9f9f9; border-radius: 4px; border: 1px solid #e0e0e0;")
        condition_widget.setFixedHeight(50)
        
        # Use simple HBox
        layout = QHBoxLayout(condition_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Field
        field_cb = QComboBox()
        field_cb.setEditable(True)
        field_cb.addItems(self.current_fields)
        field_cb.setPlaceholderText("Field...")
        field_cb.setSizePolicy(
            field_cb.sizePolicy().horizontalPolicy(), 
            field_cb.sizePolicy().verticalPolicy()
        )
        # make it expand
        layout.addWidget(field_cb, stretch=4)
        
        # Operator
        op_cb = QComboBox()
        op_cb.addItems([
            "eq", "ne", "gt", "ge", "lt", "le", 
            "contains", "startswith", "endswith"
        ])
        layout.addWidget(op_cb, stretch=2)
        
        # Value
        val_le = QLineEdit()
        val_le.setPlaceholderText("Value...")
        layout.addWidget(val_le, stretch=3)
        
        # Remove
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(30, 30)
        del_btn.setStyleSheet("""
            QPushButton { 
                background-color: #ffcdd2; 
                color: #c62828; 
                border: none; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ef9a9a; }
        """)
        del_btn.clicked.connect(lambda: self._remove_filter_condition(condition_widget))
        layout.addWidget(del_btn)
        
        self.filters_layout.addWidget(condition_widget)
        
        self.filter_widgets.append({
            "widget": condition_widget,
            "field": field_cb,
            "operator": op_cb,
            "value": val_le
        })

    def _remove_filter_condition(self, widget):
        if widget is not None:
            self.filters_layout.removeWidget(widget)
            widget.deleteLater()
            
            # Remove from list
            self.filter_widgets = [x for x in self.filter_widgets if x['widget'] != widget]
            
            # Show placeholder if empty
            if not self.filter_widgets and hasattr(self, 'no_filters_label'):
                self.no_filters_label.show()
    
    def _on_entity_changed(self, entity_name: str):
        """Handle entity selection change"""
        if not entity_name or not self.client:
            return
        
        # Fetch fields for this entity
        result = self.client.fetch_entity_attributes(entity_name)
        
        if result.get("success"):
            attributes = result.get("attributes", [])
            self.current_fields = [attr.get("LogicalName", "") for attr in attributes]
            
            # Update fields list
            self.fields_list.clear()
            for field in sorted(self.current_fields):
                self.fields_list.addItem(field)
            
            # Update order combo
            self.advanced_order_combo.clear()
            self.advanced_order_combo.addItems(sorted(self.current_fields))
    
    def _build_query(self) -> QueryBuilder:
        """Build query from current UI state"""
        # Determine which mode is active
        if self.mode_tabs.currentIndex() == 0:
            # Simple mode
            entity = self.simple_table_input.text().strip()
            
            # Get EntitySetName from metadata
            entity_set_name = None
            if self.client:
                entity_set_name = self.client.get_entity_set_name(entity)
            
            builder = QueryBuilder(entity, entity_set_name)
            
            # Add select
            select_text = self.simple_select_input.text().strip()
            if select_text:
                fields = [f.strip() for f in select_text.split(',')]
                builder.select(*fields)
            
            # Add filter (raw OData)
            filter_text = self.simple_filter_input.text().strip()
            # For simple mode, we'll pass filter directly (not using QueryBuilder filter)
            
            # Add order
            order_text = self.simple_order_input.text().strip()
            if order_text:
                parts = order_text.split()
                field = parts[0]
                direction = parts[1] if len(parts) > 1 else "asc"
                builder.order(field, direction)
            
            # Add limit
            builder.limit(self.simple_top_spin.value())
            
            return builder
        else:
            # Advanced mode
            entity = self.advanced_entity_combo.currentText().strip()
            
            # Get EntitySetName from metadata
            entity_set_name = None
            if self.client:
                entity_set_name = self.client.get_entity_set_name(entity)
            
            builder = QueryBuilder(entity, entity_set_name)
            
            # Add selected fields
            selected_items = self.fields_list.selectedItems()
            if selected_items:
                fields = [item.text() for item in selected_items]
                builder.select(*fields)
            
            # Build filters from conditions
            if self.filter_widgets:
                conditions = []
                for fw in self.filter_widgets:
                    field = fw["field"].currentText().strip()
                    operator_text = fw["operator"].currentText()
                    value = fw["value"].text().strip()
                    
                    if field and value:
                        # Map operator text to FilterOperator
                        operator = self._parse_operator(operator_text)
                        conditions.append(FilterCondition(field, operator, value))
                
                if conditions:
                    # For now, use AND to combine all conditions
                    filter_group = FilterGroup(LogicalOperator.AND, conditions)
                    builder.filter(filter_group)
            
            # Add order
            order_field = self.advanced_order_combo.currentText().strip()
            if order_field:
                order_dir_text = self.advanced_order_dir.currentText()
                # Extract "asc" or "desc" from "Ascending (asc)" or "Descending (desc)"
                order_dir = "desc" if "desc" in order_dir_text.lower() else "asc"
                builder.order(order_field, order_dir)
            
            # Add limit
            builder.limit(self.advanced_top_spin.value())
            
            return builder
    
    def _parse_operator(self, operator_text: str) -> FilterOperator:
        """Parse operator from combo box text"""
        if "eq" in operator_text:
            return FilterOperator.EQUAL
        elif "ne" in operator_text:
            return FilterOperator.NOT_EQUAL
        elif "ge" in operator_text:
            return FilterOperator.GREATER_EQUAL
        elif "gt" in operator_text:
            return FilterOperator.GREATER_THAN
        elif "le" in operator_text:
            return FilterOperator.LESS_EQUAL
        elif "lt" in operator_text:
            return FilterOperator.LESS_THAN
        elif "contains" in operator_text:
            return FilterOperator.CONTAINS
        elif "starts" in operator_text:
            return FilterOperator.STARTS_WITH
        elif "ends" in operator_text:
            return FilterOperator.ENDS_WITH
        else:
            return FilterOperator.EQUAL
    
    def _preview_query(self):
        """Preview the generated query"""
        try:
            builder = self._build_query()
            
            # Generate OData
            odata = builder.to_odata()
            if not odata:
                odata = "(No filters or options set)"
            self.odata_preview.setPlainText(odata)
            
            # Generate FetchXML
            fetchxml = builder.to_fetchxml()
            self.fetchxml_preview.setPlainText(fetchxml)
            
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Error generating preview:\n{str(e)}")
    
    def _execute_query(self):
        """Execute the query"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
            return
        
        try:
            # Get entity and parameters
            if self.mode_tabs.currentIndex() == 0:
                # Simple mode
                table_name = self.simple_table_input.text().strip()
                filter_query = self.simple_filter_input.text().strip()
                select = self.simple_select_input.text().strip()
                order_by = self.simple_order_input.text().strip()
                top = self.simple_top_spin.value()
            else:
                # Advanced mode - build from QueryBuilder
                builder = self._build_query()
                table_name = builder.entity_name
                
                # Extract OData components
                odata = builder.to_odata()
                # Parse back components (simplified - in production would use builder directly)
                filter_query = ""
                select = ""
                order_by = ""
                top = builder.top or 100
                
                if builder.filter_group:
                    filter_query = builder.filter_group.to_odata()
                
                if builder.select_fields:
                    select = ",".join(builder.select_fields)
                
                if builder.order_by:
                    order_parts = [f"{field} {direction}" for field, direction in builder.order_by]
                    order_by = ",".join(order_parts)
            
            if not table_name:
                QMessageBox.warning(self, "Missing Input", "Please enter entity name.")
                return
            
            # Disable button
            self.execute_button.setEnabled(False)
            self.execute_button.setText("⏳ Executing Query...")
            
            # Start query thread
            select_list = [s.strip() for s in select.split(',')] if select else None
            
            from ui.tabs.query_tab import QueryThread
            self.query_thread = QueryThread(
                self.client,
                table_name,
                filter_query if filter_query else None,
                select if select else "",
                order_by if order_by else None,
                top
            )
            
            self.query_thread.success.connect(self._on_query_success)
            self.query_thread.error.connect(self._on_query_error)
            self.query_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error executing query:\n{str(e)}")
            self.execute_button.setEnabled(True)
            self.execute_button.setText("🔍 Execute Query")
    
    def _on_query_success(self, result: dict):
        """Handle successful query"""
        self.execute_button.setEnabled(True)
        self.execute_button.setText("🔍 Execute Query")
        
        # Get table name from active mode
        if self.mode_tabs.currentIndex() == 0:
            table = self.simple_table_input.text()
        else:
            table = self.advanced_entity_combo.currentText()
        
        operation_data = {
            "type": "Query",
            "table": table,
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
        
        # Get table name from active mode
        if self.mode_tabs.currentIndex() == 0:
            table = self.simple_table_input.text()
        else:
            table = self.advanced_entity_combo.currentText()
        
        operation_data = {
            "type": "Query",
            "table": table,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": error_msg
        }
        
        self.operation_executed.emit(operation_data)
    
    def _save_query_template(self):
        """Save current query as template"""
        # TODO: Implement template saving
        QMessageBox.information(self, "Coming Soon", "Query template saving will be implemented soon!")
    
    def set_client(self, client):
        """Set the Dataverse client"""
        self.client = client
        self.execute_button.setEnabled(True)
        
        # Load entity list
        self.entity_list = client.get_entity_list()
        
        # Update simple mode completer
        model = QStringListModel(self.entity_list)
        self.table_completer.setModel(model)
        
        # Update advanced mode combo
        self.advanced_entity_combo.clear()
        self.advanced_entity_combo.addItems(sorted(self.entity_list))
