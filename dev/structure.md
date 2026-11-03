# Structure

You fill this file in stage 3 (see `README.md`). Do not add a part here.

## Required: Directory tree

The tree that the finished project must match. Include the files that the build tool needs.

Folders that already exist and are not listed here stay as they are. Numbered names follow the naming rule in `architecture.md`: only pipeline filters are numbered.

```
ChromaSense/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── AGENTS.md
├── Dockerfile
├── README.md
├── docker-compose.yml
├── docs/
│   ├── enhancement-evaluation.md
│   └── ocr-evaluation.md
└── src/
    ├── color_engine/
    │   ├── pyproject.toml
    │   ├── color_engine/
    │   │   ├── __init__.py
    │   │   ├── models.py
    │   │   ├── data/
    │   │   │   ├── machado_2009.json
    │   │   │   └── named_colors.csv
    │   │   ├── rules/
    │   │   │   ├── __init__.py
    │   │   │   ├── color_spaces.py
    │   │   │   ├── distance.py
    │   │   │   ├── naming.py
    │   │   │   ├── overlay.py
    │   │   │   └── simulation.py
    │   │   └── pipeline/
    │   │       ├── __init__.py
    │   │       ├── filter_1_decode/
    │   │       │   ├── __init__.py
    │   │       │   └── decode_1.py
    │   │       ├── filter_2_downscale/
    │   │       │   ├── __init__.py
    │   │       │   └── downscale_2.py
    │   │       ├── filter_3_palette/
    │   │       │   ├── __init__.py
    │   │       │   └── extract_palette_3.py
    │   │       ├── filter_4_regions/
    │   │       │   ├── __init__.py
    │   │       │   └── find_regions_4.py
    │   │       ├── filter_5_shapes/
    │   │       │   ├── __init__.py
    │   │       │   └── find_shapes_5.py
    │   │       ├── filter_6_text/
    │   │       │   ├── __init__.py
    │   │       │   └── read_text_6.py
    │   │       ├── filter_7_layout/
    │   │       │   ├── __init__.py
    │   │       │   └── analyze_layout_7.py
    │   │       ├── filter_8_confusion/
    │   │       │   ├── __init__.py
    │   │       │   └── detect_confusion_8.py
    │   │       └── filter_9_enhance/
    │   │           ├── __init__.py
    │   │           └── enhance_9.py
    │   └── tests/
    │       ├── data/
    │       ├── rules/
    │       └── pipeline/
    │           ├── test_filter_1_decode.py
    │           ├── test_filter_2_downscale.py
    │           ├── test_filter_3_palette.py
    │           ├── test_filter_4_regions.py
    │           ├── test_filter_5_shapes.py
    │           ├── test_filter_6_text.py
    │           ├── test_filter_7_layout.py
    │           ├── test_filter_8_confusion.py
    │           └── test_filter_9_enhance.py
    └── portal/
        ├── pyproject.toml
        ├── chromasense/
        │   ├── __init__.py
        │   ├── core/
        │   │   ├── __init__.py
        │   │   ├── models.py
        │   │   ├── ports.py
        │   │   ├── errors.py
        │   │   ├── policy/
        │   │   │   ├── __init__.py
        │   │   │   ├── ai_limits.py
        │   │   │   └── ai_verification.py
        │   │   └── use_cases/
        │   │       ├── __init__.py
        │   │       ├── answer_question.py
        │   │       ├── export_image.py
        │   │       ├── get_analysis.py
        │   │       ├── identify_color.py
        │   │       ├── interpret_image.py
        │   │       ├── process_upload.py
        │   │       ├── purge_expired.py
        │   │       ├── reanalyze_for_profile.py
        │   │       └── render_view.py
        │   ├── storage/
        │   │   ├── __init__.py
        │   │   ├── filesystem_image_store.py
        │   │   ├── schema.sql
        │   │   ├── sqlite_ai_usage_ledger.py
        │   │   └── sqlite_interpretation_cache.py
        │   ├── ai_gateway/
        │   │   ├── __init__.py
        │   │   ├── http_vision_reader.py
        │   │   └── read_schema.json
        │   ├── web_api/
        │   │   ├── __init__.py
        │   │   ├── app.py
        │   │   ├── schemas.py
        │   │   ├── session.py
        │   │   └── routers/
        │   │       ├── __init__.py
        │   │       ├── ai.py
        │   │       ├── images.py
        │   │       └── pages.py
        │   ├── web_ui/
        │   │   ├── templates/
        │   │   │   ├── base.html
        │   │   │   ├── home.html
        │   │   │   ├── intro.html
        │   │   │   ├── settings.html
        │   │   │   ├── simulator.html
        │   │   │   └── workspace.html
        │   │   └── static/
        │   │       ├── css/
        │   │       │   └── app.css
        │   │       └── js/
        │   │           ├── ai_panel.js
        │   │           ├── announce.js
        │   │           ├── color_point.js
        │   │           ├── profile.js
        │   │           ├── simulator.js
        │   │           ├── speech.js
        │   │           ├── upload.js
        │   │           └── workspace.js
        │   └── main/
        │       ├── __init__.py
        │       ├── __main__.py
        │       ├── settings.py
        │       └── wiring.py
        └── tests/
            ├── core/
            ├── storage/
            ├── ai_gateway/
            ├── web_api/
            └── browser/
```

## Required: Ownership

One row for each top-level folder or important file. The part must be a name from `architecture.md`.

| Path | Architecture part | What it holds |
| --- | --- | --- |
| `.devcontainer/` | Server Main | Team dev container |
| `.github/workflows/ci.yml` | Server Main | Required pull request checks: lint, dependency rules, tests, and coverage |
| `.env.example` | Server Main | Configuration names with no real values: provider URL, API key, model, retention period, confusion threshold, rate limits, and spend cap |
| `Dockerfile` | Server Main | Multi-stage build with `engine-test`, `dev`, and `runtime` targets. Each target installs the selected local text recognition engine |
| `docker-compose.yml` | Server Main | `portal` service on port 9090, `dev` service for checks, and the data volume |
| `README.md` | Server Main | Setup guide, and how to start the portal and reach it from another LAN device |
| `docs/enhancement-evaluation.md` | Color Engine | Recorded result of the enhancement method evaluation |
| `docs/ocr-evaluation.md` | Color Engine | Recorded comparison of Tesseract and RapidOCR on the labeled test set, and the selected engine |
| `src/color_engine/pyproject.toml` | Color Engine | Package definition with no web framework dependency, and coverage settings |
| `src/color_engine/color_engine/models.py` | Color Engine | `CvdType`, `CvdProfile`, `ColorInfo`, and numbered filter output classes |
| `src/color_engine/color_engine/data/` | Color Engine | Machado coefficients and the bundled named color dataset |
| `src/color_engine/color_engine/rules/` | Color Engine | Unnumbered color rules shared by filters and use cases |
| `src/color_engine/color_engine/pipeline/` | Color Engine | The nine numbered filters, one directory each |
| `src/color_engine/tests/` | Color Engine | Engine tests that run without the portal or web framework |
| `src/portal/pyproject.toml` | Server Main | Portal dependencies, the import-linter contracts, and Ruff settings |
| `src/portal/chromasense/core/ports.py` | Application Core | Port protocols that outer parts implement |
| `src/portal/chromasense/core/models.py` | Application Core | Plain core data classes |
| `src/portal/chromasense/core/policy/` | Application Core | AI verification, legend validation, rate limits, and spend cap |
| `src/portal/chromasense/core/use_cases/` | Application Core | One file per application action; `process_upload.py` sets the filter order |
| `src/portal/chromasense/storage/` | Storage Adapter | Filesystem image store, SQLite adapters, and schema |
| `src/portal/chromasense/ai_gateway/` | AI Gateway | Provider client and the structured output schema |
| `src/portal/chromasense/web_api/` | Web API | App factory, routers, Pydantic schemas, and the session cookie |
| `src/portal/chromasense/web_ui/` | Web UI | Jinja2 templates, CSS, and browser scripts |
| `src/portal/chromasense/main/` | Server Main | Settings, wiring, purge scheduling, and the entry point |
| `src/portal/tests/core/` | Application Core | Use case and policy tests with fakes for every port |
| `src/portal/tests/storage/` | Storage Adapter | Adapter tests on a temporary folder and SQLite file |
| `src/portal/tests/ai_gateway/` | AI Gateway | Gateway tests with a stubbed HTTP provider |
| `src/portal/tests/web_api/` | Web API | Endpoint tests with fake use cases |
| `src/portal/tests/browser/` | Web UI | Playwright and axe tests for pages, keyboard use, and zoom |

## Optional: Libraries and functions

Use these where a requirement or decision already depends on them. The agent must not swap them for an equivalent without a recorded decision.

### Color Engine

| Library | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| `Pillow` | `PIL.Image.open`, `PIL.ImageOps.exif_transpose`, `PIL.ImageCms.profileToProfile`, `PIL.ImageCms.createProfile("sRGB")` | `filter_1_decode` | SRS-FR-004, SRS-FR-005, SRS-FR-007 |
| `pillow-heif` | `pillow_heif.register_heif_opener` | `filter_1_decode` | SRS-FR-004 |
| `Pillow` | `Image.resize` with `Image.Resampling.LANCZOS` | `filter_2_downscale` | SRS-FR-006 |
| `scikit-learn` | `sklearn.cluster.KMeans` with a fixed `random_state`, on a pixel sample | `filter_3_palette` | SRS-FR-022, SRS-NFR-003 |
| `scikit-image` | `skimage.color.rgb2lab`, `skimage.color.lab2rgb` | `filter_3_palette`, `rules/naming.py` | SRS-FR-022, SRS-FR-036 |
| `scikit-image` | `skimage.color.deltaE_ciede2000` | `rules/distance.py` | SRS-FR-023, SRS-FR-036 |
| `numpy` | Array math, boolean masks, and matrix multiplication | Filters and `rules/` | SRS-FR-018, SRS-FR-025, SRS-FR-028, SRS-FR-065 |
| `opencv-python-headless` | `cv2.morphologyEx`, `cv2.connectedComponentsWithStats` | `filter_4_regions` | SRS-FR-065 |
| `opencv-python-headless` | `cv2.findContours`, `cv2.approxPolyDP`, `cv2.moments`, `cv2.HoughCircles` | `filter_5_shapes` | SRS-FR-056 |
| `opencv-python-headless` | `cv2.cvtColor`, `cv2.resize`, `cv2.adaptiveThreshold` for text recognition input | `filter_6_text` | SRS-FR-055 |
| `pytesseract` | `pytesseract.image_to_data` for text, boxes, and confidence. RapidOCR replaces it only if `docs/ocr-evaluation.md` records that result | `filter_6_text` | SRS-FR-055, SRS-NFR-042 |
| `opencv-python-headless` | `cv2.calcHist`, `cv2.Canny`, `cv2.HoughLines` | `filter_7_layout` | SRS-FR-066, SRS-FR-067 |
| `opencv-python-headless` | `cv2.line`, `cv2.circle`, `cv2.bitwise_and` | `rules/overlay.py` | SRS-FR-033 |
| Standard library | `colorsys.rgb_to_hls`, `csv`, `importlib.resources` | `rules/naming.py` | SRS-FR-036, SRS-FR-037 |

### Portal

| Library | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| Standard library | `dataclasses.dataclass`, `typing.Protocol`, `hashlib.sha256` | `core/` | SRS-FR-047 |
| Standard library | `sqlite3.connect` | `storage/` | SRS-FR-047, SRS-FR-048, SRS-NFR-010, SRS-NFR-011 |
| Standard library | `pathlib.Path` | `storage/filesystem_image_store.py` | SRS-FR-010 |
| `httpx` | `httpx.Client` | `ai_gateway/http_vision_reader.py` | SRS-FR-046 |
| `fastapi` | `FastAPI` with `lifespan`, `APIRouter`, `UploadFile`, `Depends`, `Response.set_cookie` | `web_api/`, `main/wiring.py` | SRS-FR-049, SRS-NFR-008 |
| `fastapi` | `fastapi.staticfiles.StaticFiles`, `fastapi.templating.Jinja2Templates` | `web_api/routers/pages.py` | SRS-NFR-005 |
| `python-multipart` | Required by `UploadFile` | `web_api/routers/images.py` | SRS-FR-001 |
| Standard library | `secrets.token_urlsafe` for the anonymous session ID | `web_api/session.py` | SRS-NFR-010 |
| `uvicorn` | `uvicorn.run(app, host="0.0.0.0", port=9090)` | `main/__main__.py` | SRS-NFR-033 |
| Standard library | `os.environ` | `main/settings.py` only | SRS-FR-010, SRS-NFR-007 |

### Web UI browser APIs

| API | Use these | In | SRS IDs |
| --- | --- | --- | --- |
| Web Speech | `window.speechSynthesis` `speak`, `pause`, `resume`, `cancel`, and `SpeechSynthesisUtterance.rate` | `speech.js` | SRS-FR-052, SRS-FR-063 |
| Web Storage | `localStorage` | `profile.js`, `speech.js` | SRS-FR-013, SRS-FR-063 |
| DOM | One shared `aria-live` region | `announce.js` | SRS-FR-039, SRS-FR-062 |
| DOM | `drop` and `paste` events, and `clipboardData` | `upload.js` | SRS-FR-002, SRS-FR-003 |
| CSS | `@media (forced-colors: active)` and `:focus-visible` | `app.css` | SRS-NFR-035, SRS-NFR-036 |

### Development and tests

| Library | Use these | SRS IDs |
| --- | --- | --- |
| `pytest`, `pytest-cov` | Test runs and the coverage report for `color_engine` | SRS-NFR-028 |
| `daltonlens` | `daltonlens.simulate.Simulator_Machado2009` and `Simulator_Brettel1997` as test-only references | SRS-NFR-023 |
| `ruff` | `ruff check` and `ruff format --check` | SRS-NFR-030 |
| `import-linter` | `lint-imports` | SRS-NFR-029 |
| `playwright`, `axe-playwright-python` | Browser, viewport, zoom, keyboard, and accessibility tests | SRS-NFR-012, SRS-NFR-013, SRS-NFR-015, SRS-NFR-016, SRS-NFR-017, SRS-NFR-036, SRS-NFR-037 |

## Required: Build and run

The commands to run after the last increment. The first command must succeed.

1. `docker compose build`
2. `docker compose up portal`, then open `http://<host-ip>:9090`
3. Extra checks:
   - `docker build --target engine-test .` (runs the Color Engine tests with no web framework installed)
   - `docker compose run --rm dev ruff check .`
   - `docker compose run --rm dev ruff format --check .`
   - `docker compose run --rm dev lint-imports --config src/portal/pyproject.toml`
   - `docker compose run --rm dev pytest src/color_engine/tests --cov=color_engine --cov-fail-under=70`
   - `docker compose run --rm dev pytest src/portal/tests`

## Required: If the build fails

Checks for this stack. The implementation agent uses this list before it invents a fix.

1. Docker: confirm that the Docker daemon is running, that the base image is Python 3.11, and that the `Dockerfile` target names match `docker-compose.yml`.
2. Install order: confirm that the image installs `src/color_engine` before `src/portal`, and that `src/color_engine/pyproject.toml` lists `data/*` as package data. `pillow-heif` must have a wheel for the image's platform.
3. Text recognition: confirm that the selected engine and its English language data are installed in every image target, and that `filter_6_text` needs no network access. OpenCV arrays in this project stay in RGB order, so pass explicit `COLOR_RGB2*` codes to `cv2.cvtColor`.
4. Imports: if `lint-imports` fails, fix the import that points outward. Do not edit the contract. Numbered directories must keep the `filter_<N>_<name>` form, because names such as `1-decode` cannot be imported.
5. Port: if the portal does not open, confirm that port 9090 is free, that the server binds `0.0.0.0`, and that the host firewall allows it.
6. Line endings: this repo is developed on Windows. If a file copied into the image fails with a bad interpreter or `\r` error, convert that file to LF.
7. AI: a missing provider setting must not stop the build or startup. Only AI features report that they are unavailable.
