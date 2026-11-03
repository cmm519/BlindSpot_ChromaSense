# Increment 21: Image workspace results

### Main rules

- Show every result as text. Color, pattern, or position alone must carry no information.
- The slider, strength control, and overlay control request images from the server. The browser computes no pixels.
- Use no global color filter, and add no setting for a default method or overlay style.

### Header

- **Increment:** 21
- **Capability:** Image workspace results
- **Status:** `Standard`
- **Depends on:** `20-home-upload-and-profile.md`
- **Traces to:** Image workspace screen in `srs.md`
- **SRS IDs:** **SRS-FR-008**, **SRS-FR-027**, **SRS-FR-031**, **SRS-FR-032**, **SRS-FR-034**, **SRS-FR-040**, **SRS-FR-050**, **SRS-FR-055**, **SRS-FR-056**, **SRS-FR-066**, **SRS-FR-013** (part; finished in increment 23), **SRS-FR-026** (part; finished in increment 22), **SRS-FR-054** (part; finished in increment 24), **SRS-FR-062** (part; finished in increment 24), **SRS-FR-064** (part; finished in increment 24), **SRS-FR-068** (part; finished in increment 24)

### Requirements

- **SRS-FR-008** (must): The system shall automatically start the pipeline of decode, downscale, local image analysis, confusion detection, and enhancement after a successful upload and display the results. (FR-1.7; local-first change)
- **SRS-FR-027** (must): The system shall inform the user when no confusable pairs are found. (FR-4.6)
- **SRS-FR-031** (should): The system shall allow the user to adjust enhancement strength. (FR-5.4)
- **SRS-FR-032** (must): The system shall allow the user to toggle between original and enhanced views. (FR-5.5)
- **SRS-FR-034** (should): The system shall allow the user to toggle overlays on and off. (FR-6.5)
- **SRS-FR-040** (must): The system shall allow the user to download the enhanced image through the browser. (FR-8.1)
- **SRS-FR-050** (must): The system shall provide a keyboard- and screen-reader-navigable list of detected dominant colors and confusable pairs; each entry shall expose available color names and values, its pattern label, and its relationship to other entries. (FR-4.1, FR-4.5, FR-7.3, FR-7.4; inferred low-vision requirement)
- **SRS-FR-055** (must): After a successful upload, the system shall recognize the text in the image locally, without the AI service, and list each piece of text as a separate item, with its location in the image, in reading order. (FR-9.2; severe low-vision requirement; local-first change)
- **SRS-FR-056** (must): After a successful upload, the system shall detect each distinct shape in the image locally, without the AI service, and list it as a separate item, with its kind, its location, and the palette ID of its color. (FR-6.2; severe low-vision requirement; local-first change)
- **SRS-FR-066** (should): The system shall classify each image locally as a chart, map, flat graphic, or photograph using measured image features, and shall tell the user that results for a photograph are best effort. (FR-9.1; local-first change)
- **SRS-FR-013** (must): The system shall store the active profile in browser storage and apply it to all features. (FR-2.3)
- **SRS-FR-026** (should): The system shall display the list of confusable pairs with swatches, names, and patterns. (FR-4.5, UC-6)
- **SRS-FR-054** (must): With no CVD selected, the system shall skip confusable pair flagging and enhancement, show the original image, and still provide the color list, local analysis results, color identification, and AI interpretation. (FR-1.7, FR-2.1; inferred severe low-vision requirement; local-first change)
- **SRS-FR-062** (must): The system shall announce the start and the completion or failure of an upload, the pipeline, and each AI request to screen readers, without moving keyboard focus. (FR-1.6, FR-1.7, FR-9.9, NFR-4.1; inferred severe low-vision requirement)
- **SRS-FR-064** (must): Each image in the portal shall have a text alternative that states which view it shows, a summary of the local analysis, and, once an interpretation exists, its summary. (NFR-4.1; severe low-vision requirement; local-first change)
- **SRS-FR-068** (must): The system shall show the local analysis results after upload without any request to the AI service, naming each item's source and flagging each local text and shape item as unverified until an AI read agrees with it. (FR-9.6; local-first change)

### Capability

The workspace shows the enhanced result, before and after views, overlays, download, and all local analysis results as accessible text.

### What may change

`web_ui/templates/workspace.html`, `static/js/workspace.js`, `static/css/app.css`, and `src/portal/tests/browser/`.

### What must stay

`upload.js`, `profile.js`, and API endpoints stay as earlier increments left them.

### Implementation notes

- **Before and after**: two images with a native `<input type="range">` that controls a CSS clip. A native range is keyboard operable. With no CVD, hide this control and say why in text.
- **Strength**: a native range, debounced, that requests `render` with `strength`. Download uses the same `strength`.
- **Overlay**: a checkbox that switches between `view=enhanced` and `view=overlay`.
- **Download**: a link to `export` with the profile and `strength`, and a `download` attribute. With no CVD, it is not offered, and the text says why.
- **On load**: `workspace.js` uses the upload response if it has one. Otherwise it calls `GET analysis` and `POST analyze`. That also applies a profile changed on the settings page (SRS-FR-014).
- **Color and pair list** (SRS-FR-050): a semantic list. Each color has its name, HEX, RGB, HSL, pattern label, and the colors it is confused with. Each pair has both names, both distances, and its pattern.
- **Local results**: lists of text, shapes, regions, and legend. Each item has its source and a text flag.
- **Messages**: "no enhancement needed" when `enhancement_needed` is false. The best effort message when the type is photograph.
- **Text alternative**: `alt` names the view, and `aria-describedby` points to the summary text.

### Verification

Show each SRS observation in full:

- **SRS-FR-008**: With a profile set, a successful upload shows the enhanced result and the local analysis results without any further user action.
- **SRS-FR-027**: An image with no confusable pairs under the active profile shows a message that no enhancement is needed.
- **SRS-FR-031**: Moving the strength control changes the enhanced image, and the change stays inside the mask.
- **SRS-FR-032**: The before and after slider in the image workspace shows the original and the enhanced image.
- **SRS-FR-034**: The overlay control adds the patterns to the displayed image and removes them.
- **SRS-FR-040**: The download control saves a file that opens as the enhanced image.
- **SRS-FR-050**: Using only the keyboard and a screen reader, a tester can navigate detected colors and pairs and hear their names, values, pattern labels, and pair relationships.
- **SRS-FR-055**: With no AI provider configured, uploading a flat graphic with known text lists each piece of text with its location, in reading order.
- **SRS-FR-056**: With no AI provider configured, uploading a flat graphic with a known circle, rectangle, and triangle lists each one with its kind, location, and color name.
- **SRS-FR-066**: Each image in a labeled sample set receives a type, and a test photograph shows the best effort message.

Show this part now. A later increment finishes the row:

- **SRS-FR-013**: Enhancement requests carry the stored profile.
- **SRS-FR-026**: The image workspace lists a test image's pairs, with swatches, names, and patterns.
- **SRS-FR-054**: With no CVD selected, an upload shows the original image, the color list, and local analysis results with no enhanced image.
- **SRS-FR-062**: Pipeline start and completion or failure appear in the `aria-live` element, with no focus change.
- **SRS-FR-064**: Each image's text alternative states its view and the local analysis summary.
- **SRS-FR-068**: The results list each item as local and unverified after upload, with no provider request.

Also confirm:

- A Playwright run confirms that the enhanced image request changes when the strength control changes, and that the page makes no provider request (stubbed provider).

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Show every result as text. Color, pattern, or position alone must carry no information.
- The slider, strength control, and overlay control request images from the server. The browser computes no pixels.
- Use no global color filter, and add no setting for a default method or overlay style.
