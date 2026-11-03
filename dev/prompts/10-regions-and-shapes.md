# Increment 10: Regions and shapes

### Main rules

- Keep the names `find_regions_4(pixels, palette)` -> `RegionMap4` and `find_shapes_5(regions)` -> `ShapeSet5`.
- Use classical OpenCV operations only. Add no machine learning segmentation.
- Filter 5 receives only `RegionMap4`, so `RegionMap4` must carry what filter 5 needs.

### Header

- **Increment:** 10
- **Capability:** Regions and shapes
- **Status:** `Standard`
- **Depends on:** `07-confusion-detection.md`
- **Traces to:** Filters 4 and 5 in `architecture.md`
- **SRS IDs:** **SRS-FR-065**, **SRS-FR-056** (part; finished in increment 21)

### Requirements

- **SRS-FR-065** (must): The system shall identify the connected regions of each palette color and record each region's location, size, and center. (FR-6.2; local-first change)
- **SRS-FR-056** (must): After a successful upload, the system shall detect each distinct shape in the image locally, without the AI service, and list it as a separate item, with its kind, its location, and the palette ID of its color. (FR-6.2; severe low-vision requirement; local-first change)

### Capability

The engine lists the connected regions of each palette color, and the shapes among them.

### What may change

`pipeline/filter_4_regions/find_regions_4.py`, `pipeline/filter_5_shapes/find_shapes_5.py`, output classes in `models.py`, and their two test files.

### What must stay

Filters 1, 2, 3, 8, and 9 stay as earlier increments left them.

### Implementation notes

- **`derived`**: `RegionMap4(regions, labels)`, with `Region(id, palette_id, x, y, width, height, area, center_x, center_y)`. `labels` is an integer array of region IDs.
- **Filter 4**: assign pixels to the nearest palette color, clean each color's mask with `cv2.morphologyEx`, and use `cv2.connectedComponentsWithStats`. Drop regions under 16 pixels (`derived`).
- **`derived`**: `ShapeSet5(shapes)`, with `Shape(id, kind, palette_id, x, y, width, height, center_x, center_y)`. Kinds are `circle`, `rectangle`, `triangle`, and `other`.
- **Filter 5**: use `cv2.findContours`, `cv2.approxPolyDP`, `cv2.moments`, and `cv2.HoughCircles`.
- **`derived`**: a region that touches all four image edges is the background and is not a shape.

### Verification

Show each SRS observation in full:

- **SRS-FR-065**: For a flat graphic with known regions, the system reports the correct number of regions for each color, with locations and sizes that match the known values within a small tolerance.

Show this part now. A later increment finishes the row:

- **SRS-FR-056**: `find_shapes_5` returns a known circle, rectangle, and triangle with kind, location, and palette ID.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_4_regions.py src/color_engine/tests/pipeline/test_filter_5_shapes.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Keep the names `find_regions_4(pixels, palette)` -> `RegionMap4` and `find_shapes_5(regions)` -> `ShapeSet5`.
- Use classical OpenCV operations only. Add no machine learning segmentation.
- Filter 5 receives only `RegionMap4`, so `RegionMap4` must carry what filter 5 needs.
