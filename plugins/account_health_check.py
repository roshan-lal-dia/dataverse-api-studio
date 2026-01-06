"""
Example Plugin: Account Health Check
Demonstrates plugin system capabilities
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QGroupBox, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, QThread
import json


def get_plugin_info():
    """Plugin metadata"""
    return {
        "name": "Account Health Check",
        "version": "1.0.0",
        "description": "Analyzes account data health and provides insights",
        "author": "Dataverse API Studio"
    }


class HealthCheckThread(QThread):
    """Background thread for health check operations"""
    
    progress = pyqtSignal(int, str)
    completed = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    def run(self):
        """Run health check analysis"""
        try:
            results = {
                "total_accounts": 0,
                "accounts_missing_phone": 0,
                "accounts_missing_email": 0,
                "accounts_missing_address": 0,
                "inactive_accounts": 0,
                "recommendations": []
            }
            
            # Query all accounts
            self.progress.emit(10, "Fetching accounts...")
            
            response = self.client.read_multiple(
                "accounts",
                None,
                ["name", "telephone1", "emailaddress1", "address1_line1", "statecode"],
                1000
            )
            
            if not response.get("success"):
                self.error.emit("Failed to fetch accounts")
                return
            
            accounts = response.get("data", [])
            results["total_accounts"] = len(accounts)
            
            self.progress.emit(50, "Analyzing data quality...")
            
            # Analyze each account
            for account in accounts:
                if not account.get("telephone1"):
                    results["accounts_missing_phone"] += 1
                
                if not account.get("emailaddress1"):
                    results["accounts_missing_email"] += 1
                
                if not account.get("address1_line1"):
                    results["accounts_missing_address"] += 1
                
                if account.get("statecode") == 1:  # Inactive
                    results["inactive_accounts"] += 1
            
            self.progress.emit(80, "Generating recommendations...")
            
            # Generate recommendations
            if results["accounts_missing_phone"] > results["total_accounts"] * 0.3:
                results["recommendations"].append(
                    f"⚠️ {results['accounts_missing_phone']} accounts missing phone numbers (>{30}%)"
                )
            
            if results["accounts_missing_email"] > results["total_accounts"] * 0.3:
                results["recommendations"].append(
                    f"⚠️ {results['accounts_missing_email']} accounts missing email addresses (>{30}%)"
                )
            
            if results["accounts_missing_address"] > results["total_accounts"] * 0.5:
                results["recommendations"].append(
                    f"⚠️ {results['accounts_missing_address']} accounts missing addresses (>{50}%)"
                )
            
            if results["inactive_accounts"] > results["total_accounts"] * 0.2:
                results["recommendations"].append(
                    f"ℹ️ {results['inactive_accounts']} inactive accounts - consider archiving"
                )
            
            if not results["recommendations"]:
                results["recommendations"].append("✅ Account data looks healthy!")
            
            self.progress.emit(100, "Analysis complete")
            self.completed.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))


class AccountHealthTab(QWidget):
    """Custom tab for account health check"""
    
    def __init__(self, main_window):
        super().__init__()
        
        self.main_window = main_window
        self.client = None
        self.health_thread = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("🏥 Account Health Check")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Analyze your account data to identify missing information and data quality issues. "
            "This plugin queries up to 1000 accounts and provides actionable insights."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(desc)
        
        # Run button
        self.run_button = QPushButton("🔍 Run Health Check")
        self.run_button.setMinimumHeight(50)
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self._run_health_check)
        layout.addWidget(self.run_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setPlaceholderText("Results will appear here after running health check...")
        results_layout.addWidget(self.results_display)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
    
    def set_client(self, client):
        """Set the Dataverse client"""
        self.client = client
        self.run_button.setEnabled(True)
    
    def _run_health_check(self):
        """Run health check analysis"""
        if not self.client:
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.run_button.setEnabled(False)
        self.results_display.clear()
        
        # Start background thread
        self.health_thread = HealthCheckThread(self.client)
        self.health_thread.progress.connect(self._update_progress)
        self.health_thread.completed.connect(self._display_results)
        self.health_thread.error.connect(self._handle_error)
        self.health_thread.start()
    
    def _update_progress(self, value: int, message: str):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def _display_results(self, results: dict):
        """Display health check results"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.run_button.setEnabled(True)
        
        # Format results
        output = []
        output.append("=" * 60)
        output.append("ACCOUNT HEALTH CHECK RESULTS")
        output.append("=" * 60)
        output.append("")
        
        output.append(f"Total Accounts Analyzed: {results['total_accounts']}")
        output.append("")
        
        output.append("DATA QUALITY METRICS:")
        output.append(f"  • Missing Phone: {results['accounts_missing_phone']} accounts")
        output.append(f"  • Missing Email: {results['accounts_missing_email']} accounts")
        output.append(f"  • Missing Address: {results['accounts_missing_address']} accounts")
        output.append(f"  • Inactive: {results['inactive_accounts']} accounts")
        output.append("")
        
        output.append("RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            output.append(f"  {rec}")
        output.append("")
        
        output.append("=" * 60)
        
        self.results_display.setPlainText("\n".join(output))


def register_tabs(main_window):
    """Register custom tabs"""
    tab = AccountHealthTab(main_window)
    return [(tab, "🏥 Health Check")]


def on_initialize(main_window):
    """Called when plugin is initialized"""
    print("Account Health Check plugin initialized")


def on_client_connected(client):
    """Called when client connects"""
    print("Account Health Check plugin: Client connected")
