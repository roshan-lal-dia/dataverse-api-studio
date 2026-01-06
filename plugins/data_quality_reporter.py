"""
Data Quality Reporter Plugin
Analyzes data quality across multiple entities and generates comprehensive reports
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QComboBox, QLabel, QGroupBox, QProgressBar, QMessageBox, QLineEdit
)
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
import json


class DataQualityThread(QThread):
    """Background thread for quality analysis"""
    
    progress = pyqtSignal(int, str)
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, client, entities):
        super().__init__()
        self.client = client
        self.entities = entities
    
    def run(self):
        """Run quality analysis"""
        try:
            results = {}
            total_entities = len(self.entities)
            
            for idx, entity in enumerate(self.entities):
                self.progress.emit(
                    int((idx / total_entities) * 100),
                    f"Analyzing {entity}..."
                )
                
                # Fetch records (limited to 100 for analysis)
                query_result = self.client.read_multiple(
                    entity,
                    filter_query=None,
                    select=None,
                    top=100
                )
                
                if query_result.get("success"):
                    records = query_result.get("data", [])
                    
                    # Analyze data quality
                    quality_metrics = self._analyze_records(entity, records)
                    results[entity] = quality_metrics
            
            self.progress.emit(100, "Analysis complete")
            self.success.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))
    
    def _analyze_records(self, entity, records):
        """Analyze records for quality metrics"""
        if not records:
            return {
                "total_records": 0,
                "empty_fields": {},
                "completeness_score": 0
            }
        
        total = len(records)
        empty_counts = {}
        
        # Analyze each field
        for record in records:
            for field, value in record.items():
                if field not in empty_counts:
                    empty_counts[field] = 0
                
                if value is None or value == "" or value == []:
                    empty_counts[field] += 1
        
        # Calculate completeness score
        total_fields = len(empty_counts)
        if total_fields == 0:
            completeness = 100
        else:
            filled_percentage = sum(
                ((total - count) / total) * 100 
                for count in empty_counts.values()
            ) / total_fields
            completeness = filled_percentage
        
        return {
            "total_records": total,
            "empty_fields": {
                field: {"count": count, "percentage": (count/total)*100}
                for field, count in empty_counts.items()
                if count > 0
            },
            "completeness_score": round(completeness, 2)
        }


class DataQualityReporterWidget(QWidget):
    """Data Quality Reporter plugin widget"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.thread = None
        self._create_ui()
    
    def _create_ui(self):
        """Create UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📊 Data Quality Reporter")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Analyze data quality across multiple entities. "
            "Checks for missing fields, empty values, and calculates completeness scores."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Entity selection
        entity_group = QGroupBox("Select Entities to Analyze")
        entity_layout = QVBoxLayout()
        
        self.entity_combo = QComboBox()
        self.entity_combo.addItems([
            "account, contact, lead",
            "opportunity, quote, order",
            "account, contact",
            "Custom selection..."
        ])
        self.entity_combo.currentTextChanged.connect(self._on_selection_changed)
        entity_layout.addWidget(QLabel("Quick selection:"))
        entity_layout.addWidget(self.entity_combo)
        
        # Custom entity input (initially hidden)
        self.custom_label = QLabel("Custom entities (comma-separated):")
        self.custom_label.setVisible(False)
        entity_layout.addWidget(self.custom_label)
        
        self.custom_entities = QLineEdit()
        self.custom_entities.setPlaceholderText("e.g., account, contact, lead, opportunity")
        self.custom_entities.setVisible(False)
        entity_layout.addWidget(self.custom_entities)
        
        entity_group.setLayout(entity_layout)
        layout.addWidget(entity_group)
        
        # Progress
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Results
        results_group = QGroupBox("Quality Report")
        results_layout = QVBoxLayout()
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setPlaceholderText("Analysis results will appear here...")
        results_layout.addWidget(self.results_display)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("📊 Run Quality Analysis")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.clicked.connect(self._run_analysis)
        self.analyze_button.setEnabled(False)
        button_layout.addWidget(self.analyze_button)
        
        self.export_button = QPushButton("💾 Export Report")
        self.export_button.clicked.connect(self._export_report)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
    
    def set_client(self, client):
        """Set Dataverse client"""
        self.client = client
        self.analyze_button.setEnabled(True)
    
    def _on_selection_changed(self, text):
        """Handle entity selection change"""
        is_custom = text == "Custom selection..."
        self.custom_label.setVisible(is_custom)
        self.custom_entities.setVisible(is_custom)
        
        if is_custom:
            self.custom_entities.setFocus()
    
    def _run_analysis(self):
        """Run quality analysis"""
        if not self.client:
            QMessageBox.warning(self, "Not Connected", "Please connect to Dataverse first.")
            return
        
        # Get selected entities
        selection = self.entity_combo.currentText()
        
        if selection == "Custom selection...":
            custom_input = self.custom_entities.text().strip()
            if not custom_input:
                QMessageBox.warning(
                    self, 
                    "No Entities", 
                    "Please enter entity names (comma-separated)."
                )
                return
            entities = [e.strip() for e in custom_input.split(",") if e.strip()]
            if not entities:
                QMessageBox.warning(
                    self, 
                    "Invalid Input", 
                    "Please enter valid entity names."
                )
                return
        else:
            entities = [e.strip() for e in selection.split(",")]
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.analyze_button.setEnabled(False)
        self.results_display.clear()
        
        # Start analysis
        self.thread = DataQualityThread(self.client, entities)
        self.thread.progress.connect(self._on_progress)
        self.thread.success.connect(self._on_success)
        self.thread.error.connect(self._on_error)
        self.thread.start()
    
    def _on_progress(self, percentage, message):
        """Update progress"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
    
    def _on_success(self, results):
        """Display results"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Format report
        report = self._format_report(results)
        self.results_display.setPlainText(report)
    
    def _on_error(self, error_msg):
        """Handle error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.analyze_button.setEnabled(True)
        
        QMessageBox.critical(self, "Analysis Failed", f"Error:\n{error_msg}")
    
    def _format_report(self, results):
        """Format analysis results as report"""
        report = []
        report.append("=" * 60)
        report.append("DATA QUALITY REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        total_entities = len(results)
        avg_completeness = sum(r["completeness_score"] for r in results.values()) / total_entities if total_entities > 0 else 0
        
        report.append("SUMMARY")
        report.append(f"  Entities Analyzed: {total_entities}")
        report.append(f"  Average Completeness: {avg_completeness:.2f}%")
        report.append("")
        
        # Detailed results per entity
        for entity, metrics in results.items():
            report.append(f"ENTITY: {entity.upper()}")
            report.append(f"  Total Records: {metrics['total_records']}")
            report.append(f"  Completeness Score: {metrics['completeness_score']}%")
            
            if metrics['empty_fields']:
                report.append(f"  Fields with Missing Data:")
                for field, data in sorted(
                    metrics['empty_fields'].items(),
                    key=lambda x: x[1]['percentage'],
                    reverse=True
                )[:10]:  # Top 10
                    report.append(
                        f"    • {field}: {data['count']} records ({data['percentage']:.1f}%)"
                    )
            else:
                report.append("  ✅ All fields populated!")
            
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        for entity, metrics in results.items():
            if metrics['completeness_score'] < 70:
                report.append(f"  ⚠️ {entity}: Low completeness ({metrics['completeness_score']}%) - Review data entry processes")
            
            critical_fields = [
                f for f, d in metrics['empty_fields'].items()
                if d['percentage'] > 50
            ]
            if critical_fields:
                report.append(f"  ⚠️ {entity}: Critical fields missing in >50% of records: {', '.join(critical_fields)}")
        
        if not any(m['completeness_score'] < 70 for m in results.values()):
            report.append("  ✅ Data quality looks good across all entities!")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _export_report(self):
        """Export report to file"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Quality Report",
            f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_display.toPlainText())
                
                QMessageBox.information(self, "Exported", f"Report exported to {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")


# Plugin interface functions
def get_plugin_info():
    """Return plugin metadata"""
    return {
        "name": "Data Quality Reporter",
        "version": "1.0.0",
        "description": "Analyzes data quality across entities and generates comprehensive reports",
        "author": "Roshan Lal J"
    }


def register_tabs(main_window):
    """Register plugin tabs"""
    widget = DataQualityReporterWidget()
    return [(widget, "📊 Quality Report")]


def on_initialize(main_window):
    """Initialize plugin"""
    print("Data Quality Reporter plugin initialized")


def on_client_connected(client):
    """Handle client connection"""
    # Plugin will receive client through set_client method
    pass
