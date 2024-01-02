from zk import ZK
from logger import ErpnextLogger, ErpnextFileHandler
from local_config import DeviceConfig
from datetime import datetime
import json


class AttendanceDevice:
    def __init__(
        self,
        device_config: DeviceConfig,
        error_logger: ErpnextLogger,
        status,
    ) -> None:
        self.attendances = []
        self.conn = None
        self.device_config = device_config
        self.error_logger = error_logger
        self.status = status

    def _connect(self):
        self.conn = ZK(ip=self.device_config.ip, timeout=self.device_config.timeout)
        return self.conn.connect()

    def _disconnect(self):
        if self.conn:
            self.conn.disconnect()

    def _disable_device(self):
        return self.conn.disable_device()

    def _enable_device(self):
        return self.conn.enable_device()

    def _fetch_attendance_from_device(self) :
        try:
            self._connect()
            self._disable_device()
            self.attendances = self.conn.get_attendance()
            self._enable_device()
            if self.clear_from_device_on_fetch:
                self.conn.clear_attendance()
        except Exception as e:
            self.error_logger.exception(
                str(self.device_config.ip)
                + f" exception when fetching from device: {e}"
            )
            raise Exception("Device fetch failed.")
        finally:
            self._disconnect()

    def _dump_attendance_data(self):
        dump_file_name = ErpnextFileHandler.get_dump_file_name_and_directory(
            self.device_config.device_id, self.device_config.ip
        )
        with open(dump_file_name, "w+") as f:
            f.write(
                json.dumps(
                    list(map(lambda x: x.__dict__, self.attendances)),
                    default=datetime.timestamp,
                )
            )

    def _get_all_attendance_from_device(self):
        self._fetch_attendance_from_device()
        if len(self.attendances):
            self._dump_attendance_data()
        self.status.set(f"{self.device_config.device_id}_push_timestamp", None)
        self.status.set(
            f"{self.device_config.device_id}_pull_timestamp",
            str(datetime.now()),
        )

    def get_attendance(self, clear_from_device_on_fetch):
        self.clear_from_device_on_fetch = clear_from_device_on_fetch
        self._get_all_attendance_from_device()
        return list(map(lambda x: x.__dict__, self.attendances))
