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
        self.target_input.setPlaceholderText("http://testphp.vulnweb.com")
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
        from app.scan_worker import init_db, crawl
        from urllib.parse import urlparse
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Missing Target", "Please enter a target URL.")
            return
        domain = urlparse(target).netloc
        conn = init_db()
        self.log(f"[scan_worker] Starting crawl: {target}")
        try:
            from app.scan_worker import crawl
            crawl(target, domain, 0, conn, log_cb=self.log)
            self.log("[scan_worker] Crawl complete.")
        except Exception as e:
            self.log(f"[scan_worker] Error: {e}")

    def run_scan_worker(self):
        from app.scan_worker import init_db, crawl
        from urllib.parse import urlparse
        target = self.target_input.text().strip()
        if not target:
            self.log("[ERROR] Please enter a target URL.")
            return
        domain = urlparse(target).netloc
        conn = init_db()
        self.log(f"[scan_worker] Starting crawl: {target}")
        try:
            crawl(target, domain, 0, conn)
            self.log("[scan_worker] Crawl complete.")
        except Exception as e:
            self.log(f"[scan_worker] Error: {e}")

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
