import os
import logging
import pickledb
from logging.handlers import RotatingFileHandler
from local_config import ErpNextConfig

class ErpnextLogger:
    def __init__(self, name, log_file, level=logging.INFO, formatter=None):
        self.name = name
        self.log_file = log_file
        self.level = level
        self.formatter = formatter if formatter else logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")

        self._setup_logger()

    def _setup_logger(self):
        handler = RotatingFileHandler(self.log_file, maxBytes=10000000, backupCount=50)
        handler.setFormatter(self.formatter)

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)

        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)

    def log(self, message):
        self.logger.log(self.level, message)

class ErpnextFileHandler:
    @staticmethod
    def get_dump_file_name_and_directory(device_id, device_ip):
        return os.path.join(
            ErpNextConfig.LOGS_DIRECTORY,
            f"{device_id}_{device_ip.replace('.', '_')}_last_fetch_dump.json"
        )

    def setup_dir():
        if not os.path.exists(ErpNextConfig.LOGS_DIRECTORY):
            os.makedirs(ErpNextConfig.LOGS_DIRECTORY)