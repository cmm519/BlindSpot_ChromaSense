# Increment 13: Pipeline use cases

### Main rules

- Run the filters in exactly the orders that `architecture.md` lists. Only use cases decide the order.
- Core imports no FastAPI, SQLite, httpx, or provider code. Test with fakes for every port.
- Filters 4 to 7 must not run again on a profile change.

### Header

- **Increment:** 13
- **Capability:** Pipeline use cases
- **Status:** `CRITICAL`
- **Depends on:** `08-targeted-enhancement.md`, `09-pattern-overlays.md`, `12-layout-analysis.md`
- **Traces to:** Use cases and filter orders in `architecture.md`
- **SRS IDs:** **SRS-FR-014**, **SRS-FR-030**, **SRS-FR-008** (part; finished in increment 21), **SRS-FR-054** (part; finished in increment 24), **SRS-FR-068** (part; finished in increment 24), **SRS-FR-070** (part; finished in increment 16)

### Requirements

- **SRS-FR-014** (must): The system shall run confusion detection and enhancement again when the profile changes for a loaded image, without repeating local image analysis. (Section 3.4; local-first change)
- **SRS-FR-030** (must): The system shall verify enhancement by re-running confusion detection on the result. (FR-5.3)
- **SRS-FR-008** (must): The system shall automatically start the pipeline of decode, downscale, local image analysis, confusion detection, and enhancement after a successful upload and display the results. (FR-1.7; local-first change)
- **SRS-FR-054** (must): With no CVD selected, the system shall skip confusable pair flagging and enhancement, show the original image, and still provide the color list, local analysis results, color identification, and AI interpretation. (FR-1.7, FR-2.1; inferred severe low-vision requirement; local-first change)
- **SRS-FR-068** (must): The system shall show the local analysis results after upload without any request to the AI service, naming each item's source and flagging each local text and shape item as unverified until an AI read agrees with it. (FR-9.6; local-first change)
- **SRS-FR-070** (must): The server shall return the stored local analysis of an image, including its regions, shapes, text, legend, and image type, as JSON. (Local-first change)

### Capability

Application Core runs the upload and profile-change pipelines and exposes the stored local analysis.

### What may change

`chromasense/core/models.py`, `ports.py`, `errors.py`, `use_cases/process_upload.py`, `use_cases/get_analysis.py`, `use_cases/reanalyze_for_profile.py`, and `src/portal/tests/core/`.

### What must stay

Color Engine stays as earlier increments left it. If a use case needs a change to a filter's output, stop and report it.

### Implementation notes

**Orders**

- Upload with a CVD type: 1, 2, 3, 4, 5, 6, 7, 8, 9, then 3 and 8 on the enhanced pixels.
- Upload with no CVD: 1, 2, 3, 4, 5, 6, 7.
- Profile change: 8 with the stored palette, 9, then 3 and 8 on the enhanced pixels.

**Ports**: define all of `ImageStore`, `InterpretationCache`, `AiUsageLedger`, `VisionReader`, and `Clock` in `ports.py` as `typing.Protocol`, with the method names from `architecture.md`.

**`derived` contracts**

- `ImageStore.load(image_id)` returns `StoredImage(record, original: bytes, working: NDArray, analysis)`, or `None`.
- `ImageRecord(image_id, image_hash, width, height, created_at, expires_at)`. `image_id` is `uuid4().hex`. `image_hash` is `hashlib.sha256` of the uploaded bytes.
- `ImageAnalysis(palette, regions, shapes, text, legend, image_type, color_items, summary)`. `summary` is one sentence that states the image type and the count of colors, regions, shapes, and text items.
- `TextItem`, `ShapeItem`, `LegendEntry`, and `ColorItem` carry a stable `item_id`, `source` (`local`, `ai`, or `both`), and `verification`. Shape and color items carry the color name from `ColorNamer`.
- A local color item is `VERIFIED`, because it comes from the image's pixels (decision 3). Local text and shape items are `UNVERIFIED`.
- `ProcessUploadResponse(image_id, analysis, pairs, remaining_pair_count, enhancement_needed)`. `remaining_pair_count` is `None` with no CVD. `enhancement_needed` is false when no pairs are found.
- `core/errors.py`: `InvalidImage`, `ImageNotFound`, `InvalidCoordinates`, `NoEnhancementForProfile`, `AiUnavailable`, `AiRateLimited`, `AiSpendCapReached`, `NotInterpreted`.
- Constructor values: `max_megapixels=12.0`, `color_count=12`, `threshold` and retention from the caller. Server Main supplies them in increment 16.

**Tests**: put fakes in `src/portal/tests/core/fakes.py`. To prove the filter orders, patch the filter names in the use case modules with spies.

### Verification

Show each SRS observation in full:

- **SRS-FR-014**: Changing the type from deutan to tritan on a loaded image updates the confusable pairs and the enhanced image, and a test confirms that the local analysis filters do not run again.
- **SRS-FR-030**: The pipeline output for a test image includes a confusable pair count from a detection run on the enhanced image.

Show this part now. A later increment finishes the row:

- **SRS-FR-008**: `ProcessUpload` with a fake store and a CVD type returns the enhanced result and local analysis.
- **SRS-FR-054**: `ProcessUpload` with `CvdType.NONE` stops after filter 7 and returns no pairs and no enhanced image.
- **SRS-FR-068**: `ProcessUpload` makes no `VisionReader` call, and each local text and shape item has source `local` and state `UNVERIFIED`.
- **SRS-FR-070**: `GetAnalysis` returns the stored regions, shapes, text, legend, and image type, and raises `ImageNotFound` for an unknown ID.

Also confirm:

- A spy test shows that filters 4, 5, 6, and 7 are not called by `ReanalyzeForProfile`, and that its first filter 8 call receives the stored palette.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/core
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
```

### Risk

An architectural boundary and the first integration of the engine and core. It is the first place where 8 and 3 run twice with different inputs, so it is easy to reuse the wrong palette or pixels.

### How to recognize failure

Re-detection uses the stored palette instead of a new one from enhanced pixels, profile change runs a local analysis filter, or `lint-imports` reports an outward import.

### Isolation test

Replace each filter with a stub that records its name and input identity, and assert the sequence. Then replace the stubs with the real filters one at a time on a small fixture.

### Rollback

Return the tree to the state that **`prompts/12-layout-analysis.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/12-layout-analysis.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Run the filters in exactly the orders that `architecture.md` lists. Only use cases decide the order.
- Core imports no FastAPI, SQLite, httpx, or provider code. Test with fakes for every port.
- Filters 4 to 7 must not run again on a profile change.
