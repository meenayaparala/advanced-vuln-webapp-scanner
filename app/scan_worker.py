from PyQt5.QtCore import QObject, QThread, pyqtSignal
import time
import logging

class ScanWorker(QObject):
    progress = pyqtSignal(str)  # emits messages to UI
    finished = pyqtSignal()     # emits when scan ends

    def run(self):
        logging.info("Scan started...")
        for i in range(5):
            msg = f"Scanning step {i+1}/5..."
            self.progress.emit(msg)
            logging.info(msg)
            time.sleep(2)  # simulate scanning
        logging.info("Scan finished.")
        self.finished.emit()
