"""Pytest fixtures shared across all test modules."""

import pytest

# Import the app and the in-memory stores so each test starts with a clean slate.
import safestar.app as app_module
from safestar.app import app


@pytest.fixture(autouse=True)
def reset_stores():
    """Clear all in-memory stores and reset counters before every test."""
    app_module._driver_profiles.clear()
    app_module._vehicle_profiles.clear()
    app_module._runs.clear()
    app_module._diagnostics.clear()
    app_module._run_counter = 0
    app_module._diag_counter = 0
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Reusable payloads
# ---------------------------------------------------------------------------

DRIVER_PAYLOAD = {
    "driver": {
        "firstName": "Alex",
        "lastName": "Johnson",
        "license": {
            "issueDate": "2022-05-14",
            "expiry": "2026-05-14",
            "issuingState": "CA",
            "restrictions": ["B"],
        },
        "email": "alex.johnson@example.com",
    },
    "safetyScore": 100,
    "hardStops": 0,
    "speeding": 0,
    "nightDrives": 0,
    "weather": 0,
    "ignoredWarnings": 0,
}

VEHICLE_PAYLOAD = {
    "vin": "1HGCM82633A004352",
    "tpms": "OK",
    "tailLights": "OK",
    "oilPressure": "OK",
    "sensors": "OK",
    "defrost": "OK",
    "airbags": "OK",
    "battery": "OK",
    "newCode": True,
    "activeCodes": ["P0300", "P0420", "P0455", "P0171", "P0128"],
}
