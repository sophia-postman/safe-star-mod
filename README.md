# SafeStar Service API

Reference Python implementation of the **SafeStar Service API** — a microservice that tracks driver and vehicle safety metrics, runs asynchronous safety scans, generates diagnostic reports, and delivers personalised Driver Messages.

---

## Quick start

### Prerequisites

- Python 3.11 or later
- pip

### Install dependencies

```bash
cd safestar
pip install -r requirements.txt
```

### Run the server

```bash
cd safestar
python app.py
```

The server starts on **http://localhost:4500** (matching the `Local` Postman environment's `baseUrl`).

---

## Running the tests

```bash
cd safestar
python -m pytest tests/ -v
```

All 48 tests should pass in under a second.

---

## Endpoint reference

| Method   | Path                                  | Description                              |
|----------|---------------------------------------|------------------------------------------|
| `POST`   | `/driver/:id`                         | Create driver safety profile             |
| `GET`    | `/driver/:id`                         | Retrieve driver safety profile           |
| `PUT`    | `/driver/:id`                         | Replace driver safety profile            |
| `DELETE` | `/driver/:id`                         | Delete driver safety profile             |
| `POST`   | `/vehicle/:id`                        | Create vehicle safety profile            |
| `GET`    | `/vehicle/:id`                        | Retrieve vehicle safety profile          |
| `PATCH`  | `/vehicle/:id`                        | Partially update vehicle safety profile  |
| `DELETE` | `/vehicle/:id`                        | Delete vehicle safety profile            |
| `POST`   | `/run`                                | Start a safety scan run                  |
| `GET`    | `/run/:id`                            | Get run status                           |
| `DELETE` | `/run/:id`                            | Cancel a run                             |
| `POST`   | `/diagnostics/generate/:vehicleId`    | Generate diagnostic report               |
| `GET`    | `/diagnostics/:id`                    | Retrieve diagnostic report               |
| `POST`   | `/diagnostics/send/:id`               | Send diagnostic report                   |
| `GET`    | `/display`                            | Get driver message display               |

---

## Project layout

```
safestar/
  app.py            # Flask application — all routes and in-memory stores
  requirements.txt  # Runtime + test dependencies
  pytest.ini        # Pytest configuration
  tests/
    conftest.py         # Shared fixtures and sample payloads
    test_driver.py      # Driver Safety Profile tests
    test_vehicle.py     # Vehicle Safety Profile tests
    test_safety_scan.py # Safety Scan tests
    test_diagnostics.py # Diagnostics / Reporting tests
    test_display.py     # Display tests
postman/
  collections/SafeStar Service API/   # Postman collection (contract source)
  environments/                        # Local / Test / Prod environments
```

---

## Notes

- **Persistence** is in-memory only — data resets on server restart. This is intentional for a runnable reference implementation.
- The `Local` Postman environment points to `http://localhost:4500`, so you can send requests directly from Postman against the running server.
- The contract is derived entirely from the Postman collection request and example YAML files under `postman/collections/SafeStar Service API/`. No spec file is used.
