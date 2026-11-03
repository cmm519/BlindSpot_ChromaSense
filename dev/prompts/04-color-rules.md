# Increment 4: Color spaces, distance, and naming

### Main rules

- Keep the signatures from `architecture.md`: `srgb_to_linear`, `linear_to_srgb`, `ciede2000`, and `ColorNamer.describe`.
- Read the dataset with `importlib.resources`. Make no network call and read no environment variable.
- Add only rules. Add no pipeline filter.

### Header

- **Increment:** 4
- **Capability:** Color spaces, distance, and naming
- **Status:** `Standard`
- **Depends on:** `03-quality-gates.md`
- **Traces to:** Color rules in `architecture.md`
- **SRS IDs:** **SRS-FR-036**, **SRS-FR-023** (part; finished in increment 7), **SRS-FR-037** (part; finished in increment 23)

### Requirements

- **SRS-FR-036** (must): The system shall return the nearest color name using CIEDE2000 against a bundled named color dataset. (FR-7.3)
- **SRS-FR-023** (must): The system shall compute CIEDE2000 distances between dominant colors before and after simulation. (FR-4.2)
- **SRS-FR-037** (must): The system shall display HEX, RGB, and HSL values and the basic color family. (FR-7.4)

### Capability

Color Engine can convert between sRGB and linear RGB, compute CIEDE2000, and name any RGB color from a bundled dataset.

### What may change

`color_engine/models.py`, `rules/color_spaces.py`, `rules/distance.py`, `rules/naming.py`, `data/named_colors.csv`, and tests in `src/color_engine/tests/rules/`.

### What must stay

Dependency contracts and image targets from earlier increments stay as they are.

### Implementation notes

- **`models.py`**: `CvdType`, `CvdProfile`, and `ColorInfo` exactly as `architecture.md` names them.
- **`distance.py`**: wrap `skimage.color.deltaE_ciede2000`.
- **`naming.py`**: use `skimage.color.rgb2lab`, `colorsys.rgb_to_hls`, `csv`, and `importlib.resources`. Cache the parsed dataset. The nearest color is the smallest CIEDE2000 distance.
- **`named_colors.csv`** (`derived`, because the user files do not name a dataset): the CSS Color Module Level 4 named colors, with columns `name,hex,l,a,b,family`. Merge duplicate values such as `aqua` and `cyan` into one row.
- **Families** (`derived`): red, orange, yellow, green, blue, purple, pink, brown, black, white, gray.
- **HSL format** (`derived`): degrees for hue, percent for saturation and lightness, rounded to whole numbers.

### Verification

Show each SRS observation in full:

- **SRS-FR-036**: Querying the exact value of a dataset color returns that color's name, with no network access.

Show this part now. A later increment finishes the row:

- **SRS-FR-023**: `ciede2000` reproduces the published Sharma (2005) test pairs.
- **SRS-FR-037**: `ColorNamer.describe` returns the correct HEX, RGB, HSL, and family for a known color.

Also confirm:

- The test for SRS-FR-036 runs in the `engine-test` build, which uses no provider and no network.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/rules
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Keep the signatures from `architecture.md`: `srgb_to_linear`, `linear_to_srgb`, `ciede2000`, and `ColorNamer.describe`.
- Read the dataset with `importlib.resources`. Make no network call and read no environment variable.
- Add only rules. Add no pipeline filter.
