import os
import platform
import socket
import sys
from datetime import datetime, timezone


def collect_device_information() -> dict[str, object]:
    """Collect only backend-host facts, and only when explicitly requested."""
    hostname = None
    try:
        hostname = socket.gethostname()
    except OSError:
        pass

    return {
        "operating_system": platform.system() or "Unavailable",
        "os_version": platform.version() or "Unavailable",
        "os_release": platform.release() or "Unavailable",
        "machine_architecture": platform.machine() or "Unavailable",
        "processor": platform.processor() or "Unavailable",
        "python_runtime": sys.version.split()[0] if sys.version else "Unavailable",
        "python_implementation": platform.python_implementation() or "Unavailable",
        "hostname": hostname or "Unavailable",
        "application_environment": os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "Application runtime",
        "collected_at": datetime.now(timezone.utc),
        "limitation": "This information describes the machine running the Flask backend, not necessarily the browser user's device.",
    }
