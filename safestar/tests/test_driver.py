"""Tests for Driver Safety Profile endpoints."""

import json
import pytest
from tests.conftest import DRIVER_PAYLOAD


# ---------------------------------------------------------------------------
# POST /driver/:id  — Create
# ---------------------------------------------------------------------------

class TestCreateDriverProfile:
    def test_201_creates_profile(self, client):
        r = client.post("/driver/1001", json=DRIVER_PAYLOAD)
        assert r.status_code == 201
        body = r.get_json()
        assert "profileId" in body
        assert body["driver"]["firstName"] == "Alex"
        assert body["safetyScore"] == 100

    def test_201_empty_body_accepted(self, client):
        """POST with empty body should still create a profile with defaults."""
        r = client.post("/driver/1001", json={})
        assert r.status_code == 201
        body = r.get_json()
        assert "profileId" in body

    def test_409_duplicate_profile(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        r = client.post("/driver/1001", json=DRIVER_PAYLOAD)
        assert r.status_code == 409
        err = r.get_json()["error"]
        assert err["code"] == "PROFILE_ALREADY_EXISTS"
        assert "existingProfileId" in err["details"]

    def test_content_type_json(self, client):
        r = client.post("/driver/1001", json=DRIVER_PAYLOAD)
        assert "application/json" in r.content_type


# ---------------------------------------------------------------------------
# GET /driver/:id  — Retrieve
# ---------------------------------------------------------------------------

class TestGetDriverProfile:
    def test_200_returns_profile(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        r = client.get("/driver/1001")
        assert r.status_code == 200
        body = r.get_json()
        assert body["driver"]["firstName"] == "Alex"

    def test_404_missing_profile(self, client):
        r = client.get("/driver/0000")
        assert r.status_code == 404
        err = r.get_json()["error"]
        assert err["code"] == "PROFILE_NOT_FOUND"
        assert err["details"]["driverId"] == "0000"


# ---------------------------------------------------------------------------
# PUT /driver/:id  — Update
# ---------------------------------------------------------------------------

class TestUpdateDriverProfile:
    def test_200_updates_profile(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        updated = {**DRIVER_PAYLOAD, "safetyScore": 95, "speeding": 1}
        r = client.put("/driver/1001", json=updated)
        assert r.status_code == 200
        body = r.get_json()
        assert body["safetyScore"] == 95
        assert body["speeding"] == 1

    def test_400_safety_score_out_of_range(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        bad = {**DRIVER_PAYLOAD, "safetyScore": 110}
        r = client.put("/driver/1001", json=bad)
        assert r.status_code == 400
        err = r.get_json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        fields = err["details"]["fields"]
        assert any(f["field"] == "safetyScore" for f in fields)

    def test_400_safety_score_negative(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        bad = {**DRIVER_PAYLOAD, "safetyScore": -1}
        r = client.put("/driver/1001", json=bad)
        assert r.status_code == 400

    def test_404_update_missing_profile(self, client):
        r = client.put("/driver/9999", json=DRIVER_PAYLOAD)
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "PROFILE_NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /driver/:id  — Delete
# ---------------------------------------------------------------------------

class TestDeleteDriverProfile:
    def test_204_deletes_profile(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        r = client.delete("/driver/1001")
        assert r.status_code == 204
        assert r.data == b""

    def test_404_delete_missing_profile(self, client):
        r = client.delete("/driver/1001")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "PROFILE_NOT_FOUND"

    def test_get_after_delete_returns_404(self, client):
        client.post("/driver/1001", json=DRIVER_PAYLOAD)
        client.delete("/driver/1001")
        r = client.get("/driver/1001")
        assert r.status_code == 404
