# Increment 11: Local text recognition

### Main rules

- Ship exactly one text recognition engine. Use Tesseract unless the recorded evaluation selects RapidOCR.
- The filter must work with no network access and must read no environment variable.
- Keep the name `read_text_6(pixels)` -> `TextSet6`.

### Header

- **Increment:** 11
- **Capability:** Local text recognition
- **Status:** `CRITICAL`
- **Depends on:** `06-image-intake.md`
- **Traces to:** Filter 6 and `docs/ocr-evaluation.md` in `architecture.md` and `structure.md`
- **SRS IDs:** **SRS-FR-055** (part; finished in increment 21), **SRS-NFR-042** (part; finished in increment 28)

### Requirements

- **SRS-FR-055** (must): After a successful upload, the system shall recognize the text in the image locally, without the AI service, and list each piece of text as a separate item, with its location in the image, in reading order. (FR-9.2; severe low-vision requirement; local-first change)
- **SRS-NFR-042** (should): Local text and shape items shall each be at least 80 percent correct on the labeled test set of charts, maps, and flat graphics. (Local-first change)

### Capability

The engine reads English text from an image locally, with locations in reading order.

### What may change

`pipeline/filter_6_text/read_text_6.py`, `TextSet6` in `models.py`, `tests/pipeline/test_filter_6_text.py`, `tests/data/`, and `docs/ocr-evaluation.md`. Change the `Dockerfile` and `pyproject.toml` only if the evaluation selects RapidOCR.

### What must stay

The other filters stay as earlier increments left them. Each image target keeps installing the one selected engine.

### Implementation notes

- **Evaluation**: compare Tesseract and RapidOCR on `tests/data/labeled/`, using temporary code and a temporary install of RapidOCR outside the repository.
- **`tests/data/labeled/`**: generated charts, maps, and flat graphics with known text, and a `labels.json`. Add any labeled files that the team supplies. Increment 28 needs the real labeled set.
- **Selection rule** (`derived`): keep Tesseract unless RapidOCR is at least 5 points more correct and still fits SRS-NFR-041.
- **`derived`**: `TextSet6(items)`, with `TextPiece(text, x, y, width, height, confidence)`. One piece is one line of text, so that AI text items can be matched line by line.
- **With Tesseract**: prepare input with `cv2.cvtColor` (`COLOR_RGB2GRAY`), `cv2.resize`, and `cv2.adaptiveThreshold`, and call `pytesseract.image_to_data`. Group words by block, paragraph, and line. Drop words under confidence 60 (`derived`).
- **Reading order**: block, paragraph, then line order from the engine.
- If the engine binary is missing, raise an error. Do not return an empty result.

### Verification

Show this part now. A later increment finishes the row:

- **SRS-FR-055**: `read_text_6` lists each piece of text in a known flat graphic, with its location, in reading order, with no network access.
- **SRS-NFR-042**: `docs/ocr-evaluation.md` records the local text correctness of both engines on the available labeled set.

Also confirm:

- `docs/ocr-evaluation.md` exists and names one engine.
- The filter test passes when the container has no network: `docker run --rm --network none` with the `dev` image.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_6_text.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

The first external binary in the pipeline. It must exist in all three image targets and run offline, and small or colored text can fail silently with an empty result.

### How to recognize failure

`TesseractNotFoundError` in one target, an empty result on clear text, or a timing over about 10 seconds on 12 megapixels.

### Isolation test

Run `tesseract --version` and `tesseract --list-langs` in each image target. Call `read_text_6` on one black-on-white fixture before any colored fixture, and compare the raw `image_to_data` output with the grouped items.

### Rollback

Return the tree to the state that **`prompts/10-regions-and-shapes.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/10-regions-and-shapes.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Ship exactly one text recognition engine. Use Tesseract unless the recorded evaluation selects RapidOCR.
- The filter must work with no network access and must read no environment variable.
- Keep the name `read_text_6(pixels)` -> `TextSet6`.
