"""
Authentication Panel - Handles credentials and connection
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QFont

from client.metadata_client import MetadataClient
from utils.config import Config


class AuthThread(QThread):
    """Background thread for authentication"""
    
    success = pyqtSignal(object)  # MetadataClient
    error = pyqtSignal(str)
    
    def __init__(self, tenant_id, client_id, client_secret, org_url, cache_dir):
        super().__init__()
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.org_url = org_url
        self.cache_dir = cache_dir
    
    def run(self):
        """Execute authentication in background"""
        try:
            client = MetadataClient(
                self.tenant_id,
                self.client_id,
                self.client_secret,
                self.org_url,
                self.cache_dir
            )
            
            # Authenticate
            client.authenticate()
            
            self.success.emit(client)
        
        except Exception as e:
            self.error.emit(str(e))


class AuthPanel(QWidget):
    """Authentication panel widget"""
    
    authenticated = pyqtSignal(object)  # MetadataClient
    cache_refresh_requested = pyqtSignal()
    
    def __init__(self, config: Config):
        super().__init__()
        
        self.config = config
        self.client = None
        self.auth_thread = None
        
        self._create_ui()
        self._load_defaults()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Auth group
        auth_group = QGroupBox("🔐 Authentication")
        auth_layout = QVBoxLayout()
        
        # Tenant ID
        tenant_label = QLabel("Tenant ID:")
        self.tenant_input = QLineEdit()
        self.tenant_input.setPlaceholderText("Azure AD Tenant ID")
        auth_layout.addWidget(tenant_label)
        auth_layout.addWidget(self.tenant_input)
        
        # Client ID
        client_id_label = QLabel("Client ID:")
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("App Registration Client ID")
        auth_layout.addWidget(client_id_label)
        auth_layout.addWidget(self.client_id_input)
        
        # Client Secret
        client_secret_label = QLabel("Client Secret:")
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setPlaceholderText("App Registration Secret")
        auth_layout.addWidget(client_secret_label)
        auth_layout.addWidget(self.client_secret_input)
        
        # Environment selector
        env_label = QLabel("Environment:")
        self.env_combo = QComboBox()
        self.env_combo.currentTextChanged.connect(self._on_environment_changed)
        auth_layout.addWidget(env_label)
        auth_layout.addWidget(self.env_combo)
        
        # Org URL (read-only)
        org_url_label = QLabel("Organization URL:")
        self.org_url_display = QLineEdit()
        self.org_url_display.setReadOnly(True)
        self.org_url_display.setStyleSheet("background-color: #f0f0f0;")
        auth_layout.addWidget(org_url_label)
        auth_layout.addWidget(self.org_url_display)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("🔗 Connect")
        self.connect_button.clicked.connect(self._on_connect)
        button_layout.addWidget(self.connect_button)
        
        self.refresh_button = QPushButton("🔄 Refresh Schema")
        self.refresh_button.setEnabled(False)
        self.refresh_button.clicked.connect(self._on_refresh_cache)
        button_layout.addWidget(self.refresh_button)
        
        auth_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("⚪ Not Connected")
        self.status_label.setFont(QFont("", 10, QFont.Weight.Bold))
        auth_layout.addWidget(self.status_label)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        layout.addStretch()
    
    def _load_defaults(self):
        """Load default values from config"""
        # Load credentials
        tenant_id = self.config.get_tenant_id()
        if tenant_id:
            self.tenant_input.setText(tenant_id)
        
        client_id = self.config.get_client_id()
        if client_id:
            self.client_id_input.setText(client_id)
        
        client_secret = self.config.get_client_secret()
        if client_secret:
            self.client_secret_input.setText(client_secret)
        
        # Load environments
        environments = self.config.get_available_environments()
        
        if environments:
            self.env_combo.addItems(sorted(environments.keys()))
            # Trigger environment change to set org URL
            self._on_environment_changed(self.env_combo.currentText())
        else:
            self.env_combo.addItem("No environments configured")
            self.env_combo.setEnabled(False)
    
    def _on_environment_changed(self, env_name: str):
        """Handle environment selection change"""
        org_url = self.config.get_org_url(env_name)
        if org_url:
            self.org_url_display.setText(org_url)
    
    def _on_connect(self):
        """Handle connect button click"""
        # Validate inputs
        tenant_id = self.tenant_input.text().strip()
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        org_url = self.org_url_display.text().strip()
        
        if not all([tenant_id, client_id, client_secret, org_url]):
            QMessageBox.warning(
                self,
                "Missing Credentials",
                "Please fill in all required fields."
            )
            return
        
        # Disable button and show status
        self.connect_button.setEnabled(False)
        self.connect_button.setText("Connecting...")
        self.status_label.setText("🟡 Connecting...")
        
        # Start authentication in background thread
        cache_dir = self.config.get_cache_directory()
        
        self.auth_thread = AuthThread(
            tenant_id,
            client_id,
            client_secret,
            org_url,
            cache_dir
        )
        
        self.auth_thread.success.connect(self._on_auth_success)
        self.auth_thread.error.connect(self._on_auth_error)
        self.auth_thread.start()
    
    def _on_auth_success(self, client: MetadataClient):
        """Handle successful authentication"""
        self.client = client
        
        # Update UI
        self.connect_button.setEnabled(True)
        self.connect_button.setText("🔗 Connected")
        self.connect_button.setStyleSheet("background-color: #4CAF50;")
        
        self.refresh_button.setEnabled(True)
        
        self.status_label.setText("🟢 Connected")
        self.status_label.setStyleSheet("color: green;")
        
        # Emit signal
        self.authenticated.emit(client)
    
    def _on_auth_error(self, error_msg: str):
        """Handle authentication error"""
        # Update UI
        self.connect_button.setEnabled(True)
        self.connect_button.setText("🔗 Connect")
        
        self.status_label.setText("🔴 Connection Failed")
        self.status_label.setStyleSheet("color: red;")
        
        # Show error dialog
        QMessageBox.critical(
            self,
            "Authentication Error",
            f"Failed to connect:\n\n{error_msg}"
        )
    
    def _on_refresh_cache(self):
        """Handle cache refresh button click"""
        if self.client:
            self.cache_refresh_requested.emit()
            QMessageBox.information(
                self,
                "Cache Cleared",
                "Metadata cache has been cleared. Schema will be re-fetched on next use."
            )
    
    def get_current_environment(self) -> str:
        """Get currently selected environment name"""
        return self.env_combo.currentText()
