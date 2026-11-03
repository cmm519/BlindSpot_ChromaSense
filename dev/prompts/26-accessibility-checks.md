# Increment 26: Automated accessibility checks

### Main rules

- Fix the page. Do not disable an axe rule or lower a check.
- Add no feature here. This increment only corrects Web UI defects.
- All pages includes home, workspace, simulator, settings, and intro.

### Header

- **Increment:** 26
- **Capability:** Automated accessibility checks
- **Status:** `Standard`
- **Depends on:** `22-simulator-page.md`, `25-speech-playback.md`
- **Traces to:** Accessibility rows in `srs.md`; browser tests in `structure.md`
- **SRS IDs:** **SRS-FR-049**, **SRS-NFR-013**, **SRS-NFR-015**, **SRS-NFR-016**, **SRS-NFR-035**, **SRS-NFR-036**, **SRS-NFR-037**, **SRS-NFR-012** (part; finished in increment 28), **SRS-NFR-014** (part; finished in increment 28), **SRS-NFR-017** (part; finished in increment 28)

### Requirements

- **SRS-FR-049** (must): The system shall provide all features without an account. (FR-12.2)
- **SRS-NFR-013** (must): All pages shall remain usable at 200 percent browser zoom. (NFR-4.2)
- **SRS-NFR-015** (must): Text and interface elements shall meet WCAG 2.2 AA contrast ratios. (NFR-4.4)
- **SRS-NFR-016** (must): All pages shall work at phone and computer screen widths. (Section 3.1)
- **SRS-NFR-035** (must): The portal shall respect browser or operating-system forced-colors settings while preserving readable text, visible focus, and distinguishable controls and status states. (NFR-4.3, NFR-4.4; inferred low-vision requirement)
- **SRS-NFR-036** (must): Every function of the portal shall be operable using only the keyboard, including upload, sliders, and the before and after view, with visible focus and no keyboard trap. (NFR-4.1; inferred severe low-vision requirement)
- **SRS-NFR-037** (must): All pages shall reflow without loss of content or function at 400 percent browser zoom on a 1280 pixel wide window. (NFR-4.2; inferred severe low-vision requirement)
- **SRS-NFR-012** (must): All interactive elements and dynamic results shall expose accessible names, roles, states, and updates to screen readers. (NFR-4.1; extended for low-vision access)
- **SRS-NFR-014** (must): The portal shall never use color, shape, pattern, or position as the only means of conveying information. (NFR-4.3; extended for low-vision access)
- **SRS-NFR-017** (must): A first time user with a profile set shall be able to enhance an image within 3 clicks of the home page. (NFR-4.5)

### Capability

Automated tests prove keyboard use, zoom, phone width, contrast, and forced colors on every page.

### What may change

`web_ui/templates/`, `static/css/app.css`, `static/js/`, and `src/portal/tests/browser/`.

### What must stay

The server code and API stay as earlier increments left them.

### Implementation notes

- **axe**: `axe-playwright-python` on all five pages, with an image loaded where relevant. Fail on any label or contrast violation.
- **Viewports**: phone 390 by 844, computer 1280 by 800.
- **Zoom**: test 200 percent with a 640 pixel wide viewport, and 400 percent with a 320 pixel wide viewport. Assert `scrollWidth <= clientWidth` on the document.
- **Forced colors**: a Playwright context with `forced_colors="active"`. Use `@media (forced-colors: active)` and `:focus-visible` in `app.css`.
- **Keyboard-only run**: no pointer calls. It covers upload, profile, enhance, identify, Explain, and playback, and it asserts a visible focus style at each stop and no trap.
- **Sign in**: walk every page with a new browser context, and assert no sign in page or prompt.

### Verification

Show each SRS observation in full:

- **SRS-FR-049**: A new browser session uses every feature with no sign in page or prompt.
- **SRS-NFR-013**: At 200 percent zoom, each page's controls are visible and operable, and the enhance task completes.
- **SRS-NFR-015**: axe reports no contrast violations on any page.
- **SRS-NFR-016**: Playwright runs of the enhance task pass at a phone viewport and a computer viewport, with no horizontal page scroll.
- **SRS-NFR-035**: With forced-colors mode enabled, text, focus indicators, controls, and status states remain visible and distinguishable during keyboard navigation.
- **SRS-NFR-036**: A keyboard-only run with no pointer completes the upload, profile, enhance, identify, Explain, and playback tasks, and focus is visible at each stop.
- **SRS-NFR-037**: At 400 percent zoom, each page has no horizontal page scroll, and the enhance and Explain tasks complete.

Show this part now. A later increment finishes the row:

- **SRS-NFR-012**: axe reports no missing label violations on any page. The team does the screen reader walkthrough in increment 28.
- **SRS-NFR-014**: A test confirms that each flag and status has a text equivalent. The team does the review in increment 28.
- **SRS-NFR-017**: A Playwright run from the home page reaches the enhanced result in 3 clicks or fewer. The user study is in increment 28.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Fix the page. Do not disable an axe rule or lower a check.
- Add no feature here. This increment only corrects Web UI defects.
- All pages includes home, workspace, simulator, settings, and intro.
