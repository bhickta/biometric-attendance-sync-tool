import datetime, json, os


def get_last_line_from_file(file):
    # concerns to address(may be much later):
    # how will last line lookup work with log rotation when a new file is created?
    # - will that new file be empty at any time? or will it have a partial line from the previous file?
    line = None
    if os.stat(file).st_size < 5000:
        # quick hack to handle files with one line
        with open(file, "r") as f:
            for line in f:
                pass
    else:
        # optimized for large log files
        with open(file, "rb") as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
            line = f.readline().decode()
    return line


def _apply_function_to_key(obj, key, fn):
    obj[key] = fn(obj[key])
    return obj


def _safe_convert_date(datestring, pattern):
    try:
        return datetime.datetime.strptime(datestring, pattern)
    except:
        return None

def _safe_get_error_str(res):
    try:
        error_json = json.loads(res._content)
        if 'exc' in error_json: # this means traceback is available
            error_str = json.loads(error_json['exc'])[0]
        else:
            error_str = json.dumps(error_json)
    except:
        error_str = str(res.__dict__)
    return error_str