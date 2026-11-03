# Increment 16: Server and image API

### Main rules

- Web API is a humble adapter. It checks request shape, calls one use case, and maps the result. It holds no business rule.
- Only `main/settings.py` reads `os.environ`.
- A missing provider setting must not stop startup.

### Header

- **Increment:** 16
- **Capability:** Server and image API
- **Status:** `CRITICAL`
- **Depends on:** `15-view-and-export-use-cases.md`
- **Traces to:** Web API and Server Main in `architecture.md`; endpoint table in `srs.md`
- **SRS IDs:** **SRS-FR-010**, **SRS-FR-070**, **SRS-NFR-008**, **SRS-NFR-009**, **SRS-FR-007** (part; finished in increment 20), **SRS-FR-049** (part; finished in increment 26), **SRS-NFR-033** (part; finished in increment 28), **SRS-NFR-034** (part; finished in increment 28)

### Requirements

- **SRS-FR-010** (must): The system shall automatically delete uploaded images and working copies after a configurable period, with a default of 24 hours. (Sections 2.5 and 7)
- **SRS-FR-070** (must): The server shall return the stored local analysis of an image, including its regions, shapes, text, legend, and image type, as JSON. (Local-first change)
- **SRS-NFR-008** (must): The server shall validate all inputs. (NFR-2.3)
- **SRS-NFR-009** (must): The server shall limit image upload size to 10 MB. (NFR-2.3)
- **SRS-FR-007** (must): The system shall display an error message for unsupported or corrupted files. (FR-1.6)
- **SRS-FR-049** (must): The system shall provide all features without an account. (FR-12.2)
- **SRS-NFR-033** (must): The portal shall listen on port 9090 on all host interfaces and be reachable at `http://<host-ip>:9090` from another device on the same LAN. (NFR-8.1)
- **SRS-NFR-034** (should): The project repository shall include a README and setup guide that explain how to start the portal and reach it from another device on the LAN. (Section 2.6)

### Capability

The portal runs on port 9090 and serves the image endpoints from `srs.md`.

### What may change

`web_api/app.py`, `schemas.py`, `session.py`, `routers/images.py`, `main/settings.py`, `wiring.py`, `__main__.py`, `README.md`, and tests in `src/portal/tests/web_api/`.

### What must stay

Core and Color Engine stay as earlier increments left them. Add no endpoint beyond the `srs.md` table. Add no health endpoint.

### Implementation notes

**Endpoints**: `POST /api/images`, `POST /api/images/{id}/analyze`, `GET /api/images/{id}/render`, `GET /api/images/{id}/analysis`, `GET /api/images/{id}/color`, `GET /api/images/{id}/export`.

**`derived` parameters**

- Profile: `cvd_type` (`protan`, `deutan`, `tritan`, `achromatopsia`, `none`) and `severity` (0 to 1). `severity` is required with a CVD type and refused with `none`.
- Render: `view`, `strength`. Color: `x`, `y`. Export: `strength`.
- `image_id` must match `^[0-9a-f]{32}$`.

**`derived` error mapping**, as JSON `{"error": {"code", "message"}}`

| Error | Status |
| --- | --- |
| `InvalidImage` | 400 |
| Request validation, `InvalidCoordinates` | 422 |
| `ImageNotFound` | 404 |
| `NoEnhancementForProfile` | 409 |
| Upload over 10 MB | 413 |

**Upload size**: read at most 10 MB + 1 byte. A file of exactly 10 MB is accepted.

**Session**: `secrets.token_urlsafe` in an `HttpOnly`, `SameSite=Lax` cookie. Do not set `Secure`, because the portal uses plain HTTP on the LAN.

**Logging**: log the method, path template, status, and session ID for each request, so that SRS-NFR-021 can be measured. Never log a header or the API key.

**`Settings`** (`derived` defaults)

| Setting | Default |
| --- | --- |
| Retention | 24 hours (SRS-FR-010) |
| Confusion threshold | 10.0 |
| Purge interval | 3600 seconds |
| Data directory | `/data` |

Increments 17 and 18 add the AI settings.

**Purge**: `build_app` schedules `PurgeExpired` in the FastAPI `lifespan`.

**Server**: `main/__main__.py` calls `uvicorn.run(app, host="0.0.0.0", port=9090)`.

**README**: how to start with `docker compose up portal`, find the host IP, open `http://<host-ip>:9090`, and allow port 9090 through the firewall.

### Verification

Show each SRS observation in full:

- **SRS-FR-010**: With a short test period, the files are gone from the server after expiry, and the default configuration value is 24 hours.
- **SRS-FR-070**: After an upload with no AI provider configured, the endpoint returns each result for the test image, and an unknown image ID receives a client error response.
- **SRS-NFR-008**: Requests with invalid IDs, profile values, and coordinates each receive a client error response and do not cause a server error.
- **SRS-NFR-009**: An upload over 10 MB is rejected with an error message, and a 10 MB upload is accepted.

Show this part now. A later increment finishes the row:

- **SRS-FR-007**: `POST /api/images` returns a client error with a message for both bad files, and no image is stored.
- **SRS-FR-049**: No endpoint requires a sign in. A new client receives an anonymous session cookie.
- **SRS-NFR-033**: `docker compose up portal` listens on port 9090 on `0.0.0.0`, and a request from the host reaches it.
- **SRS-NFR-034**: `README.md` holds the setup guide and how to reach the portal from another LAN device.

Also confirm:

- With `portal` running and no provider configured, `curl -i -F file=@<fixture.png> -F cvd_type=none http://localhost:9090/api/images` returns an `image_id`, and `GET /api/images/<id>/analysis` returns its JSON.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/web_api
docker compose build
docker compose up portal
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

The first integration of all server parts and the first runtime wiring. Filters that passed alone can now fail on real uploads, and a server error can leak through missing validation.

### How to recognize failure

A 5xx on invalid input, `ModuleNotFoundError` for package data in the `runtime` image, the port is not reachable, or the data volume is not writable.

### Isolation test

Test each router with fake use cases first. Then run `build_app` in the `dev` container with a temporary data directory. Then run the `runtime` image. Use failure checks 1, 2, and 5 in `structure.md`.

### Rollback

Return the tree to the state that **`prompts/15-view-and-export-use-cases.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/15-view-and-export-use-cases.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Web API is a humble adapter. It checks request shape, calls one use case, and maps the result. It holds no business rule.
- Only `main/settings.py` reads `os.environ`.
- A missing provider setting must not stop startup.
