from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QPlainTextEdit,
    QHBoxLayout, QLineEdit, QLabel, QMessageBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
import sys

from app.database import Database
from app.core.crawl_worker import CrawlWorker
from app.logger import get_logger

class ScannerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Vulnerability Web App Scanner")
        self.setGeometry(200, 200, 820, 520)

        self.logger = get_logger()
        self.db = Database()
        self.worker = None
        self.current_project_id = None

        # --- Controls ---
        top = QHBoxLayout()
        top.addWidget(QLabel("Target URL:"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("https://example.com/")
        top.addWidget(self.target_input)

        top.addWidget(QLabel("Max Depth:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(0, 10)
        self.depth_spin.setValue(2)
        top.addWidget(self.depth_spin)

        self.same_domain_chk = QCheckBox("Same domain only")
        self.same_domain_chk.setChecked(True)
        top.addWidget(self.same_domain_chk)

        self.start_btn = QPushButton("Start Scan")
        self.stop_btn = QPushButton("Stop Scan")
        self.report_btn = QPushButton("Generate Report")
        self.upload_btn = QPushButton("Upload Payload")
        top.addWidget(self.start_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.report_btn)
        top.addWidget(self.upload_btn)

        # Log area
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Crawler logs will appear here…")

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.log_view)
        self.setLayout(layout)

        # wire buttons
        self.start_btn.clicked.connect(self.start_scan)
        self.stop_btn.clicked.connect(self.stop_scan)
        self.report_btn.clicked.connect(lambda: self.log("[REPORT] Phase 4"))
        self.upload_btn.clicked.connect(lambda: self.log("[PAYLOAD] Phase 3"))

    def log(self, text: str):
        self.log_view.appendPlainText(text)
        self.logger.info(text)

    def start_scan(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Scan Running", "Stop the current scan first.")
            return
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Missing Target", "Please enter a target URL.")
            return

        project_name = f"Crawl: {target}"
        self.current_project_id = self.db.create_project(project_name, target)
        self.log(f"[INFO] Project #{self.current_project_id} created.")

        self.worker = CrawlWorker(
            target_url=target,
            db=self.db,
            project_id=self.current_project_id,
            max_depth=self.depth_spin.value(),
            same_domain_only=self.same_domain_chk.isChecked(),
        )
        self.worker.progress.connect(self.log)
        self.worker.error.connect(lambda e: self.log(f"[FATAL] {e}"))
        self.worker.finished.connect(lambda: self.log("[INFO] Crawl finished."))
        self.worker.start()
        self.log("[INFO] Crawl started…")

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log("[INFO] Stop requested (will stop after current tasks).")
        else:
            self.log("[INFO] No active scan.")

def run_ui():
    app = QApplication(sys.argv)
    window = ScannerUI()
    window.show()
    sys.exit(app.exec_())
