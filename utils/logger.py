import logging
import os


def setup_logger(base_dir):
    logging.basicConfig(
        filename=os.path.join(base_dir, "app.log"),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8",
    )
