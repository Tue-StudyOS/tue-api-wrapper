"""Read-only VPN and service reachability diagnostics."""
from __future__ import annotations

import re
import subprocess
import sys

import requests

SERVICES = {
    "alma": "https://alma.uni-tuebingen.de/",
    "ilias": "https://ovidius.uni-tuebingen.de/",
    "moodle": "https://moodle.zdv.uni-tuebingen.de/",
}
VPN_GUIDE = "https://uni-tuebingen.de/einrichtungen/zentrum-fuer-datenverarbeitung/dienstleistungen/netze/netzzugang/remote-zugang-vpn/"


def eduvpn_status() -> dict:
    result = {"status": "unknown", "university_profile_verified": False}
    if sys.platform != "darwin":
        return {**result, "reason": "Automatic eduVPN detection is currently available on macOS only."}
    try:
        process = subprocess.run(["/usr/sbin/scutil", "--nc", "list"], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {**result, "reason": "Unable to inspect macOS network connections."}
    if process.returncode != 0:
        return {**result, "reason": "macOS network connection inspection failed."}
    lines = [line for line in process.stdout.splitlines() if "org.eduvpn.app" in line.casefold()]
    if any(re.search(r"\(Connected\)", line, re.IGNORECASE) for line in lines):
        result["status"] = "connected"
    elif lines and all(re.search(r"\(Disconnected\)", line, re.IGNORECASE) for line in lines):
        result["status"] = "disconnected"
    return {**result, "reason": "The active institution and actual routing cannot be verified from this status."}


def probe_service(url: str) -> dict:
    try:
        response = requests.get(url, timeout=(4, 4), allow_redirects=False)
        return {"status": "reachable", "http_status": response.status_code}
    except requests.RequestException as error:
        return {"status": "unreachable", "error": type(error).__name__}


def check_connectivity() -> dict:
    return {"vpn": eduvpn_status(), "services": {name: probe_service(url) for name, url in SERVICES.items()},
            "guide": VPN_GUIDE, "note": "Reachability does not verify authentication or authorization."}
