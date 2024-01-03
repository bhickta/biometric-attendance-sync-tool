from attendance import AttendanceDevice
from local_config import DeviceConfig, ErpNextConfig
import logging, os, pickledb
from logger import ErpnextLogger, ErpnextFileHandler
import datetime

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


@app.get("/logs")
def logs(clear_logs: bool = False):
    # logs_data = device.get_attendance(clear_logs)
    logs_data = [
        {
            "uid": 12,
            "user_id": "1",
            "timestamp": datetime.datetime(2024, 1, 3, 9, 3, 29),
            "status": 15,
            "punch": 0,
        },
        {
            "uid": 13,
            "user_id": "3",
            "timestamp": datetime.datetime(2024, 1, 3, 9, 11, 7),
            "status": 15,
            "punch": 0,
        },
    ]
    return logs_data