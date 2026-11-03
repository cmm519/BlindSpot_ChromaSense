# Increment 5: CVD simulation

### Main rules

- Apply every simulation model in linear RGB. Linearize first, and re-encode to sRGB after.
- Use DaltonLens only in tests. `color_engine` code must not import it.
- Keep the signature `simulate(pixels, profile)`.

### Header

- **Increment:** 5
- **Capability:** CVD simulation
- **Status:** `CRITICAL`
- **Depends on:** `04-color-rules.md`
- **Traces to:** `simulate` in `architecture.md`
- **SRS IDs:** **SRS-FR-015**, **SRS-FR-016**, **SRS-FR-017**, **SRS-FR-018**, **SRS-NFR-023**

### Requirements

- **SRS-FR-015** (must): The system shall simulate protan and deutan deficiencies using the Machado (2009) model with variable severity. (FR-3.1)
- **SRS-FR-016** (must): The system shall simulate tritan deficiency using the Brettel (1997) model. (FR-3.2)
- **SRS-FR-017** (must): The system shall simulate achromatopsia using luminance based conversion. (FR-3.3)
- **SRS-FR-018** (must): The system shall perform simulation in linear RGB space. (FR-3.4)
- **SRS-NFR-023** (must): The Python simulation output shall match an independent reference implementation, such as the DaltonLens package, with a mean per pixel difference under 1 percent. (NFR-6.1)

### Capability

`simulate(pixels, profile)` returns the view of an image under each CVD type and severity.

### What may change

`rules/simulation.py`, `data/machado_2009.json`, and tests in `src/color_engine/tests/rules/`.

### What must stay

`rules/color_spaces.py` and `rules/distance.py` stay as increment 4 left them, unless a test here proves a defect.

### Implementation notes

- **Input and output**: `uint8` RGB arrays of shape `(H, W, 3)`.
- **Protan and deutan**: Machado (2009) matrices at severity 0.0 to 1.0 in 0.1 steps, stored in `machado_2009.json`. Interpolate linearly between the two nearest tables. Check the stored numbers against the published table.
- **Tritan**: Brettel (1997). For severity below 1, blend in linear RGB between the input and the full simulation (`derived`, because SRS-FR-016 gives no severity rule and SRS-FR-012 requires a severity for every type).
- **Achromatopsia**: Rec. 709 luminance computed in linear RGB and re-encoded to sRGB, written equally to R, G, and B. SRS-FR-017 requires equal channels, so this type ignores severity (`derived`).
- **`CvdType.NONE`**: return a copy of the input.
- **SRS-NFR-023 measure**: mean absolute per-channel difference divided by 255, below 0.01, against `daltonlens.simulate.Simulator_Machado2009` and `Simulator_Brettel1997`.
- **Fixtures**: small generated gradient and flat images, plus files in `src/color_engine/tests/data/`.

### Verification

Show each SRS observation in full:

- **SRS-FR-015**: Output for a test image at several severities matches the reference values from the published model within the SRS-NFR-023 tolerance.
- **SRS-FR-016**: Output for a test image matches the reference values from the published model within the SRS-NFR-023 tolerance.
- **SRS-FR-017**: Output pixels have equal R, G, and B values that equal the computed luminance of the input pixel.
- **SRS-FR-018**: A unit test shows the input is linearized before the model is applied and re-encoded to sRGB after it, and the result matches the reference values.
- **SRS-NFR-023**: A unit test comparing output with the reference implementation on test images reports a mean per pixel difference under 1 percent.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/rules/test_simulation.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

The first complex operation. A gamma mistake or wrong matrix gives plausible images that are wrong, and every later confusion and enhancement result depends on them.

### How to recognize failure

The reference comparison exceeds 1 percent, white or gray pixels change hue, or severity 0 differs from the input for protan or deutan.

### Isolation test

Run `simulate` on one pixel at a time, without any filter: pure white, mid gray, pure red, and pure green, at severities 0, 0.5, and 1. Compare with DaltonLens at each step: after linearization, after the matrix, and after re-encoding.

### Rollback

Return the tree to the state that **`prompts/04-color-rules.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/04-color-rules.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Apply every simulation model in linear RGB. Linearize first, and re-encode to sRGB after.
- Use DaltonLens only in tests. `color_engine` code must not import it.
- Keep the signature `simulate(pixels, profile)`.
