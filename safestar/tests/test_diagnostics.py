"""Tests for Diagnostics / Reporting endpoints."""

import pytest
from tests.conftest import VEHICLE_PAYLOAD


class TestGenerateDiagnostic:
    def test_201_queued(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        r = client.post("/diagnostics/generate/1002")
        assert r.status_code == 201
        body = r.get_json()
        assert body["status"] == "queued"
        assert "id" in body

    def test_201_no_vehicle_profile(self, client):
        """Generate should still work even if no vehicle profile exists (graceful)."""
        r = client.post("/diagnostics/generate/9999")
        assert r.status_code == 201

    def test_id_increments(self, client):
        r1 = client.post("/diagnostics/generate/1002")
        r2 = client.post("/diagnostics/generate/1002")
        assert r1.get_json()["id"] != r2.get_json()["id"]


class TestRetrieveDiagnostic:
    def test_200_returns_report(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        gen_r = client.post("/diagnostics/generate/1002")
        diag_id = gen_r.get_json()["id"]

        r = client.get(f"/diagnostics/{diag_id}")
        assert r.status_code == 200
        body = r.get_json()
        assert body["id"] == diag_id
        assert body["status"] == "success"
        assert "report" in body

    def test_report_contains_checks(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        gen_r = client.post("/diagnostics/generate/1002")
        diag_id = gen_r.get_json()["id"]
        r = client.get(f"/diagnostics/{diag_id}")
        report = r.get_json()["report"]
        assert "checks" in report
        assert "tpms" in report["checks"]

    def test_report_contains_active_codes(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        gen_r = client.post("/diagnostics/generate/1002")
        diag_id = gen_r.get_json()["id"]
        r = client.get(f"/diagnostics/{diag_id}")
        diag = r.get_json()["report"]["diagnostics"]
        codes = [c["code"] for c in diag["activeCodes"]]
        assert "P0300" in codes

    def test_404_unknown_diagnostic(self, client):
        r = client.get("/diagnostics/9999")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "DIAGNOSTIC_NOT_FOUND"


class TestSendDiagnostic:
    def test_204_sends_report(self, client):
        client.post("/vehicle/1002", json=VEHICLE_PAYLOAD)
        gen_r = client.post("/diagnostics/generate/1002")
        diag_id = gen_r.get_json()["id"]
        r = client.post(f"/diagnostics/send/{diag_id}")
        assert r.status_code == 204
        assert r.data == b""

    def test_404_send_unknown_report(self, client):
        r = client.post("/diagnostics/send/9999")
        assert r.status_code == 404
        assert r.get_json()["error"]["code"] == "DIAGNOSTIC_NOT_FOUND"
