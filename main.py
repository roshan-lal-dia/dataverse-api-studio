#!/usr/bin/env python3
"""
Dataverse API Studio - Professional Edition
Main entry point for PyQt6 application
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Dataverse API Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Dataverse API Studio")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
