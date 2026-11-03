# Increment 7: Palette and confusion detection

### Main rules

- Keep the names `extract_palette_3(pixels, color_count)` -> `Palette3` and `detect_confusion_8(pixels, palette, profile, threshold)` -> `ConfusionResult8`.
- Filter 8 takes the threshold as an argument. Color Engine reads no configuration.
- A pair is flagged only when the simulated distance is below the threshold and the original distance exceeds it.

### Header

- **Increment:** 7
- **Capability:** Palette and confusion detection
- **Status:** `CRITICAL`
- **Depends on:** `05-cvd-simulation.md`, `06-image-intake.md`
- **Traces to:** Filters 3 and 8 in `architecture.md`
- **SRS IDs:** **SRS-FR-022**, **SRS-FR-023**, **SRS-FR-024**, **SRS-FR-025**

### Requirements

- **SRS-FR-022** (must): The system shall extract dominant colors using k-means clustering in CIELAB space. (FR-4.1)
- **SRS-FR-023** (must): The system shall compute CIEDE2000 distances between dominant colors before and after simulation. (FR-4.2)
- **SRS-FR-024** (must): The system shall flag a pair as confusable when the simulated distance falls below a configurable threshold while the original distance exceeds it. (FR-4.3)
- **SRS-FR-025** (must): The system shall produce a mask of pixels belonging to confusable colors. (FR-4.4)

### Capability

For a given profile, the engine extracts dominant colors, flags confusable pairs, and produces a mask of the pixels that belong to them.

### What may change

`pipeline/filter_3_palette/extract_palette_3.py`, `pipeline/filter_8_confusion/detect_confusion_8.py`, output classes in `models.py`, their two test files, and `tests/data/`.

### What must stay

`simulate` and `ciede2000` stay as earlier increments left them. Filter 8 calls those rules and calls no other filter.

### Implementation notes

- **`derived`**: `Palette3(entries)`, with `PaletteEntry(id: int, rgb, lab, share)`. IDs run from 1 in order of descending pixel share.
- **`derived`**: `ConfusionResult8(pairs, groups, mask, color_index)`, with `ConfusablePair(a_id, b_id, original_distance, simulated_distance)` and `ConfusionGroup(group_id, palette_ids)`. A group is a connected set of palette IDs linked by flagged pairs.
- **Filter 3**: `skimage.color.rgb2lab`, then `sklearn.cluster.KMeans` with a fixed `random_state`, on a sample of at most 50,000 pixels (`derived`). Merge clusters closer than CIEDE2000 2.3 (`derived`), because a flat graphic has fewer colors than `color_count`.
- **Filter 8**: simulate the palette colors as a small array and measure both distances with `ciede2000`. Assign each pixel to its nearest palette color for `color_index`. Use a lookup table of 64 bins per RGB channel for this (`derived`, because SRS-NFR-003 allows 500 milliseconds).
- **Test colors**: a known flat graphic, including a red and green pair under full deutan, and a pair distinct under both views.

### Verification

Show each SRS observation in full:

- **SRS-FR-022**: For a flat graphic with known colors, the extracted palette contains a color within a small CIEDE2000 distance of each known color.
- **SRS-FR-023**: The distance function reproduces the published Sharma (2005) test pairs, and each detected pair reports both distances.
- **SRS-FR-024**: A red and green test pair under full deutan is flagged, a pair distinct under both views is not flagged, and changing the threshold changes the result.
- **SRS-FR-025**: For a flat graphic, the mask covers the pixels of the flagged colors and no pixels of the other colors.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_3_palette.py src/color_engine/tests/pipeline/test_filter_8_confusion.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

An architectural meeting point: the first filter that combines simulation, distance, and a palette. K-means is also random and over-segments flat images, which produces false pairs from near-duplicate clusters.

### How to recognize failure

Repeated runs give different palettes, a flat three-color graphic yields more than three entries, or pairs appear between two shades of one color.

### Isolation test

Run filter 3 alone on a three-color fixture and assert three entries. Run filter 8 alone with a hand-written `Palette3`, so palette errors cannot affect it. Then run them together.

### Rollback

Return the tree to the state that **`prompts/06-image-intake.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/06-image-intake.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Keep the names `extract_palette_3(pixels, color_count)` -> `Palette3` and `detect_confusion_8(pixels, palette, profile, threshold)` -> `ConfusionResult8`.
- Filter 8 takes the threshold as an argument. Color Engine reads no configuration.
- A pair is flagged only when the simulated distance is below the threshold and the original distance exceeds it.
