"""
Main PyQt6 Application Window
Orchestrates all UI components and tabs
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QMenuBar, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from pathlib import Path

from client.metadata_client import MetadataClient
from utils.config import Config
from utils.template_manager import TemplateManager
from utils.plugin_manager import PluginManager

from ui.panels.auth_panel import AuthPanel
from ui.panels.history_panel import HistoryPanel
from ui.tabs.crud_tab import CRUDTab
from ui.tabs.batch_tab import BatchTab
from ui.tabs.query_tab import QueryTab
from ui.tabs.query_builder_tab import QueryBuilderTab
from ui.tabs.results_tab import ResultsTab
from ui.tabs.excel_mapper_tab import ExcelMapperTab


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config = Config()
        self.client = None
        self.template_manager = TemplateManager(self.config.get_templates_directory())
        
        # Initialize plugin manager
        plugins_dir = Path(__file__).parent.parent / "plugins"
        self.plugin_manager = PluginManager(plugins_dir)
        
        # Operation history
        self.operation_history = []
        
        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_ui()
        self._create_status_bar()
        
        # Load plugins
        self._load_plugins()
        
        # Apply theme
        self._apply_theme()
    
    def _setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("🚀 Dataverse API Studio - Professional Edition")
        self.setMinimumSize(QSize(1400, 800))
        self.resize(QSize(1600, 900))
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        export_action = QAction("&Export Results", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        clear_cache_action = QAction("Clear &Cache", self)
        clear_cache_action.triggered.connect(self._clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        clear_history_action = QAction("Clear &History", self)
        clear_history_action.triggered.connect(self._clear_history)
        tools_menu.addAction(clear_history_action)
        
        tools_menu.addSeparator()
        
        # Plugins submenu
        self.plugins_menu = tools_menu.addMenu("🔌 &Plugins")
        reload_plugins_action = QAction("Reload Plugins", self)
        reload_plugins_action.triggered.connect(self._reload_plugins)
        self.plugins_menu.addAction(reload_plugins_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_ui(self):
        """Create main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Authentication + History
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Auth panel
        self.auth_panel = AuthPanel(self.config)
        self.auth_panel.authenticated.connect(self._on_authenticated)
        self.auth_panel.cache_refresh_requested.connect(self._on_cache_refresh)
        left_layout.addWidget(self.auth_panel)
        
        # History panel
        self.history_panel = HistoryPanel()
        left_layout.addWidget(self.history_panel, stretch=1)
        
        # Right panel - Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Create tabs
        self.crud_tab = CRUDTab(self.template_manager)
        self.crud_tab.operation_executed.connect(self._on_operation_executed)
        
        self.excel_mapper_tab = ExcelMapperTab()
        self.excel_mapper_tab.load_to_crud_requested.connect(self._load_to_crud)
        self.excel_mapper_tab.load_to_batch_requested.connect(self._load_to_batch)
        
        self.batch_tab = BatchTab(self.template_manager)
        self.batch_tab.operation_executed.connect(self._on_operation_executed)
        
        self.query_tab = QueryTab()
        self.query_tab.operation_executed.connect(self._on_operation_executed)
        
        self.query_builder_tab = QueryBuilderTab(self.template_manager)
        self.query_builder_tab.operation_executed.connect(self._on_operation_executed)
        
        self.results_tab = ResultsTab()
        
        # Add tabs
        self.tab_widget.addTab(self.crud_tab, "📝 CRUD Operations")
        self.tab_widget.addTab(self.excel_mapper_tab, "📊 Excel Mapper")
        self.tab_widget.addTab(self.batch_tab, "⚡ Batch Operations")
        self.tab_widget.addTab(self.query_tab, "🔍 Query (Simple)")
        self.tab_widget.addTab(self.query_builder_tab, "🎨 Query Builder")
        self.tab_widget.addTab(self.results_tab, "📋 Results")
        
        # Store plugin tabs for later
        self.plugin_tabs = []
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tab_widget)
        
        # Set initial sizes (20% left, 80% right)
        splitter.setSizes([300, 1100])
        
        main_layout.addWidget(splitter)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Not connected - Please authenticate")
    
    def _apply_theme(self):
        """Apply Fusion theme with modern styling"""
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # Modern color scheme
        stylesheet = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background: white;
        }
        QTabBar::tab {
            background: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 2px solid #2196F3;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #888888;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 6px;
            background: white;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #2196F3;
        }
        QGroupBox {
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            margin-top: 12px;
            font-weight: bold;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def _on_authenticated(self, client: MetadataClient):
        """Handle successful authentication"""
        self.client = client
        
        # Update tabs with client
        self.crud_tab.set_client(client)
        self.batch_tab.set_client(client)
        self.query_tab.set_client(client)
        self.query_builder_tab.set_client(client)
        self.excel_mapper_tab.set_client(client)
        self.results_tab.set_client(client)
        
        # Update plugin tabs
        for tab_widget, _ in self.plugin_tabs:
            if hasattr(tab_widget, 'set_client'):
                tab_widget.set_client(client)
        
        # Notify plugins
        self.plugin_manager.notify_client_connected(client)
        
        # Update status bar
        env = self.auth_panel.get_current_environment()
        self.status_bar.showMessage(f"✅ Connected to {env}")
    
    def _on_cache_refresh(self):
        """Handle cache refresh request"""
        if self.client:
            self.client.invalidate_cache()
            self.status_bar.showMessage("Cache cleared", 3000)
    
    def _on_operation_executed(self, operation_data: dict):
        """Handle operation execution"""
        # Add to history
        self.operation_history.insert(0, operation_data)
        if len(self.operation_history) > 20:
            self.operation_history = self.operation_history[:20]
        
        # Update history panel
        self.history_panel.add_operation(operation_data)
        
        # Display results
        self.results_tab.display_result(operation_data)
        
        # Switch to results tab
        self.tab_widget.setCurrentWidget(self.results_tab)
    
    def _load_to_crud(self, json_data: dict):
        """Load Excel mapper output to CRUD tab"""
        self.crud_tab.load_data(json_data)
        self.tab_widget.setCurrentWidget(self.crud_tab)
    
    def _load_to_batch(self, operations: list):
        """Load Excel mapper output to Batch tab"""
        self.batch_tab.load_operations(operations)
        self.tab_widget.setCurrentWidget(self.batch_tab)
    
    def _export_results(self):
        """Export current results"""
        self.results_tab.export_results()
    
    def _clear_cache(self):
        """Clear metadata cache"""
        if self.client:
            self.client.invalidate_cache()
            QMessageBox.information(self, "Cache Cleared", "Metadata cache has been cleared.")
        else:
            QMessageBox.warning(self, "Not Connected", "Please connect first.")
    
    def _clear_history(self):
        """Clear operation history"""
        self.operation_history.clear()
        self.history_panel.clear()
        QMessageBox.information(self, "History Cleared", "Operation history has been cleared.")
    
    def _show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Dataverse API Studio</h2>
        <p><b>Version:</b> 2.0.0 (Professional Edition)</p>
        <p><b>Framework:</b> PyQt6</p>
        <p>A modern desktop application for Dataverse Web API operations.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>CRUD Operations</li>
            <li>Batch Processing (up to 1000 ops)</li>
            <li>Excel/CSV Mapper with visual field mapping</li>
            <li>Advanced Query Builder with OData/FetchXML</li>
            <li>Metadata Discovery with 24hr caching</li>
            <li>Template Library</li>
            <li>Plugin System</li>
            <li>Enhanced Exports (JSON, CSV, Excel, Power BI)</li>
        </ul>
        <br>
        <p><b>Loaded Plugins:</b> {plugin_count}</p>
        """
        
        plugin_count = len(self.plugin_manager.get_loaded_plugins())
        about_text = about_text.format(plugin_count=plugin_count)
        
        QMessageBox.about(self, "About Dataverse API Studio", about_text)
    
    def _load_plugins(self):
        """Discover and load plugins"""
        try:
            # Discover plugins
            plugins = self.plugin_manager.discover_plugins()
            
            # Initialize plugins
            self.plugin_manager.initialize_plugins(self)
            
            # Register plugin tabs
            plugin_tabs = self.plugin_manager.register_plugin_tabs(self)
            for tab_widget, tab_name in plugin_tabs:
                self.tab_widget.addTab(tab_widget, tab_name)
                self.plugin_tabs.append((tab_widget, tab_name))
            
            # Register plugin actions
            plugin_actions = self.plugin_manager.register_plugin_actions(self)
            for action in plugin_actions:
                self.plugins_menu.addAction(action)
            
            # Log loaded plugins
            loaded = self.plugin_manager.get_loaded_plugins()
            failed = self.plugin_manager.get_failed_plugins()
            
            if loaded:
                print(f"✅ Loaded {len(loaded)} plugin(s):")
                for plugin in loaded:
                    print(f"  - {plugin.name} v{plugin.version}")
            
            if failed:
                print(f"⚠️ Failed to load {len(failed)} plugin(s):")
                for plugin in failed:
                    print(f"  - {plugin.name}: {plugin.error}")
        
        except Exception as e:
            print(f"Error loading plugins: {str(e)}")
    
    def _reload_plugins(self):
        """Reload all plugins"""
        try:
            # Remove existing plugin tabs
            for tab_widget, _ in self.plugin_tabs:
                index = self.tab_widget.indexOf(tab_widget)
                if index >= 0:
                    self.tab_widget.removeTab(index)
            
            self.plugin_tabs.clear()
            
            # Reload plugins
            self.plugin_manager.reload_plugins()
            self._load_plugins()
            
            QMessageBox.information(
                self,
                "Plugins Reloaded",
                f"Successfully reloaded plugins.\n\n"
                f"Loaded: {len(self.plugin_manager.get_loaded_plugins())}\n"
                f"Failed: {len(self.plugin_manager.get_failed_plugins())}"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reload plugins:\n{str(e)}")
        <p>Features:</p>
        <ul>
        <li>CRUD Operations with all datatypes</li>
        <li>Batch Processing (up to 1000 operations)</li>
        <li>Excel/CSV Mapper with field mapping</li>
        <li>Metadata Discovery with caching</li>
        <li>Template Library</li>
        <li>Query Builder with OData support</li>
        </ul>
        <p><b>Developer:</b> Dataverse API Studio Team</p>
        """
        QMessageBox.about(self, "About Dataverse API Studio", about_text)
