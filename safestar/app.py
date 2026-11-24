"""
SafeStar Service API — reference implementation.

Endpoints
---------
Driver Safety
  POST   /driver/:id          Create driver safety profile
  PUT    /driver/:id          Update driver safety profile (full replace)
  DELETE /driver/:id          Delete driver safety profile

Vehicle Safety
  POST   /vehicle/:id         Create vehicle safety profile
  GET    /vehicle/:id         Retrieve vehicle safety profile
  PATCH  /vehicle/:id         Update vehicle safety profile (partial)
  DELETE /vehicle/:id         Delete vehicle safety profile

Safety Scan
  POST   /run                 Start a safety scan run
  GET    /run/:id             Get run status
  DELETE /run/:id             Cancel a run

Diagnostics / Reporting
  POST   /diagnostics/generate/:vehicleId   Generate diagnostic report
  GET    /diagnostics/:id                   Retrieve diagnostic report
  POST   /diagnostics/send/:id              Send diagnostic report

Display
  GET    /display             Get driver message display
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------
_driver_profiles: dict[str, dict] = {}   # key = driver_id (path param)
_vehicle_profiles: dict[str, dict] = {}  # key = vehicle_id (path param)
_runs: dict[str, dict] = {}              # key = run_id (auto-incremented str)
_diagnostics: dict[str, dict] = {}       # key = diagnostic_id

_run_counter = 0
_diag_counter = 0


def _next_run_id() -> str:
    global _run_counter
    _run_counter += 1
    return str(_run_counter)


def _next_diag_id() -> str:
    global _diag_counter
    _diag_counter += 1
    return str(_diag_counter)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------
SENSOR_ENUM = {"OK", "LOW", "ERR"}


def _error(code: str, message: str, details: Any = None, status: int = 400):
    body = {"error": {"code": code, "message": message, "details": details or {}}}
    return jsonify(body), status


# ---------------------------------------------------------------------------
# Driver Safety
# ---------------------------------------------------------------------------

@app.route("/driver/<driver_id>", methods=["POST"])
def create_driver_profile(driver_id: str):
    if driver_id in _driver_profiles:
        existing = _driver_profiles[driver_id]
        return _error(
            "PROFILE_ALREADY_EXISTS",
            "A safety profile already exists for this driver.",
            {"driverId": driver_id, "existingProfileId": existing["profileId"]},
            409,
        )

    data = request.get_json(silent=True) or {}
    profile_id = str(uuid.uuid4())
    profile = {
        "profileId": profile_id,
        "driver": data.get("driver", {}),
        "safetyScore": data.get("safetyScore", 100),
        "hardStops": data.get("hardStops", 0),
        "speeding": data.get("speeding", 0),
        "nightDrives": data.get("nightDrives", 0),
        "weather": data.get("weather", 0),
        "ignoredWarnings": data.get("ignoredWarnings", 0),
    }
    _driver_profiles[driver_id] = profile
    return jsonify(profile), 201


@app.route("/driver/<driver_id>", methods=["PUT"])
def update_driver_profile(driver_id: str):
    profile = _driver_profiles.get(driver_id)
    if profile is None:
        return _error(
            "PROFILE_NOT_FOUND",
            "No safety profile found for the specified driver.",
            {"driverId": driver_id},
            404,
        )

    data = request.get_json(silent=True) or {}

    # Validate safetyScore if provided
    if "safetyScore" in data:
        score = data["safetyScore"]
        if not isinstance(score, (int, float)) or not (0 <= score <= 100):
            return _error(
                "VALIDATION_ERROR",
                "Request body failed validation.",
                {"fields": [{"field": "safetyScore", "issue": "must be an integer between 0 and 100"}]},
                400,
            )

    profile.update({
        "driver": data.get("driver", profile.get("driver", {})),
        "safetyScore": data.get("safetyScore", profile.get("safetyScore", 100)),
        "hardStops": data.get("hardStops", profile.get("hardStops", 0)),
        "speeding": data.get("speeding", profile.get("speeding", 0)),
        "nightDrives": data.get("nightDrives", profile.get("nightDrives", 0)),
        "weather": data.get("weather", profile.get("weather", 0)),
        "ignoredWarnings": data.get("ignoredWarnings", profile.get("ignoredWarnings", 0)),
    })
    return jsonify(profile), 200


@app.route("/driver/<driver_id>", methods=["DELETE"])
def delete_driver_profile(driver_id: str):
    if driver_id not in _driver_profiles:
        return _error(
            "PROFILE_NOT_FOUND",
            "No safety profile found for the specified driver.",
            {"driverId": driver_id},
            404,
        )
    del _driver_profiles[driver_id]
    return "", 204


# ---------------------------------------------------------------------------
# Vehicle Safety
# ---------------------------------------------------------------------------

def _validate_vehicle_body(data: dict) -> list[dict]:
    """Return a list of field-level validation errors."""
    errors = []
    if "vin" in data and len(str(data["vin"])) != 17:
        errors.append({"field": "vin", "issue": "must be 17 characters"})
    for field in ("tpms", "tailLights", "oilPressure", "sensors", "defrost", "airbags", "battery"):
        if field in data and data[field] not in SENSOR_ENUM:
            errors.append({"field": field, "issue": "value must be an enum: [OK, LOW, ERR]"})
    return errors


@app.route("/vehicle/<vehicle_id>", methods=["POST"])
def create_vehicle_profile(vehicle_id: str):
    if vehicle_id in _vehicle_profiles:
        existing = _vehicle_profiles[vehicle_id]
        return _error(
            "PROFILE_ALREADY_EXISTS",
            "A safety profile already exists for this vehicle.",
            {
                "vehicleId": vehicle_id,
                "existingProfileId": existing["profileId"],
                "vin": existing.get("vin", ""),
            },
            409,
        )

    data = request.get_json(silent=True) or {}
    field_errors = _validate_vehicle_body(data)
    if field_errors:
        return _error(
            "VALIDATION_ERROR",
            "Request body failed validation.",
            {"fields": field_errors},
            400,
        )

    profile_id = str(uuid.uuid4())
    vehicle_uuid = str(uuid.uuid4())
    now = _now_iso()
    profile = {
        "vehicleId": vehicle_uuid,
        "profileId": profile_id,
        "createdAt": now,
        "updatedAt": now,
        "status": "ACTIVE",
        "riskScore": 0,
        "vin": data.get("vin", ""),
        "make": data.get("make", ""),
        "model": data.get("model", ""),
        "year": data.get("year", 0),
        "tpms": data.get("tpms", "OK"),
        "tailLights": data.get("tailLights", "OK"),
        "oilPressure": data.get("oilPressure", "OK"),
        "sensors": data.get("sensors", "OK"),
        "defrost": data.get("defrost", "OK"),
        "airbags": data.get("airbags", "OK"),
        "battery": data.get("battery", "OK"),
        "newCode": data.get("newCode", False),
        "activeCodes": data.get("activeCodes", []),
        "metrics": {
            "hardCorneringEvents": 0,
            "hardBrakingEvents": 0,
            "speedingEvents": 0,
        },
    }
    _vehicle_profiles[vehicle_id] = profile
    return jsonify(profile), 201


@app.route("/vehicle/<vehicle_id>", methods=["GET"])
def get_vehicle_profile(vehicle_id: str):
    profile = _vehicle_profiles.get(vehicle_id)
    if profile is None:
        return _error(
            "VEHICLE_PROFILE_NOT_FOUND",
            "No safety profile found for the specified vehicle.",
            {"vehicleId": vehicle_id},
            404,
        )
    return jsonify(profile), 200


@app.route("/vehicle/<vehicle_id>", methods=["PATCH"])
def update_vehicle_profile(vehicle_id: str):
    profile = _vehicle_profiles.get(vehicle_id)
    if profile is None:
        return _error(
            "VEHICLE_PROFILE_NOT_FOUND",
            "No safety profile found for the specified vehicle.",
            {"vehicleId": vehicle_id},
            404,
        )

    data = request.get_json(silent=True) or {}
    field_errors = _validate_vehicle_body(data)
    if field_errors:
        return _error(
            "VALIDATION_ERROR",
            "Request body failed validation.",
            {"fields": field_errors},
            400,
        )

    for key, value in data.items():
        profile[key] = value
    profile["updatedAt"] = _now_iso()
    return jsonify(profile), 200


@app.route("/vehicle/<vehicle_id>", methods=["DELETE"])
def delete_vehicle_profile(vehicle_id: str):
    if vehicle_id not in _vehicle_profiles:
        return _error(
            "VEHICLE_PROFILE_NOT_FOUND",
            "No safety profile found for the specified vehicle.",
            {"vehicleId": vehicle_id},
            404,
        )
    del _vehicle_profiles[vehicle_id]
    return "", 204


# ---------------------------------------------------------------------------
# Safety Scan
# ---------------------------------------------------------------------------

@app.route("/run", methods=["POST"])
def start_run():
    data = request.get_json(silent=True) or {}
    run_id = _next_run_id()
    _runs[run_id] = {
        "run": run_id,
        "status": "QUEUED",
        "vehicle": data.get("vehicle"),
        "driver": data.get("driver"),
        "createdAt": _now_iso(),
    }
    return jsonify({"run": run_id, "status": "QUEUED"}), 201


@app.route("/run/<run_id>", methods=["GET"])
def get_run_status(run_id: str):
    run = _runs.get(run_id)
    if run is None:
        return _error(
            "RUN_NOT_FOUND",
            "No safety scan run found for the specified ID.",
            {"runId": run_id},
            404,
        )
    # Simulate progression: QUEUED → COMPLETE on first retrieval
    if run["status"] == "QUEUED":
        run["status"] = "COMPLETE"
    return jsonify({"run": run_id, "status": run["status"]}), 200


@app.route("/run/<run_id>", methods=["DELETE"])
def cancel_run(run_id: str):
    run = _runs.get(run_id)
    if run is None:
        return _error(
            "RUN_NOT_FOUND",
            "No safety scan run found for the specified ID.",
            {"runId": run_id},
            404,
        )
    run["status"] = "CANCELLED"
    return "", 200


# ---------------------------------------------------------------------------
# Diagnostics / Reporting
# ---------------------------------------------------------------------------

@app.route("/diagnostics/generate/<vehicle_id>", methods=["POST"])
def generate_diagnostic(vehicle_id: str):
    diag_id = _next_diag_id()
    vehicle = _vehicle_profiles.get(vehicle_id, {})
    active_codes = vehicle.get("activeCodes", [])

    _CODE_META = {
        "P0300": {
            "description": "Random/Multiple Cylinder Misfire Detected",
            "severity": "CRITICAL",
            "recommendedAction": "Inspect ignition system, spark plugs, and fuel injectors immediately.",
        },
        "P0420": {
            "description": "Catalyst System Efficiency Below Threshold",
            "severity": "MAJOR",
            "recommendedAction": "Inspect catalytic converter and oxygen sensors.",
        },
        "P0455": {
            "description": "Evaporative Emission System Leak (Large Leak)",
            "severity": "MAJOR",
            "recommendedAction": "Check fuel cap, EVAP hoses, and purge valve.",
        },
        "P0171": {
            "description": "System Too Lean (Bank 1)",
            "severity": "MAJOR",
            "recommendedAction": "Inspect for vacuum leaks and check fuel delivery system.",
        },
        "P0128": {
            "description": "Coolant Thermostat Temperature Below Regulating Temperature",
            "severity": "MODERATE",
            "recommendedAction": "Inspect thermostat and coolant temperature sensor.",
        },
    }

    enriched_codes = []
    for code in active_codes:
        meta = _CODE_META.get(code, {
            "description": "Unknown code",
            "severity": "UNKNOWN",
            "recommendedAction": "Consult a mechanic.",
        })
        enriched_codes.append({"code": code, **meta})

    severity_counts = {"CRITICAL": 0, "MAJOR": 0, "MODERATE": 0}
    for c in enriched_codes:
        sev = c.get("severity", "")
        if sev in severity_counts:
            severity_counts[sev] += 1

    overall = "SAFE TO RELEASE" if not active_codes else "NOT SAFE TO RELEASE"

    report = {
        "id": diag_id,
        "status": "success",
        "report": {
            "timestamp": _now_iso(),
            "status": "FAILED" if active_codes else "PASSED",
            "job": {
                "jobId": f"JOB-{diag_id}",
                "type": "VehicleSafetyScan",
                "completed": True,
                "durationMs": 0,
                "apiVersion": "v1.0.0",
            },
            "vehicle": {
                "id": vehicle_id,
                "vin": vehicle.get("vin", ""),
                "make": vehicle.get("make", ""),
                "model": vehicle.get("model", ""),
                "year": vehicle.get("year", 0),
            },
            "checks": {
                field: {"status": vehicle.get(field, "OK"), "severity": "NONE"}
                for field in ("tpms", "tailLights", "oilPressure", "sensors", "defrost", "airbags", "battery")
            },
            "diagnostics": {
                "newCodeDetected": vehicle.get("newCode", False),
                "activeCodes": enriched_codes,
                "failureReason": "Active diagnostic trouble codes detected during safety scan." if active_codes else None,
            },
            "summary": {
                "overallSafetyStatus": overall,
                "criticalIssues": severity_counts["CRITICAL"],
                "majorIssues": severity_counts["MAJOR"],
                "moderateIssues": severity_counts["MODERATE"],
                "notes": (
                    "Vehicle passed physical safety component checks but failed due to active engine diagnostic trouble codes."
                    if active_codes else "Vehicle passed all safety checks."
                ),
            },
        },
    }
    _diagnostics[diag_id] = report
    return jsonify({"status": "queued", "id": diag_id}), 201


@app.route("/diagnostics/<diag_id>", methods=["GET"])
def get_diagnostic(diag_id: str):
    report = _diagnostics.get(diag_id)
    if report is None:
        return _error(
            "DIAGNOSTIC_NOT_FOUND",
            "No diagnostic report found for the specified ID.",
            {"id": diag_id},
            404,
        )
    return jsonify(report), 200


@app.route("/diagnostics/send/<diag_id>", methods=["POST"])
def send_diagnostic(diag_id: str):
    if diag_id not in _diagnostics:
        return _error(
            "DIAGNOSTIC_NOT_FOUND",
            "No diagnostic report found for the specified ID.",
            {"id": diag_id},
            404,
        )
    # Mark as sent (no-op in reference impl)
    _diagnostics[diag_id]["sent"] = True
    return "", 204


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

@app.route("/display", methods=["GET"])
def get_display():
    data = request.get_json(silent=True) or {}
    driver_id = data.get("driver") or request.args.get("driver")
    vehicle_id = data.get("vehicle") or request.args.get("vehicle")

    driver_profile = _driver_profiles.get(str(driver_id), {}) if driver_id else {}
    vehicle_profile = _vehicle_profiles.get(str(vehicle_id), {}) if vehicle_id else {}

    driver_info = driver_profile.get("driver", {})
    first_name = driver_info.get("firstName", "Driver")
    safety_score = driver_profile.get("safetyScore", 0)
    active_codes = vehicle_profile.get("activeCodes", [])

    code_summary = ", ".join(active_codes) if active_codes else "none"
    message = (
        f" Hey {first_name} ! Safety score: {safety_score} - "
        f"keep up the great work! Active codes: {code_summary}."
    )
    html = (
        f"<div>🚗✅ Hey <b>{first_name}</b>! Safety score: <b>{safety_score}</b>. "
        f"Active codes: {code_summary}.</div>"
    )
    return jsonify({"message": message, "html": html}), 200


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

@app.errorhandler(Exception)
def handle_unexpected(exc):
    app.logger.exception("Unexpected error")
    return _error("UNEXPECTED_ERROR", "An unexpected error occurred.", {}, 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4500, debug=True)
