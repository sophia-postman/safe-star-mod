"""Tests for Safety Scan endpoints (POST /run, GET /run/:id, DELETE /run/:id)."""

import pytest
from tests.conftest import DRIVER_PAYLOAD, VEHICLE_PAYLOAD


RUN_PAYLOAD = {"vehicle": "1002", "driver": "1001"}


class TestStartRun:
    def test_201_queued(self, client):
        r = client.post("/run", json=RUN_PAYLOAD)
        assert r.status_code == 201
        body = r.get_json()
        assert body["status"] == "QUEUED"
        assert "run" in body

    def test_run_id_increments(self, client):
        r1 = client.post("/run", json=RUN_PAYLOAD)
        r2 = client.post("/run", json=RUN_PAYLOAD)
        id1 = r1.get_json()["run"]
        id2 = r2.get_json()["run"]
        assert id1 != id2

    def test_content_type_json(self, client):
        r = client.post("/run", json=RUN_PAYLOAD)
        assert "application/json" in r.content_type


class TestGetRunStatus:
    def test_200_complete_after_first_get(self, client):
        post_r = client.post("/run", json=RUN_PAYLOAD)
        run_id = post_r.get_json()["run"]
        r = client.get(f"/run/{run_id}")
        assert r.status_code == 200
        body = r.get_json()
        assert body["run"] == run_id
        assert body["status"] == "COMPLETE"

    def test_404_unknown_run(self, client):
        r = client.get("/run/9999")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "RUN_NOT_FOUND"


class TestCancelRun:
    def test_200_cancels_run(self, client):
        post_r = client.post("/run", json=RUN_PAYLOAD)
        run_id = post_r.get_json()["run"]
        r = client.delete(f"/run/{run_id}")
        assert r.status_code == 200

    def test_404_cancel_unknown_run(self, client):
        r = client.delete("/run/9999")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "RUN_NOT_FOUND"

    def test_status_is_cancelled_after_cancel(self, client):
        post_r = client.post("/run", json=RUN_PAYLOAD)
        run_id = post_r.get_json()["run"]
        client.delete(f"/run/{run_id}")
        r = client.get(f"/run/{run_id}")
        assert r.get_json()["status"] == "CANCELLED"
