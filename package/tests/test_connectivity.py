from types import SimpleNamespace

from tue_api_wrapper import connectivity


def test_macos_reports_eduvpn_connection_without_assuming_provider(monkeypatch):
    monkeypatch.setattr(connectivity.sys, "platform", "darwin")
    monkeypatch.setattr(connectivity.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout='* (Connected) 123 VPN (org.eduvpn.app) "eduVPN"'))
    result = connectivity.eduvpn_status()
    assert result["status"] == "connected"
    assert result["university_profile_verified"] is False


def test_disconnected_vpn_does_not_imply_services_are_unreachable(monkeypatch):
    monkeypatch.setattr(connectivity, "eduvpn_status", lambda: {"status": "disconnected", "university_profile_verified": False})
    monkeypatch.setattr(connectivity.requests, "get", lambda *args, **kwargs: SimpleNamespace(status_code=302))
    result = connectivity.check_connectivity()
    assert result["vpn"]["status"] == "disconnected"
    assert all(value["status"] == "reachable" for value in result["services"].values())


def test_failed_probe_is_reported_without_falsely_diagnosing_vpn(monkeypatch):
    def fail(*args, **kwargs):
        raise connectivity.requests.exceptions.ConnectTimeout("timeout")
    monkeypatch.setattr(connectivity.requests, "get", fail)
    result = connectivity.probe_service("https://alma.uni-tuebingen.de/")
    assert result == {"status": "unreachable", "error": "ConnectTimeout"}
