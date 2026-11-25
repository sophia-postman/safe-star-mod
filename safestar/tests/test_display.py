"""Tests for the Display endpoint (GET /display)."""

import pytest
from tests.conftest import DRIVER_PAYLOAD, VEHICLE_PAYLOAD


class TestDisplay:
    def test_200_with_driver_and_vehicle(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.get("/display", json={"driver": "1001", "vehicle": "1002"})
        assert r.status_code == 200
        body = r.get_json()
        assert "message" in body
        assert "html" in body

    def test_message_contains_driver_name(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.get("/display", json={"driver": "1001", "vehicle": "1002"})
        body = r.get_json()
        assert "Alex" in body["message"]

    def test_message_contains_safety_score(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.get("/display", json={"driver": "1001", "vehicle": "1002"})
        body = r.get_json()
        assert "100" in body["message"]

    def test_200_no_profiles_returns_defaults(self, client):
        """Display should still return 200 even with no matching profiles."""
        r = client.get("/display", json={"driver": "0000", "vehicle": "0000"})
        assert r.status_code == 200
        body = r.get_json()
        assert "message" in body

    def test_html_field_present(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.get("/display", json={"driver": "1001", "vehicle": "1002"})
        body = r.get_json()
        assert "<div>" in body["html"]
