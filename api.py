from local_config import ErpNextConfig
import requests
import json
from utils import _safe_get_error_str


class Api:
    def __init__(self, config: ErpNextConfig) -> None:
        self.set_defaults()
        self.config = config

    def set_defaults(self):
        self.__set_url()
        self._set_headers()

    def _set_url(self):
        endpoint = "hrms" if self.config.ERPNEXT_VERSION > 13 else "erpnext"
        self.urls.checkin = f"{self.config.ERPNEXT_URL}/api/method/{endpoint}.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field"

    def _set_headers(self):
        self.headers = {
            "Authorization": "token "
            + self.config.ERPNEXT_API_KEY
            + ":"
            + self.config.ERPNEXT_API_SECRET,
            "Accept": "application/json",
        }

    def send_to_erpnext(
        self, error_logger, employee_field_value, timestamp, device_id=None, log_type=None
    ):
        data = {
            "employee_field_value": employee_field_value,
            "timestamp": timestamp.__str__(),
            "device_id": device_id,
            "log_type": log_type,
        }
        response = requests.request("POST", self.urls.checkin, headers=self.headers, json=data)
        if response.status_code == 200:
            return 200, json.loads(response._content)["message"]["name"]
        else:
            error_str = _safe_get_error_str(response)
            error_logger.error(
                "\t".join(
                    [
                        "Error during ERPNext API Call",
                        str(employee_field_value),
                        str(timestamp.timestamp()),
                        str(device_id),
                        str(log_type),
                        error_str,
                    ]
                )
            )
            return response.status_code, error_str

    def send_shift_sync_to_erpnext(self, info_logger, error_logger, shift_type_name, sync_timestamp):
        self.urls.shift_type = self.config.ERPNEXT_URL + "/api/resource/Shift Type/" + shift_type_name
        data = {"last_sync_of_checkin": str(sync_timestamp)}
        try:
            response = requests.request("PUT", self.urls.shift_type, headers=self.headers, data=json.dumps(data))
            if response.status_code == 200:
                info_logger.info(
                    "\t".join(
                        [
                            "Shift Type last_sync_of_checkin Updated",
                            str(shift_type_name),
                            str(sync_timestamp.timestamp()),
                        ]
                    )
                )
            else:
                error_str = _safe_get_error_str(response)
                error_logger.error(
                    "\t".join(
                        [
                            "Error during ERPNext Shift Type API Call.",
                            str(shift_type_name),
                            str(sync_timestamp.timestamp()),
                            error_str,
                        ]
                    )
                )
            return response.status_code
        except:
            error_logger.exception(
                "\t".join(
                    [
                        "exception when updating last_sync_of_checkin in Shift Type",
                        str(shift_type_name),
                        str(sync_timestamp.timestamp()),
                    ]
                )
            )