"""Tests for Vehicle Safety Profile endpoints."""

import pytest
from tests.conftest import VEHICLE_PAYLOAD


# ---------------------------------------------------------------------------
# POST /vehicle/:id  — Create
# ---------------------------------------------------------------------------

class TestCreateVehicleProfile:
    def test_201_creates_profile(self, client):
        r = client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        assert r.status_code == 201
        body = r.get_json()
        assert "profileId" in body
        assert "vehicleId" in body
        assert body["vin"] == "1HGCM82633A004352"
        assert body["status"] == "ACTIVE"

    def test_409_duplicate_profile(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        assert r.status_code == 409
        err = r.get_json()["error"]
        assert err["code"] == "PROFILE_ALREADY_EXISTS"
        assert "existingProfileId" in err["details"]

    def test_400_invalid_vin_length(self, client):
        bad = {**VEHICLE_PAYLOAD, "vin": "TOOSHORT"}
        r = client.post("/vehicle/1002", json=bad)
        assert r.status_code == 400
        err = r.get_json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        fields = err["details"]["fields"]
        assert any(f["field"] == "vin" for f in fields)

    def test_400_invalid_sensor_enum(self, client):
        bad = {**VEHICLE_PAYLOAD, "battery": "DEAD"}
        r = client.post("/vehicle/1002", json=bad)
        assert r.status_code == 400
        err = r.get_json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        fields = err["details"]["fields"]
        assert any(f["field"] == "battery" for f in fields)

    def test_content_type_json(self, client):
        r = client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        assert "application/json" in r.content_type


# ---------------------------------------------------------------------------
# GET /vehicle/:id  — Retrieve
# ---------------------------------------------------------------------------

class TestGetVehicleProfile:
    def test_200_returns_profile(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.get("/vehicle/1002")
        assert r.status_code == 200
        body = r.get_json()
        assert body["vin"] == "1HGCM82633A004352"
        assert body["tpms"] == "OK"

    def test_404_missing_profile(self, client):
        r = client.get("/vehicle/9999")
        assert r.status_code == 404
        err = r.get_json()["error"]
        assert err["code"] == "VEHICLE_PROFILE_NOT_FOUND"
        assert err["details"]["vehicleId"] == "9999"


# ---------------------------------------------------------------------------
# PATCH /vehicle/:id  — Partial update
# ---------------------------------------------------------------------------

class TestUpdateVehicleProfile:
    def test_200_partial_update(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.patch("/vehicle/1002", json={"newCode": False})
        assert r.status_code == 200
        body = r.get_json()
        assert body["newCode"] is False
        # Other fields unchanged
        assert body["vin"] == "1HGCM82633A004352"

    def test_400_invalid_sensor_value(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.patch("/vehicle/1002", json={"battery": "INVALID"})
        assert r.status_code == 400
        err = r.get_json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        fields = err["details"]["fields"]
        assert any(f["field"] == "battery" for f in fields)

    def test_404_update_missing_profile(self, client):
        r = client.patch("/vehicle/9999", json={"newCode": False})
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "VEHICLE_PROFILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /vehicle/:id  — Delete
# ---------------------------------------------------------------------------

class TestDeleteVehicleProfile:
    def test_204_deletes_profile(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.delete("/vehicle/1002")
        assert r.status_code == 204
        assert r.data == b""

    def test_404_delete_missing_profile(self, client):
        r = client.delete("/vehicle/9999")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "VEHICLE_PROFILE_NOT_FOUND"

    def test_get_after_delete_returns_404(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        client.delete("/vehicle/1002")
        r = client.get("/vehicle/1002")
        assert r.status_code == 404
