# Increment 27: Measured targets and offline run

### Main rules

- Run timing tests in the reference container, which is limited to 4 CPU cores and 8 GB.
- Report the measured numbers. Do not change a threshold to make a test pass.
- `srs.md` marks timing numbers as provisional, so a miss on a `should` row is a yellow result to report, not a reason to rewrite the architecture.

### Header

- **Increment:** 27
- **Capability:** Measured targets and offline run
- **Status:** `Standard`
- **Depends on:** `26-accessibility-checks.md`
- **Traces to:** Performance section and quality rows in `srs.md`
- **SRS IDs:** **SRS-NFR-001**, **SRS-NFR-002**, **SRS-NFR-003**, **SRS-NFR-007**, **SRS-NFR-020**, **SRS-NFR-024**, **SRS-NFR-028**, **SRS-NFR-041**

### Requirements

- **SRS-NFR-001** (should): Simulation and enhancement of a preview sized image of up to 2 megapixels shall complete in under 1 second on the reference host. (NFR-1.1)
- **SRS-NFR-002** (should): A 12 megapixel export shall complete in under 5 seconds on the reference host. (NFR-1.1)
- **SRS-NFR-003** (should): Confusion detection shall complete in under 500 milliseconds on a downscaled image on the reference host. (NFR-1.2)
- **SRS-NFR-007** (must): API keys for third party services shall reside only on the server. (NFR-2.2)
- **SRS-NFR-020** (must): All features except AI interpretation shall work when the server has no internet connection. (Section 2.4; local-first change)
- **SRS-NFR-024** (should): Targeted enhancement shall reduce confusable pairs by at least 80 percent on the flat graphics test dataset. (NFR-6.2)
- **SRS-NFR-028** (must): Unit tests shall cover at least 70 percent of the color engine code. (NFR-7.1)
- **SRS-NFR-041** (should): Local image analysis, including text recognition, of an image of up to 12 megapixels shall complete in under 10 seconds on the reference host. (Local-first change)

### Capability

Tests measure the speed, coverage, secret handling, and offline behavior that the SRS requires.

### What may change

`src/portal/tests/core/test_timing.py`, `src/portal/tests/web_api/test_no_api_key_exposed.py`, `src/portal/tests/core/test_offline_pipeline.py`, `src/color_engine/tests/pipeline/test_filter_9_enhance.py`, and code only where a measurement proves a defect.

### What must stay

Add no queue, worker, cache layer, or other part to meet a number. Parts and decisions stay as `architecture.md` states them.

### Implementation notes

- **Timing**: 2 megapixel simulation and enhancement, 12 megapixel export, detection on a downscaled image, and local analysis at 12 megapixels. Print each measurement.
- **SRS-NFR-007**: set a known fake API key, search all delivered pages and scripts and each API response, and also the captured logs. Assert that it appears nowhere.
- **SRS-NFR-020**: run with no network, using `docker run --rm --network none` on the `dev` image. Cover upload, local analysis, simulation, enhancement, color identification, and export.
- **SRS-NFR-024**: run over `tests/data/flat_graphics/` and print the total before and after pair counts.

### Verification

Show each SRS observation in full:

- **SRS-NFR-001**: A timing test on a 2 megapixel image in the reference container reports under 1 second.
- **SRS-NFR-002**: A timing test on a 12 megapixel export in the reference container reports under 5 seconds.
- **SRS-NFR-003**: A timing test of detection on a downscaled image in the reference container reports under 500 milliseconds.
- **SRS-NFR-007**: A search of browser delivered assets and API responses finds no API key.
- **SRS-NFR-020**: With server internet access blocked, upload, local image analysis, simulation, enhancement, color identification, and export all complete.
- **SRS-NFR-024**: The before and after confusable pair counts over the dataset show a reduction of at least 80 percent.
- **SRS-NFR-028**: The coverage report for the package shows at least 70 percent.
- **SRS-NFR-041**: A timing test on a 12 megapixel image in the reference container reports under 10 seconds.

Run from the repository root:

```
docker compose build
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70
docker compose run --rm dev pytest src/portal/tests
```

### Main rules again

- Run timing tests in the reference container, which is limited to 4 CPU cores and 8 GB.
- Report the measured numbers. Do not change a threshold to make a test pass.
- `srs.md` marks timing numbers as provisional, so a miss on a `should` row is a yellow result to report, not a reason to rewrite the architecture.
