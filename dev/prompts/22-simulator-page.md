# Increment 22: Simulator page

### Main rules

- Every simulation is computed on the server through `render`.
- Keep focus on the control that the user is moving.
- The page does not change the stored profile.

### Header

- **Increment:** 22
- **Capability:** Simulator page
- **Status:** `Standard`
- **Depends on:** `21-image-workspace.md`
- **Traces to:** Simulator screen in `srs.md`; `simulator.js` in `structure.md`
- **SRS IDs:** **SRS-FR-011**, **SRS-FR-019**, **SRS-FR-020**, **SRS-FR-021**, **SRS-FR-026**

### Requirements

- **SRS-FR-011** (must): The system shall allow the user to select a CVD type (protan, deutan, tritan, or achromatopsia) or no CVD. (FR-2.1; inferred severe low-vision requirement)
- **SRS-FR-019** (must): The system shall display original and simulated images side by side or with a swipe slider. (FR-3.5)
- **SRS-FR-020** (should): The system shall update a preview sized simulated image shortly after the user stops moving the severity slider. (FR-3.6)
- **SRS-FR-021** (must): The simulator page shall allow the user to select a CVD type and severity and display the simulated view of the loaded image. (Section 3.1, UC-6)
- **SRS-FR-026** (should): The system shall display the list of confusable pairs with swatches, names, and patterns. (FR-4.5, UC-6)

### Capability

A user can view a loaded image beside its simulation under any CVD type and severity.

### What may change

`web_ui/templates/simulator.html`, `static/js/simulator.js`, `static/css/app.css`, and `src/portal/tests/browser/`.

### What must stay

The workspace and API stay as earlier increments left them.

### Implementation notes

- **Route**: `/simulator?image_id=<id>`. With no image ID, the page says that an image must be uploaded first, with a link to the home page (`derived`, because `srs.md` links Home to the simulator and SRS-FR-021 opens it from a loaded image).
- **Layout**: original and simulated images side by side, stacking on narrow screens.
- **Selection** (`derived`): the type selector offers the four types. It starts at the active profile, or protan with no CVD. A change here is not saved as the profile.
- **Slider**: request a preview 250 milliseconds after movement stops (`derived`). Announce the updated view.
- **Pairs**: call `POST analyze` with the simulator's selection, and list the pairs with swatches, names, and patterns. Use the same list markup as the workspace.
- **Text alternative**: name the view, the type, and the severity.

### Verification

Show each SRS observation in full:

- **SRS-FR-011**: The settings page offers all four types and no CVD, and a selected type is used in the next simulation.
- **SRS-FR-019**: The simulator page shows both images side by side or with a slider that reveals each one.
- **SRS-FR-020**: Releasing the slider updates the preview with no further user action and no page reload.
- **SRS-FR-021**: Opening the simulator from a loaded image and changing the type and severity changes the simulated view.
- **SRS-FR-026**: The image workspace and the simulator page each list a test image's pairs, with swatches, names, and patterns.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Every simulation is computed on the server through `render`.
- Keep focus on the control that the user is moving.
- The page does not change the stored profile.
