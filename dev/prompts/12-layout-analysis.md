# Increment 12: Image type and local legend

### Main rules

- Keep the name `analyze_layout_7(pixels, palette, regions, text)` -> `LayoutResult7`.
- Use measured features and written rules only. Add no trained classifier.
- Do not place legend labels on chart regions, because `srs.md` puts that out of scope.

### Header

- **Increment:** 12
- **Capability:** Image type and local legend
- **Status:** `Standard`
- **Depends on:** `10-regions-and-shapes.md`, `11-local-text-recognition.md`
- **Traces to:** Filter 7 in `architecture.md`
- **SRS IDs:** **SRS-FR-066** (part; finished in increment 21), **SRS-FR-067** (part; finished in increment 17)

### Requirements

- **SRS-FR-066** (should): The system shall classify each image locally as a chart, map, flat graphic, or photograph using measured image features, and shall tell the user that results for a photograph are best effort. (FR-9.1; local-first change)
- **SRS-FR-067** (should): The system shall detect a legend of color swatches and nearby text locally, map each entry to a palette ID, and flag an AI legend entry as unverified when a local entry for the same palette ID has different text. (FR-9.2, FR-9.5; local-first change)

### Capability

The engine classifies the image type and finds a legend of swatches and nearby text, locally.

### What may change

`pipeline/filter_7_layout/analyze_layout_7.py`, `LayoutResult7` in `models.py`, `tests/pipeline/test_filter_7_layout.py`, and `tests/data/labeled/`.

### What must stay

Filters 4, 5, and 6 stay as earlier increments left them.

### Implementation notes

- **`derived`**: `LayoutResult7(image_type, legend)`, with `ImageType` values `CHART`, `MAP`, `FLAT_GRAPHIC`, and `PHOTOGRAPH`, and `LegendEntry7(palette_id, text, x, y, width, height)`.
- **Features**: use `cv2.calcHist`, `cv2.Canny`, and `cv2.HoughLines`, with palette coverage, region count, and text count. Record the thresholds as named constants in the filter.
- **Legend rule** (`derived`): at least two small regions of similar size, aligned in a row or column, each with a `TextPiece` next to it on the same side. Map each entry to the region's palette ID.
- With no legend, return an empty list. Do not raise an error.

### Verification

Show this part now. A later increment finishes the row:

- **SRS-FR-066**: Each image in a labeled sample set receives one of chart, map, flat graphic, or photograph.
- **SRS-FR-067**: For a chart with a known legend, the local entries match it, with no AI provider configured.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_7_layout.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Keep the name `analyze_layout_7(pixels, palette, regions, text)` -> `LayoutResult7`.
- Use measured features and written rules only. Add no trained classifier.
- Do not place legend labels on chart regions, because `srs.md` puts that out of scope.
