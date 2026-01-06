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
        
        # Theme mode
        self.dark_mode = False
        
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
        
        # Theme toggle
        self.theme_action = QAction("🌙 Dark Mode", self)
        self.theme_action.triggered.connect(self._toggle_theme)
        tools_menu.addAction(self.theme_action)
        
        tools_menu.addSeparator()
        
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
        """Apply theme based on mode (light/dark)"""
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        if self.dark_mode:
            stylesheet = self._get_dark_stylesheet()
        else:
            stylesheet = self._get_light_stylesheet()
        
        self.setStyleSheet(stylesheet)
    
    def _toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.theme_action.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")
        self._apply_theme()
    
    def _get_light_stylesheet(self):
        """Get light mode stylesheet"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QWidget {
            color: #212121;
            font-size: 10pt;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background: white;
            padding: 10px;
        }
        QTabBar::tab {
            background: #e0e0e0;
            color: #212121;
            padding: 10px 20px;
            margin-right: 2px;
            min-width: 100px;
        }
        QTabBar::tab:selected {
            background: white;
            color: #212121;
            border-bottom: 3px solid #2196F3;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 32px;
            font-size: 10pt;
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
            padding: 8px 12px;
            background: white;
            color: #212121;
            min-height: 28px;
            font-size: 10pt;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QSpinBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            background: white;
            color: #212121;
            min-height: 28px;
            font-size: 10pt;
        }
        QSpinBox:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QComboBox {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            background: white;
            color: #212121;
            min-height: 28px;
            font-size: 10pt;
        }
        QComboBox:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QComboBox::drop-down {
            border: none;
            width: 25px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #212121;
            margin-right: 5px;
        }
        QComboBox QAbstractItemView {
            background: white;
            color: #212121;
            selection-background-color: #2196F3;
            selection-color: white;
            border: 1px solid #cccccc;
            padding: 4px;
        }
        QComboBox QAbstractItemView::item {
            padding: 6px 12px;
            min-height: 25px;
            color: #212121;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background: #e0e0e0;
            border: none;
            width: 20px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #d0d0d0;
        }
        QGroupBox {
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
            padding-top: 20px;
            padding-left: 10px;
            padding-right: 10px;
            padding-bottom: 10px;
            color: #212121;
            background: white;
            font-size: 10pt;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: #212121;
            left: 8px;
            top: 2px;
        }
        QLabel {
            color: #212121;
            font-size: 10pt;
            background: transparent;
        }
        QScrollArea {
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
        QScrollArea > QWidget > QWidget {
            background: #f5f5f5;
        }
        QScrollArea QWidget {
            background: transparent;
        }
        QCheckBox {
            color: #212121;
            spacing: 8px;
            padding: 4px;
            font-size: 10pt;
        }
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #cccccc;
            border-radius: 3px;
            background: white;
        }
        QCheckBox::indicator:checked {
            background: #2196F3;
            border-color: #2196F3;
        }
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            color: #212121;
            background: white;
            min-height: 25px;
            font-size: 10pt;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        QTableWidget {
            gridline-color: #e0e0e0;
            background: white;
            color: #212121;
            border: 1px solid #cccccc;
            font-size: 10pt;
            alternate-background-color: #f9f9f9;
        }
        QTableWidget::item {
            padding: 6px 8px;
            color: #212121;
            background: transparent;
        }
        QTableWidget::item:alternate {
            background: transparent;
        }
        QTableWidget::item:selected {
            background: #2196F3;
            color: white;
        }
        QHeaderView::section {
            background: #f5f5f5;
            color: #212121;
            padding: 8px;
            border: 1px solid #e0e0e0;
            font-weight: bold;
            font-size: 10pt;
        }
        QListWidget {
            background: white;
            color: #212121;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px;
            font-size: 10pt;
            alternate-background-color: #f9f9f9;
        }
        QListWidget::item {
            padding: 8px;
            color: #212121;
            border-radius: 2px;
            background: transparent;
        }
        QListWidget::item:alternate {
            background: transparent;
        }
        QListWidget::item:selected {
            background: #2196F3;
            color: white;
        }
        QMenuBar {
            background: #f5f5f5;
            color: #212121;
            padding: 4px;
            font-size: 10pt;
        }
        QMenuBar::item {
            padding: 6px 12px;
            background: transparent;
            color: #212121;
        }
        QMenuBar::item:selected {
            background: #e0e0e0;
            border-radius: 3px;
        }
        QMenu {
            background: white;
            color: #212121;
            border: 1px solid #cccccc;
            padding: 4px;
            font-size: 10pt;
        }
        QMenu::item {
            padding: 8px 24px;
            border-radius: 3px;
            color: #212121;
        }
        QMenu::item:selected {
            background: #2196F3;
            color: white;
        }
        QStatusBar {
            background: #f5f5f5;
            color: #212121;
            padding: 4px;
            font-size: 10pt;
        }
        QScrollBar:vertical {
            border: none;
            background: #f5f5f5;
            width: 14px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #cccccc;
            border-radius: 7px;
            min-height: 30px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: #b0b0b0;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #f5f5f5;
            height: 14px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #cccccc;
            border-radius: 7px;
            min-width: 30px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #b0b0b0;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QMessageBox {
            background: white;
            color: #212121;
        }
        QMessageBox QLabel {
            color: #212121;
            background: transparent;
            padding: 8px;
            font-size: 10pt;
        }
        QMessageBox QPushButton {
            min-width: 80px;
            padding: 8px 16px;
        }
        QDialog {
            background: white;
            color: #212121;
        }
        QDialog QLabel {
            color: #212121;
            padding: 4px;
            font-size: 10pt;
            background: transparent;
        }
        """
    
    def _get_dark_stylesheet(self):
        """Get dark mode stylesheet"""
        return """
        QMainWindow {
            background-color: #1e1e1e;
        }
        QWidget {
            color: #e0e0e0;
            font-size: 10pt;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QTabWidget::pane {
            border: 1px solid #3c3c3c;
            background: #2d2d2d;
            padding: 10px;
        }
        QTabBar::tab {
            background: #3c3c3c;
            color: #e0e0e0;
            padding: 10px 20px;
            margin-right: 2px;
            min-width: 100px;
        }
        QTabBar::tab:selected {
            background: #2d2d2d;
            color: #ffffff;
            border-bottom: 3px solid #2196F3;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
            min-height: 32px;
            font-size: 10pt;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QPushButton:disabled {
            background-color: #3c3c3c;
            color: #666666;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px 12px;
            background: #252525;
            color: #e0e0e0;
            min-height: 28px;
            font-size: 10pt;
            selection-background-color: #2196F3;
            selection-color: white;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QSpinBox {
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px 12px;
            background: #252525;
            color: #e0e0e0;
            min-height: 28px;
            font-size: 10pt;
        }
        QSpinBox:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QComboBox {
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px 12px;
            background: #252525;
            color: #e0e0e0;
            min-height: 28px;
            font-size: 10pt;
        }
        QComboBox:focus {
            border: 2px solid #2196F3;
            padding: 7px 11px;
        }
        QComboBox::drop-down {
            border: none;
            width: 25px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #e0e0e0;
            margin-right: 5px;
        }
        QComboBox QAbstractItemView {
            background: #252525;
            color: #e0e0e0;
            selection-background-color: #2196F3;
            selection-color: white;
            border: 1px solid #3c3c3c;
            padding: 4px;
        }
        QComboBox QAbstractItemView::item {
            padding: 6px 12px;
            min-height: 25px;
            color: #e0e0e0;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            background: #3c3c3c;
            border: none;
            width: 20px;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #4c4c4c;
        }
        QGroupBox {
            border: 2px solid #3c3c3c;
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
            padding-top: 20px;
            padding-left: 10px;
            padding-right: 10px;
            padding-bottom: 10px;
            color: #e0e0e0;
            background: #2d2d2d;
            font-size: 10pt;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: #e0e0e0;
            left: 8px;
            top: 2px;
        }
        QLabel {
            color: #e0e0e0;
            font-size: 10pt;
            background: transparent;
        }
        QScrollArea {
            background: #383838;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
        }
        QScrollArea > QWidget > QWidget {
            background: #383838;
        }
        QScrollArea QWidget {
            background: transparent;
        }
        QCheckBox {
            color: #e0e0e0;
            spacing: 8px;
            padding: 4px;
            font-size: 10pt;
        }
        QCheckBox::indicator {
            width: 20px;
            height: 20px;
            border: 2px solid #3c3c3c;
            border-radius: 3px;
            background: #252525;
        }
        QCheckBox::indicator:checked {
            background: #2196F3;
            border-color: #2196F3;
        }
        QProgressBar {
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            text-align: center;
            color: #e0e0e0;
            background: #252525;
            min-height: 25px;
            font-size: 10pt;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        QTableWidget {
            gridline-color: #3c3c3c;
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
            font-size: 10pt;
            alternate-background-color: #252525;
        }
        QTableWidget::item {
            padding: 6px 8px;
            color: #e0e0e0;
            background: transparent;
        }
        QTableWidget::item:alternate {
            background: transparent;
        }
        QTableWidget::item:selected {
            background: #2196F3;
            color: white;
        }
        QHeaderView::section {
            background: #3c3c3c;
            color: #e0e0e0;
            padding: 8px;
            border: 1px solid #4c4c4c;
            font-weight: bold;
            font-size: 10pt;
        }
        QListWidget {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 4px;
            font-size: 10pt;
            alternate-background-color: #252525;
        }
        QListWidget::item {
            padding: 8px;
            color: #e0e0e0;
            border-radius: 2px;
            background: transparent;
        }
        QListWidget::item:alternate {
            background: transparent;
        }
        QListWidget::item:selected {
            background: #2196F3;
            color: white;
        }
        QMenuBar {
            background: #2d2d2d;
            color: #e0e0e0;
            padding: 4px;
            font-size: 10pt;
        }
        QMenuBar::item {
            padding: 6px 12px;
            background: transparent;
            color: #e0e0e0;
        }
        QMenuBar::item:selected {
            background: #3c3c3c;
            border-radius: 3px;
        }
        QMenu {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3c3c3c;
            padding: 4px;
            font-size: 10pt;
        }
        QMenu::item {
            padding: 8px 24px;
            border-radius: 3px;
            color: #e0e0e0;
        }
        QMenu::item:selected {
            background: #2196F3;
            color: white;
        }
        QStatusBar {
            background: #2d2d2d;
            color: #e0e0e0;
            padding: 4px;
            font-size: 10pt;
        }
        QScrollBar:vertical {
            border: none;
            background: #2d2d2d;
            width: 14px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #5c5c5c;
            border-radius: 7px;
            min-height: 30px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6c6c6c;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #2d2d2d;
            height: 14px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #5c5c5c;
            border-radius: 7px;
            min-width: 30px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #6c6c6c;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QMessageBox {
            background: #2d2d2d;
            color: #e0e0e0;
        }
        QMessageBox QLabel {
            color: #e0e0e0;
            background: transparent;
            padding: 8px;
            font-size: 10pt;
        }
        QMessageBox QPushButton {
            min-width: 80px;
            padding: 8px 16px;
        }
        QDialog {
            background: #2d2d2d;
            color: #e0e0e0;
        }
        QDialog QLabel {
            color: #e0e0e0;
            padding: 4px;
            font-size: 10pt;
            background: transparent;
        }
        """
    
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
            <li>CRUD Operations with Validation</li>
            <li>Batch Processing (up to 1000 ops)</li>
            <li>Bulk Update/Delete with Filters</li>
            <li>Excel/CSV Mapper with visual field mapping</li>
            <li>Advanced Query Builder with OData/FetchXML</li>
            <li>Metadata Discovery with 24hr caching</li>
            <li>Template Library</li>
            <li>Plugin System (Hot-reload)</li>
            <li>Enhanced Exports (JSON, CSV, Excel, Power BI)</li>
            <li>Progress Indicators</li>
            <li>EntitySetName Support</li>
        </ul>
        <br>
        <p><b>Loaded Plugins:</b> {plugin_count}</p>
        <br>
        <hr>
        <p><b>Author:</b> Roshan Lal J</p>
        <p><b>Contact:</b> hello@roshanlaldia.top</p>
        <p><b>Made with ❤️ in:</b> Thuckalay, Tamil Nadu, India 🇮🇳</p>
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
                # If already connected, pass client to plugin
                if self.client and hasattr(tab_widget, 'set_client'):
                    tab_widget.set_client(self.client)
            
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
