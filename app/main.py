from .ui import run_ui
from .database import init_db
from .logger import get_logger

if __name__ == "__main__":
    logger = get_logger()
    logger.info("Starting Advanced Vulnerability Web App Scanner...")

    init_db()
    run_ui()
