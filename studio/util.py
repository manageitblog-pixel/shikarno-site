"""Спільні JSON без гонок (аудит 22.11, P0: до 4 агентів пишуть ті самі файли).
locked(path) — flock на path+'.lock'; write_json_atomic — tmp у тій же теці + os.replace;
update_json(path, fn, default) — блокування + читання + fn(data) + атомарний запис.
"""
import contextlib, fcntl, json, os, tempfile


@contextlib.contextmanager
def locked(path):
    with open(str(path) + ".lock", "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)


def read_json(path, default=None):
    try:
        with open(path) as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default() if callable(default) else default


def write_json_atomic(path, data, **kw):
    kw.setdefault("ensure_ascii", False); kw.setdefault("indent", 1)
    path = os.path.realpath(path); d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix="." + os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f: json.dump(data, f, **kw)
        if os.path.exists(path): os.chmod(tmp, os.stat(path).st_mode & 0o777)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError): os.unlink(tmp)
        raise


def update_json(path, fn, default=None, **kw):
    """fn(data) змінює data на місці або повертає нове значення; повертає записане."""
    with locked(path):
        data = read_json(path, default)
        r = fn(data)
        if r is not None: data = r
        write_json_atomic(path, data, **kw)
        return data
