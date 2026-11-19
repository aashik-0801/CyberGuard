import os
import socket
from datetime import datetime, timezone


def _read_dns_configuration() -> list[str]:
    values: list[str] = []
    resolv_path = "/etc/resolv.conf"
    if os.path.exists(resolv_path):
        try:
            with open(resolv_path, "r", encoding="utf-8") as resolv:
                for line in resolv:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0] == "nameserver" and parts[1] not in values:
                        values.append(parts[1])
        except (OSError, UnicodeDecodeError):
            pass
    return values


def _read_default_gateway() -> str | None:
    route_path = "/proc/net/route"
    if not os.path.exists(route_path):
        return None
    try:
        with open(route_path, "r", encoding="ascii") as routes:
            next(routes, None)
            for line in routes:
                fields = line.strip().split()
                if len(fields) >= 8 and fields[1].upper() == "00000000" and fields[7] != "0":
                    raw = bytes.fromhex(fields[2])
                    return ".".join(str(value) for value in raw[::-1])
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return None


def collect_network_information() -> dict[str, object]:
    """Collect local socket/interface facts without scanning or packet interception."""
    hostname = None
    local_ip = None
    interfaces: list[str] = []

    try:
        hostname = socket.gethostname()
    except OSError:
        pass

    try:
        host_addresses = socket.getaddrinfo(hostname or "localhost", None)
        for family, _kind, _proto, _canonical, address in host_addresses:
            if family == socket.AF_INET:
                value = address[0]
                if not value.startswith("127.") and value not in interfaces:
                    interfaces.append(value)
        if not interfaces:
            interfaces = sorted({
                value[4][0]
                for value in socket.getaddrinfo(hostname or "localhost", None)
                if value[0] == socket.AF_INET and not value[4][0].startswith("127.")
            })
    except (OSError, socket.gaierror):
        pass

    if interfaces:
        local_ip = interfaces[0]

    return {
        "hostname": hostname or "Unavailable",
        "local_ip": local_ip or "Unavailable",
        "interfaces": interfaces,
        "default_gateway": _read_default_gateway() or "Unavailable",
        "dns_servers": _read_dns_configuration(),
        "connectivity_status": "Not externally tested",
        "collected_at": datetime.now(timezone.utc),
        "limitation": "Local configuration facts only. CyberGuard does not scan devices, ports, or network traffic.",
    }
