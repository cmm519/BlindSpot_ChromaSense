# Increment 15: Render, identify, and export

### Main rules

- Export runs filters 8 and 9 on the original pixels with the stored palette.
- A color's name and values come only from `ColorNamer`.
- Do not store rendered views. Compute them from the stored image and the request's profile.

### Header

- **Increment:** 15
- **Capability:** Render, identify, and export
- **Status:** `Standard`
- **Depends on:** `14-image-storage-and-purge.md`
- **Traces to:** `RenderView`, `IdentifyColor`, and `ExportImage` in `architecture.md`
- **SRS IDs:** **SRS-FR-041**, **SRS-FR-035** (part; finished in increment 23), **SRS-FR-037** (part; finished in increment 23), **SRS-FR-038** (part; finished in increment 23), **SRS-FR-040** (part; finished in increment 21)

### Requirements

- **SRS-FR-041** (should): The system shall export at the original image resolution. (FR-8.3)
- **SRS-FR-035** (must): The system shall identify the color of a clicked or tapped point. (FR-7.1)
- **SRS-FR-037** (must): The system shall display HEX, RGB, and HSL values and the basic color family. (FR-7.4)
- **SRS-FR-038** (should): The system shall show how the identified color appears under the active profile. (FR-7.5)
- **SRS-FR-040** (must): The system shall allow the user to download the enhanced image through the browser. (FR-8.1)

### Capability

Application Core returns any view of a stored image, the color at a point, and a full-resolution export.

### What may change

`core/use_cases/render_view.py`, `identify_color.py`, `export_image.py`, and tests in `src/portal/tests/core/`.

### What must stay

Earlier use cases, ports, and the store stay as earlier increments left them.

### Implementation notes

- **`RenderView`** (`derived` request): `image_id`, `view` (`original`, `simulated`, `enhanced`, or `overlay`), `profile`, `strength`. It returns PNG bytes of at most 2 megapixels, using `downscale_2`.
- `simulated` uses `simulate`. `enhanced` runs 8 and 9 on the working copy with the stored palette. `overlay` applies `apply_overlay` to the enhanced pixels.
- With no CVD, `enhanced` and `overlay` raise `NoEnhancementForProfile` (`derived`, from SRS-FR-054).
- **`IdentifyColor`** (`derived` request): `image_id`, `x`, `y`, `profile`, in working copy coordinates. Out-of-bounds coordinates raise `InvalidCoordinates`.
- **`ExportImage`** (`derived` request): `image_id`, `profile`, `strength`. Decode the original with `decode_1`. With no CVD it raises `NoEnhancementForProfile`. Overlays are not part of the export, because SRS-FR-040 names the enhanced image.

### Verification

Show each SRS observation in full:

- **SRS-FR-041**: The export of a 20 megapixel upload has the same pixel dimensions as the original.

Show this part now. A later increment finishes the row:

- **SRS-FR-035**: `IdentifyColor` returns a known region's color for a coordinate inside it.
- **SRS-FR-037**: `IdentifyColor` returns HEX, RGB, HSL, name, and family from `ColorNamer`.
- **SRS-FR-038**: `IdentifyColor` returns a simulated RGB value that changes with the profile, and none for no CVD.
- **SRS-FR-040**: `ExportImage` returns PNG bytes that decode to the enhanced image.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/core
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Export runs filters 8 and 9 on the original pixels with the stored palette.
- A color's name and values come only from `ColorNamer`.
- Do not store rendered views. Compute them from the stored image and the request's profile.
