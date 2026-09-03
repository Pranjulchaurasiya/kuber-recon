"""test_wire_diagnostic.py
========================
Tests for Razorpay wire diagnostic separating network reachability from credential authentication.
"""

from unittest.mock import MagicMock, patch
import urllib.error
import pytest

from kuber_recon.wire_diagnostic import cli_main, run_wire_diagnostic


def test_wire_diagnostic_http_200_authenticated():
    """HTTP 200 means network is reachable AND credentials are valid."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.headers = {"x-razorpay-request-id": "req_mock_pass_12345"}
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = run_wire_diagnostic(is_live=False)
        assert res.network_reachable is True
        assert res.credentials_authenticated is True
        assert res.verified is True
        assert res.http_status == 200
        assert "Wire reachable and credentials authenticated" in res.message


def test_wire_diagnostic_http_401_rejected():
    """HTTP 401 means network is reachable, but credentials failed authentication."""
    mock_err = urllib.error.HTTPError(
        url="https://api.razorpay.com/v1/payments",
        code=401,
        msg="Unauthorized",
        hdrs={"x-razorpay-request-id": "req_mock_unauth_9999"},
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        res = run_wire_diagnostic(is_live=False)
        assert res.network_reachable is True
        assert res.credentials_authenticated is False
        assert res.verified is False
        assert res.http_status == 401
        assert "Network Reachable (TLS/DNS ok), but Credentials Rejected" in res.message


def test_wire_diagnostic_network_unreachable():
    """Network connection failure means network is unreachable and unauthenticated."""
    mock_err = urllib.error.URLError("Temporary DNS failure")

    with patch("urllib.request.urlopen", side_effect=mock_err):
        res = run_wire_diagnostic(is_live=False)
        assert res.network_reachable is False
        assert res.credentials_authenticated is False
        assert res.verified is False
        assert res.http_status == 0
        assert "Network Connection Failed" in res.message


def test_cli_main_exits_nonzero_on_unauthenticated():
    """cli_main must exit with status code 1 when credentials are not authenticated."""
    mock_err = urllib.error.HTTPError(
        url="https://api.razorpay.com/v1/payments",
        code=401,
        msg="Unauthorized",
        hdrs={"x-razorpay-request-id": "req_mock_unauth_9999"},
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=mock_err):
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 1


def test_cli_main_exits_zero_on_verified():
    """cli_main must exit with status code 0 when HTTP 200 verified."""
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.headers = {"x-razorpay-request-id": "req_mock_pass_12345"}
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        assert exc_info.value.code == 0
