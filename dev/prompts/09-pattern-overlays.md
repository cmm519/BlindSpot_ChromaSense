# Increment 9: Pattern overlays

### Main rules

- Keep the signature `apply_overlay(pixels, mask, groups)`.
- Add no setting for overlay style, because `srs.md` puts that out of scope.
- OpenCV arrays stay in RGB order in this project.

### Header

- **Increment:** 9
- **Capability:** Pattern overlays
- **Status:** `Standard`
- **Depends on:** `07-confusion-detection.md`
- **Traces to:** `apply_overlay` in `architecture.md`
- **SRS IDs:** **SRS-FR-033**

### Requirements

- **SRS-FR-033** (should): The system shall use the confusion mask to apply a distinct pattern (hatching, dots, crosshatch, or outline) to each confusable color group. (FR-6.3)

### Capability

The engine can draw a distinct, labeled pattern on each confusable color group, inside the mask only.

### What may change

`rules/overlay.py` and `src/color_engine/tests/rules/test_overlay.py`.

### What must stay

All filters stay as earlier increments left them.

### Implementation notes

- Use `cv2.line`, `cv2.circle`, and `cv2.bitwise_and`, and return a new array.
- Assign patterns by group order: hatching, dots, crosshatch, outline. Expose the label for each group, because later increments show it as text.
- **`derived`**: SRS-FR-033 lists four patterns but does not limit the number of groups. After four groups, reuse the list at double spacing with the label `<pattern>, wide`.
- **`derived`**: draw black or white, whichever has the higher contrast with the group's color.

### Verification

Show each SRS observation in full:

- **SRS-FR-033**: In a test image with two confusable groups, each group has a different pattern, and pixels outside the mask are unchanged.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/rules/test_overlay.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Keep the signature `apply_overlay(pixels, mask, groups)`.
- Add no setting for overlay style, because `srs.md` puts that out of scope.
- OpenCV arrays stay in RGB order in this project.
