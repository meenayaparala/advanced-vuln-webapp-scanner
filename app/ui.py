from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
import sys

class ScannerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Vulnerability Web App Scanner")
        self.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()

        self.start_btn = QPushButton("Start Scan")
        self.stop_btn = QPushButton("Stop Scan")
        self.report_btn = QPushButton("Generate Report")
        self.upload_btn = QPushButton("Upload Payload")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.report_btn)
        layout.addWidget(self.upload_btn)

        self.setLayout(layout)

def run_ui():
    app = QApplication(sys.argv)
    window = ScannerUI()
    window.show()
    sys.exit(app.exec_())
