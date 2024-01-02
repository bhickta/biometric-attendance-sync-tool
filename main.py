from attendance import AttendanceDevice
from local_config import DeviceConfig, ErpNextConfig
import logging, os, pickledb
from logger import ErpnextLogger, ErpnextFileHandler

ErpnextFileHandler.setup_dir()
device = DeviceConfig(
    device_id="1",
    ip="192.168.0.35",
    punch_direction="IN",
    clear_from_device_on_fetch=False,
)
error_logger = ErpnextLogger(
    "error_logger",
    os.path.join(ErpNextConfig.LOGS_DIRECTORY, "error.log"),
    logging.ERROR,
)
status = pickledb.load(os.path.join(ErpNextConfig.LOGS_DIRECTORY, "status.json"), True)
device = AttendanceDevice(device, error_logger, status)


from typing import Union

from fastapi import FastAPI

app = FastAPI()

@app.get("/get_logs/")
def read_logs(clear_logs: bool = False):
    logs_data = device.get_attendance(clear_logs)
    return logs_data