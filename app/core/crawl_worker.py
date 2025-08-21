from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
from app.core.crawler import AsyncCrawler, CrawlConfig

class CrawlWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, target_url: str, db, project_id: int, max_depth: int = 2, same_domain_only: bool = True):
        super().__init__()
        self.target_url = target_url
        self.db = db
        self.project_id = project_id
        self.cfg = CrawlConfig(max_depth=max_depth, same_domain_only=same_domain_only)
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            def log_cb(msg: str):
                self.progress.emit(msg)

            crawler = AsyncCrawler(self.target_url, db=self.db, project_id=self.project_id, log_cb=log_cb, config=self.cfg)
            asyncio.run(crawler.run())
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
