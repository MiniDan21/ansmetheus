import logging
from pathlib import Path

# Разобраться, что с этим делать
LOG_FILE = Path("ansmini.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)
