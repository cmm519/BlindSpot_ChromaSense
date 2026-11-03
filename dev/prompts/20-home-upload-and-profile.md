# Increment 20: Home, upload, and profile pages

### Main rules

- The Web UI does no pixel processing. It uses server-rendered Jinja2 pages and plain JavaScript, with no build step.
- Keep focus on the upload control during and after an upload.
- Add no sign in, privacy notice, or permission prompt.

### Header

- **Increment:** 20
- **Capability:** Home, upload, and profile pages
- **Status:** `CRITICAL`
- **Depends on:** `16-server-and-image-api.md`
- **Traces to:** Web UI in `architecture.md`; screens in `srs.md`
- **SRS IDs:** **SRS-FR-001**, **SRS-FR-002**, **SRS-FR-003**, **SRS-FR-004**, **SRS-FR-007**, **SRS-FR-009**, **SRS-FR-012**, **SRS-FR-053**, **SRS-FR-011** (part; finished in increment 22), **SRS-FR-013** (part; finished in increment 23), **SRS-FR-062** (part; finished in increment 24)

### Requirements

- **SRS-FR-001** (must): The system shall allow the user to select an image using the browser file picker. (FR-1.1)
- **SRS-FR-002** (must): The system shall allow the user to upload an image by drag and drop. (FR-1.2)
- **SRS-FR-003** (should): The system shall allow the user to paste an image from the clipboard. (FR-1.3)
- **SRS-FR-004** (must): The system shall accept PNG, JPEG, HEIC, and WEBP images. (FR-1.4)
- **SRS-FR-007** (must): The system shall display an error message for unsupported or corrupted files. (FR-1.6)
- **SRS-FR-009** (must): If no CVD profile is set when an image is uploaded, the system shall ask the user to select one, including the no CVD option, before starting the pipeline. (FR-1.7, UC-1; inferred severe low-vision requirement)
- **SRS-FR-012** (must): The system shall allow the user to set severity from 0 to 1 using a slider, unless no CVD is selected. (FR-2.2; inferred severe low-vision requirement)
- **SRS-FR-053** (should): The portal shall include an introduction that explains CVD profiles and enhancement. (Section 2.6)
- **SRS-FR-011** (must): The system shall allow the user to select a CVD type (protan, deutan, tritan, or achromatopsia) or no CVD. (FR-2.1; inferred severe low-vision requirement)
- **SRS-FR-013** (must): The system shall store the active profile in browser storage and apply it to all features. (FR-2.3)
- **SRS-FR-062** (must): The system shall announce the start and the completion or failure of an upload, the pipeline, and each AI request to screen readers, without moving keyboard focus. (FR-1.6, FR-1.7, FR-9.9, NFR-4.1; inferred severe low-vision requirement)

### Capability

A user can set a profile and upload an image by any method, and sees the original in the workspace section.

### What may change

`web_ui/templates/base.html`, `home.html`, `settings.html`, `intro.html`, a minimal `workspace.html`, `static/js/announce.js`, `profile.js`, `upload.js`, `static/css/app.css`, `web_api/routers/pages.py`, `web_api/app.py`, and `src/portal/tests/browser/`.

### What must stay

API endpoints and use cases stay as earlier increments left them.

### Implementation notes

**Page routes** (`derived`, because `srs.md` names the screens but not their URLs): `/`, `/workspace/{image_id}`, `/simulator`, `/settings`, `/intro`.

**Focus and page change** (`derived`): SRS-FR-062 keeps focus on the control during an upload, and SRS-FR-001 needs the workspace to show the image with no further action. A page navigation would lose both the focus and the live message. So `upload.js` does the following:

1. Sends the upload with `fetch`.
2. On success, fetches `/workspace/{image_id}` and places its `<main>` content into a section on the home page.
3. Calls `history.pushState` with that URL.

A direct visit to `/workspace/{image_id}` renders the same content as a full page. Script behavior is started by a function that both paths call.

**`base.html`**: `lang="en"`, skip link, navigation, one shared `aria-live` element, and deferred scripts. Keep `image_id` in the Simulator and Settings links with `?image_id=` when an image is loaded, so that the user can return.

**`profile.js`**: `localStorage` holds type, severity, and time of last update. With `none`, disable the slider and send no severity.

**Profile prompt** (SRS-FR-009): with no stored profile, a modal `<dialog>` offers the four types, no CVD, and severity. The chosen file stays in memory, and the upload starts after the choice. Return focus to the upload control afterward.

**`upload.js`**: file picker, `drop`, and `paste` with `clipboardData`.

**`intro.html`**: explains CVD profiles and enhancement. It gives no medical advice, because `srs.md` puts diagnosis out of scope.

**Minimal `workspace.html`**: one image, from `render?view=original`. Increment 21 completes it. Every format renders because the server returns PNG.

**Browser tests**: `conftest.py` starts the real app with a temporary data directory on a free port.

### Verification

Show each SRS observation in full:

- **SRS-FR-001**: Selecting a PNG in the file picker uploads it and the image workspace shows the image.
- **SRS-FR-002**: Dropping an image file on the upload control uploads it and the image workspace shows the image.
- **SRS-FR-003**: Pasting a copied image on the home page uploads it and the image workspace shows the image.
- **SRS-FR-004**: One sample file of each format uploads successfully and renders in the image workspace.
- **SRS-FR-007**: Uploading a text file renamed as a PNG and a truncated JPEG each shows an error message, and the pipeline does not start.
- **SRS-FR-009**: With empty browser storage, an upload shows the profile prompt with the no CVD option, and the results appear after an option is selected.
- **SRS-FR-012**: The slider reaches 0 and 1, the selected value is sent with the next request that needs the profile, and with no CVD selected the slider is disabled and no severity is sent.
- **SRS-FR-053**: A new user can open the introduction in the portal and read both explanations.

Show this part now. A later increment finishes the row:

- **SRS-FR-011**: The settings page offers all four types and no CVD. Increment 22 shows a selected type in a simulation.
- **SRS-FR-013**: After a reload, the profile is still selected, and the upload request carries it.
- **SRS-FR-062**: During an upload, start and completion or failure messages appear in the `aria-live` element, and focus stays on the same control.

Also confirm:

- A Playwright test records `document.activeElement` before and after an upload and a failed upload, and it is the same control.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

Conflicting requirements and the first integration of browser and API. A separate workspace page conflicts with keeping focus and live messages during an upload.

### How to recognize failure

Focus falls to `<body>` after an upload, the completion message is never in the live region, or scripts in the placed `<main>` content do not start.

### Isolation test

Test `announce.js` and `profile.js` on the settings page alone. Test `upload.js` against the API with no page placement. Then add the placement step and assert `activeElement` again.

### Rollback

Return the tree to the state that **`prompts/19-follow-up-questions.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/19-follow-up-questions.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- The Web UI does no pixel processing. It uses server-rendered Jinja2 pages and plain JavaScript, with no build step.
- Keep focus on the upload control during and after an upload.
- Add no sign in, privacy notice, or permission prompt.
