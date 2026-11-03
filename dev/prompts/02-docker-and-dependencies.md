# Increment 2: Docker image and dependencies

### Main rules

- Install `src/color_engine` before `src/portal` in every image target.
- Keep FastAPI and every web dependency out of `src/color_engine/pyproject.toml` and out of the `engine-test` target.
- Use the libraries in the `structure.md` tables. Do not swap one for an equivalent.

### Header

- **Increment:** 2
- **Capability:** Docker image and dependencies
- **Status:** `Standard`
- **Depends on:** `01-project-skeleton.md`
- **Traces to:** Stack in `architecture.md`; Dockerfile and Compose rows in `structure.md`
- **SRS IDs:** **SRS-NFR-027**, **SRS-NFR-032**

### Requirements

- **SRS-NFR-027** (must): The color engine shall be a separate Python package. (NFR-7.1)
- **SRS-NFR-032** (must): The color engine shall not depend on the web framework. (NFR-7.4)

### Capability

`docker compose build` produces the `engine-test`, `dev`, and `runtime` targets with all project dependencies installed.

### What may change

Create `Dockerfile`, `docker-compose.yml`, and `.devcontainer/devcontainer.json`. Add dependencies to both `pyproject.toml` files. Add `src/color_engine/tests/rules/test_package_smoke.py` and `src/portal/tests/core/test_package_smoke.py`.

### What must stay

The tree from increment 1 stays as it is. Add no application behavior.

### Implementation notes

- **`Dockerfile`**: multi-stage on a Python 3.11 base with targets `engine-test`, `dev`, and `runtime`. Every target installs Tesseract and its English data (`tesseract-ocr`, `tesseract-ocr-eng`).
- **`engine-test`**: installs `src/color_engine` with its test extras, and runs `pytest src/color_engine/tests` during the image build. This installs no web framework.
- **`dev`**: installs both packages in editable mode with all test tools, and Playwright Chromium with its system dependencies.
- **`runtime`**: installs both packages without test tools.
- **Color Engine dependencies**: `numpy`, `Pillow`, `pillow-heif`, `scikit-image`, `scikit-learn`, `opencv-python-headless`, `pytesseract`. **Test extras**: `pytest`, `pytest-cov`, `daltonlens`.
- **Portal dependencies**: `fastapi`, `uvicorn`, `python-multipart`, `jinja2`, `httpx`. **Test extras**: `pytest`, `playwright`, `axe-playwright-python`, `ruff`, `import-linter`.
- **`docker-compose.yml`**: service `portal` (target `runtime`, port `9090:9090`, data volume, `.env` optional, entry `python -m chromasense.main`), service `dev` (target `dev`, repository mounted, working directory at the repository root), and a named data volume. Limit `portal` and `dev` to 4 CPUs and 8 GB, because `srs.md` defines that as the reference host.
- The smoke tests only import the package, so `pytest` has one test to run. `chromasense.main` may not exist yet, so do not start `portal` in this increment.

### Verification

Show each SRS observation in full:

- **SRS-NFR-027**: The package installs and its tests run on their own, without the rest of the application.
- **SRS-NFR-032**: The color engine's tests pass in an environment where the web framework is not installed.

Also confirm:

- `docker compose run --rm dev pytest src/portal/tests/core/test_package_smoke.py` passes.
- `pip list` in the `engine-test` image shows no `fastapi`.

Run from the repository root:

```
docker compose build
docker build --target engine-test .
```

### Main rules again

- Install `src/color_engine` before `src/portal` in every image target.
- Keep FastAPI and every web dependency out of `src/color_engine/pyproject.toml` and out of the `engine-test` target.
- Use the libraries in the `structure.md` tables. Do not swap one for an equivalent.
