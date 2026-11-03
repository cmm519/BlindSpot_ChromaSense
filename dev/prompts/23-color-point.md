# Increment 23: Color identification point

### Main rules

- The browser sends coordinates only. The server returns the color.
- Use the one shared `aria-live` element for each result.
- Identify one point only. Do not add a brushed region average, because `srs.md` puts that out of scope.

### Header

- **Increment:** 23
- **Capability:** Color identification point
- **Status:** `Standard`
- **Depends on:** `21-image-workspace.md`
- **Traces to:** `color_point.js` in `structure.md`; workspace screen in `srs.md`
- **SRS IDs:** **SRS-FR-013**, **SRS-FR-035**, **SRS-FR-037**, **SRS-FR-038**, **SRS-FR-039**, **SRS-FR-061**, **SRS-FR-069**

### Requirements

- **SRS-FR-013** (must): The system shall store the active profile in browser storage and apply it to all features. (FR-2.3)
- **SRS-FR-035** (must): The system shall identify the color of a clicked or tapped point. (FR-7.1)
- **SRS-FR-037** (must): The system shall display HEX, RGB, and HSL values and the basic color family. (FR-7.4)
- **SRS-FR-038** (should): The system shall show how the identified color appears under the active profile. (FR-7.5)
- **SRS-FR-039** (must): The system shall announce identification results to screen readers using an ARIA live region. (FR-7.6)
- **SRS-FR-061** (must): The system shall allow the user to move an identification point across the image using the keyboard, and shall announce the color at the point after each move. (FR-7.1, FR-7.6; inferred severe low-vision requirement)
- **SRS-FR-069** (should): The system shall allow the user to move the identification point to the next or previous detected region using the keyboard, and shall announce the region's color, size, and location. (FR-7.1, FR-7.6; local-first change)

### Capability

A user can identify a color by click, tap, arrow keys, or next and previous region.

### What may change

`static/js/color_point.js`, `web_ui/templates/workspace.html`, `static/css/app.css`, and `src/portal/tests/browser/`.

### What must stay

`/color` and `/analysis` stay as earlier increments left them.

### Implementation notes

- Scale pointer coordinates from the displayed image to working copy coordinates using the image dimensions from the analysis response.
- **Keyboard** (`derived`): a focusable image wrapper with a name and instructions. Arrow keys move the point by 1 percent of the image's width or height, at least 1 pixel. `n` and `p` move to the next and previous region. Do not trap Tab.
- Show the point with a mark that has a contrasting outline, and state its position in text.
- **Result**: name, HEX, RGB, HSL, family, and a simulated swatch with a text label. With no CVD, omit the simulated swatch.
- **Region announcement**: region number and total, color name, size, and location as percent from the left and from the top (`derived`).
- Region data comes from `GET analysis`. The color comes from `GET color` at the region's center.

### Verification

Show each SRS observation in full:

- **SRS-FR-013**: After a page reload, the profile is still selected, and simulation, enhancement, and color identification requests all carry it.
- **SRS-FR-035**: Clicking and tapping a known color region each returns that region's color.
- **SRS-FR-037**: Clicking a known color shows the correct HEX, RGB, and HSL values and color family.
- **SRS-FR-038**: The color result shows a simulated swatch that changes when the profile changes.
- **SRS-FR-039**: After a click, the color name appears in an element with an `aria-live` attribute.
- **SRS-FR-061**: Using only the arrow keys, a tester moves the point onto a known color region and the color name appears in the `aria-live` element.
- **SRS-FR-069**: Using only the keyboard, a tester moves through each region of a test image, and each region's details appear in the `aria-live` element.

Also confirm:

- A Playwright run uses a touch-enabled context for the tap check, and a keyboard-only run for the arrow and region checks.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- The browser sends coordinates only. The server returns the color.
- Use the one shared `aria-live` element for each result.
- Identify one point only. Do not add a brushed region average, because `srs.md` puts that out of scope.
