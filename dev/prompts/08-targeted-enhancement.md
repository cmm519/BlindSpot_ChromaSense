# Increment 8: Targeted enhancement

### Main rules

- Ship exactly one enhancement method, selected by the recorded evaluation. Do not commit the rejected methods.
- Change no pixel outside the mask.
- Keep the name `enhance_9(pixels, confusion, strength)` -> `EnhancedImage9`.

### Header

- **Increment:** 8
- **Capability:** Targeted enhancement
- **Status:** `CRITICAL`
- **Depends on:** `07-confusion-detection.md`
- **Traces to:** Filter 9 and `docs/enhancement-evaluation.md` in `architecture.md` and `structure.md`
- **SRS IDs:** **SRS-FR-028**, **SRS-FR-029**, **SRS-FR-031** (part; finished in increment 21), **SRS-NFR-024** (part; finished in increment 27)

### Requirements

- **SRS-FR-028** (must): The system shall modify only pixels within the confusion mask. (FR-5.1)
- **SRS-FR-029** (must): The system shall support one enhancement method, selected by technical evaluation from targeted daltonization, lightness separation, and hue rotation. (FR-5.2)
- **SRS-FR-031** (should): The system shall allow the user to adjust enhancement strength. (FR-5.4)
- **SRS-NFR-024** (should): Targeted enhancement shall reduce confusable pairs by at least 80 percent on the flat graphics test dataset. (NFR-6.2)

### Capability

The engine recolors only the confusable pixels with the single method that the evaluation selected.

### What may change

`pipeline/filter_9_enhance/enhance_9.py`, `EnhancedImage9` in `models.py`, `tests/pipeline/test_filter_9_enhance.py`, `tests/data/flat_graphics/`, and `docs/enhancement-evaluation.md`.

### What must stay

Filter 8 output stays as increment 7 left it. Add no setting that selects a method, because `srs.md` puts that out of scope.

### Implementation notes

- **Evaluation**: compare targeted daltonization, lightness separation, and hue rotation on the flat graphics dataset, in temporary code outside the repository.
- **Selection rule** (`derived`): the highest percent reduction in confusable pairs. Break a tie with the smallest mean CIEDE2000 change inside the mask.
- **`docs/enhancement-evaluation.md`**: the dataset, each method's before and after pair counts, and the selected method.
- **`tests/data/flat_graphics/`**: at least 20 generated flat graphics with known colors and a `labels.json`. Generate them with Pillow.
- **`derived`**: `EnhancedImage9(pixels, method)`. `strength` is 0 to 1. Strength 0 returns the input unchanged, and the default is 1.
- Do not add the re-detection step here. The use case runs it in increment 13.

### Verification

Show each SRS observation in full:

- **SRS-FR-028**: A pixel comparison of original and enhanced images finds no changed pixels outside the mask.
- **SRS-FR-029**: The evaluation result is recorded, and the system offers exactly that one method.

Show this part now. A later increment finishes the row:

- **SRS-FR-031**: `enhance_9` output changes with `strength`, and the change stays inside the mask.
- **SRS-NFR-024**: The evaluation records the before and after pair counts for the selected method on the flat graphics test dataset.

Also confirm:

- `docs/enhancement-evaluation.md` exists and names one method, and `enhance_9.py` contains only that method.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_9_enhance.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

Conflicting requirements. Stronger recoloring separates pairs better, but it can create a new confusion with a color outside the group, and nothing may change outside the mask.

### How to recognize failure

The re-detection count rises after enhancement, pixel comparison finds changes outside the mask, or strength 0 changes the image.

### Isolation test

Run `enhance_9` on a hand-built `ConfusionResult8` with a known mask, without filters 3 or 8. Assert a zero difference outside the mask at strengths 0, 0.5, and 1. Then run filters 3 and 8 on the output by hand to count pairs.

### Rollback

Return the tree to the state that **`prompts/07-confusion-detection.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/07-confusion-detection.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Ship exactly one enhancement method, selected by the recorded evaluation. Do not commit the rejected methods.
- Change no pixel outside the mask.
- Keep the name `enhance_9(pixels, confusion, strength)` -> `EnhancedImage9`.
