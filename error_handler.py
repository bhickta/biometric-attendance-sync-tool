from local_config import erpnext_config
from dataclasses import dataclass

@dataclass
class Errors:
    EMPLOYEE_NOT_FOUND_ERROR_MESSAGE = "No Employee found for the given employee field value"
    EMPLOYEE_INACTIVE_ERROR_MESSAGE = "Transactions cannot be created for an Inactive Employee"
    DUPLICATE_EMPLOYEE_CHECKIN_ERROR_MESSAGE = "This employee already has a log with the same timestamp"

def get_allowed_errors(allowlisted_errors):
    if hasattr(erpnext_config, 'allowed_exceptions'):
        allowlisted_errors_temp = []
        for error_number in erpnext_config.allowed_exceptions:
            allowlisted_errors_temp.append(allowlisted_errors[error_number - 1])
        allowlisted_errors = allowlisted_errors_temp
    return allowlisted_errors

allowlisted_errors = [Errors.EMPLOYEE_NOT_FOUND_ERROR_MESSAGE, Errors.EMPLOYEE_INACTIVE_ERROR_MESSAGE, Errors.DUPLICATE_EMPLOYEE_CHECKIN_ERROR_MESSAGE]
allowlisted_errors = get_allowed_errors(allowlisted_errors)