from local_config import erpnext_config, DeviceConfig, ErpNextConfig
from error_handler import allowlisted_errors, Errors
import requests
import datetime
import json
import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
import pickledb
from attendance import ZK, const
from utils import (
    _apply_function_to_key,
    _safe_convert_date,
    _safe_get_error_str,
    get_last_line_from_file,
)
from logger import ErpnextLogger, ErpnextFileHandler

ErpnextFileHandler.setup_dir()
error_logger = ErpnextLogger(
    "error_logger",
    os.path.join(ErpNextConfig.LOGS_DIRECTORY, "error.log"),
    logging.ERROR,
)
info_logger = ErpnextLogger(
    "info_logger", os.path.join(ErpNextConfig.LOGS_DIRECTORY, "logs.log")
)

status = pickledb.load(os.path.join(ErpNextConfig.LOGS_DIRECTORY, "status.json"), True)


def main():
    try:
        last_lift_off_timestamp = _safe_convert_date(
            status.get("lift_off_timestamp"), "%Y-%m-%d %H:%M:%S.%f"
        )
        if (
            last_lift_off_timestamp
            and last_lift_off_timestamp
            < datetime.datetime.now()
            - datetime.timedelta(minutes=erpnext_config.PULL_FREQUENCY)
        ) or not last_lift_off_timestamp:
            status.set("lift_off_timestamp", str(datetime.datetime.now()))
            info_logger.info("Cleared for lift off!")
            for device in erpnext_config.devices:
                device_attendance_logs = None
                info_logger.info("Processing Device: " + device.device_id)
                dump_file = ErpnextFileHandler.get_dump_file_name_and_directory(
                    device.device_id, device.ip
                )
                if os.path.exists(dump_file):
                    info_logger.error(
                        "Device Attendance Dump Found in Log Directory. This can mean the program crashed unexpectedly. Retrying with dumped data."
                    )
                    with open(dump_file, "r") as f:
                        file_contents = f.read()
                        if file_contents:
                            device_attendance_logs = list(
                                map(
                                    lambda x: _apply_function_to_key(
                                        x, "timestamp", datetime.datetime.fromtimestamp
                                    ),
                                    json.loads(file_contents),
                                )
                            )
                try:
                    pull_process_and_push_data(device, device_attendance_logs)
                    status.set(
                        f"{device.device_id}_push_timestamp",
                        str(datetime.datetime.now()),
                    )
                    if os.path.exists(dump_file):
                        os.remove(dump_file)
                    info_logger.info(
                        "Successfully processed Device: " + device.device_id
                    )
                except:
                    error_logger.exception(
                        "exception when calling pull_process_and_push_data function for device"
                        + json.dumps(device, default=str)
                    )
            if hasattr(erpnext_config, "shift_type_device_mapping"):
                update_shift_last_sync_timestamp(
                    erpnext_config.shift_type_device_mapping
                )
            status.set("mission_accomplished_timestamp", str(datetime.datetime.now()))
            info_logger.info("Mission Accomplished!")
    except:
        error_logger.exception("exception has occurred in the main function...")


def pull_process_and_push_data(device, device_attendance_logs=None):
    """Takes a single device erpnext_config as param and pulls data from that device.

    params:
    device: a single device erpnext_config object from the local_erpnext_config file
    device_attendance_logs: fetching from device is skipped if this param is passed. used to restart failed fetches from previous runs.
    """
    attendance_success_log_file = f"attendance_success_log_{device.device_id}"
    attendance_failed_log_file = f"attendance_failed_log_{device.device_id}"

    attendance_success_logger = ErpnextLogger(
        attendance_success_log_file,
        os.path.join(erpnext_config.LOGS_DIRECTORY, f"{attendance_success_log_file}.log")
    )

    attendance_failed_logger = ErpnextLogger(
        attendance_failed_log_file,
        os.path.join(erpnext_config.LOGS_DIRECTORY, f"{attendance_failed_log_file}.log")
    )

    if not device_attendance_logs:
        device_attendance_logs = ErpnextFileHandler.get_all_attendance_from_device(
            device.ip,
            device_id=device.device_id,
            clear_from_device_on_fetch=device.clear_from_device_on_fetch,
        )
        if not device_attendance_logs:
            return
    # for finding the last successfull push and restart from that point (or) from a set 'erpnext_config.IMPORT_START_DATE' (whichever is later)
    index_of_last = -1
    last_line = get_last_line_from_file(
        "/".join([erpnext_config.LOGS_DIRECTORY, attendance_success_log_file]) + ".log"
    )
    import_start_date = _safe_convert_date(erpnext_config.IMPORT_START_DATE, "%Y%m%d")
    if last_line or import_start_date:
        last_user_id = None
        last_timestamp = None
        if last_line:
            last_user_id, last_timestamp = last_line.split("\t")[4:6]
            last_timestamp = datetime.datetime.fromtimestamp(float(last_timestamp))
        if import_start_date:
            if last_timestamp:
                if last_timestamp < import_start_date:
                    last_timestamp = import_start_date
                    last_user_id = None
            else:
                last_timestamp = import_start_date
        for i, x in enumerate(device_attendance_logs):
            if last_user_id and last_timestamp:
                if (
                    last_user_id == str(x["user_id"])
                    and last_timestamp == x["timestamp"]
                ):
                    index_of_last = i
                    break
            elif last_timestamp:
                if x["timestamp"] >= last_timestamp:
                    index_of_last = i
                    break

    for device_attendance_log in device_attendance_logs[index_of_last + 1 :]:
        punch_direction = device.punch_direction
        if punch_direction == "AUTO":
            if device_attendance_log["punch"] in erpnext_config.device_punch_values_IN:
                punch_direction = "OUT"
            elif device_attendance_log["punch"] in erpnext_config.device_punch_values_OUT:
                punch_direction = "IN"
            else:
                punch_direction = None
        erpnext_status_code, erpnext_message = send_to_erpnext(
            device_attendance_log["user_id"],
            device_attendance_log["timestamp"],
            device.device_id,
            punch_direction,
        )
        if erpnext_status_code == 200:
            attendance_success_logger.info(
                "\t".join(
                    [
                        erpnext_message,
                        str(device_attendance_log["uid"]),
                        str(device_attendance_log["user_id"]),
                        str(device_attendance_log["timestamp"].timestamp()),
                        str(device_attendance_log["punch"]),
                        str(device_attendance_log["status"]),
                        json.dumps(device_attendance_log, default=str),
                    ]
                )
            )
        else:
            attendance_failed_logger.error(
                "\t".join(
                    [
                        str(erpnext_status_code),
                        str(device_attendance_log["uid"]),
                        str(device_attendance_log["user_id"]),
                        str(device_attendance_log["timestamp"].timestamp()),
                        str(device_attendance_log["punch"]),
                        str(device_attendance_log["status"]),
                        json.dumps(device_attendance_log, default=str),
                    ]
                )
            )
            if not (any(error in erpnext_message for error in allowlisted_errors)):
                raise Exception("API Call to ERPNext Failed.")




def update_shift_last_sync_timestamp(shift_type_device_mapping):
    """
    ### algo for updating the sync_current_timestamp
    - get a list of devices to check
    - check if all the devices have a non 'None' push_timestamp
        - check if the earliest of the pull timestamp is greater than sync_current_timestamp for each shift name
            - then update this min of pull timestamp to the shift

    """
    for shift_type_device_map in shift_type_device_mapping:
        all_devices_pushed = True
        pull_timestamp_array = []
        for device_id in shift_type_device_map.related_device_id:
            if not status.get(f"{device_id}_push_timestamp"):
                all_devices_pushed = False
                break
            pull_timestamp_array.append(
                _safe_convert_date(
                    status.get(f"{device_id}_pull_timestamp"), "%Y-%m-%d %H:%M:%S.%f"
                )
            )
        if all_devices_pushed:
            min_pull_timestamp = min(pull_timestamp_array)
            if isinstance(
                shift_type_device_map.shift_type_name, str
            ):  # for backward compatibility of erpnext_config file
                shift_type_device_map.shift_type_name = [
                    shift_type_device_map.shift_type_name
                ]
            for shift in shift_type_device_map.shift_type_name:
                try:
                    sync_current_timestamp = _safe_convert_date(
                        status.get(f"{shift}_sync_timestamp"), "%Y-%m-%d %H:%M:%S.%f"
                    )
                    if (
                        sync_current_timestamp
                        and min_pull_timestamp > sync_current_timestamp
                    ) or (min_pull_timestamp and not sync_current_timestamp):
                        response_code = send_shift_sync_to_erpnext(
                            shift, min_pull_timestamp
                        )
                        if response_code == 200:
                            status.set(
                                f"{shift}_sync_timestamp", str(min_pull_timestamp)
                            )
                except:
                    error_logger.exception(
                        "Exception in update_shift_last_sync_timestamp, for shift:"
                        + shift
                    )


def infinite_loop(sleep_time=15):
    print("Service Running...")
    try:
        while True:
            main()
            time.sleep(sleep_time)
    except BaseException as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    infinite_loop(sleep_time=erpnext_config.PULL_FREQUENCY)
