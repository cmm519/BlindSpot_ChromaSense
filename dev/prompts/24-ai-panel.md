# Increment 24: AI panel

### Main rules

- Send nothing to AI until the user clicks Explain. Add no confirmation step.
- A failed request must leave all current results on screen.
- Every flag is the text verified or unverified, and it is never shown by color alone.

### Header

- **Increment:** 24
- **Capability:** AI panel
- **Status:** `Standard`
- **Depends on:** `19-follow-up-questions.md`, `21-image-workspace.md`
- **Traces to:** AI panel screen in `srs.md`; `ai_panel.js` in `structure.md`
- **SRS IDs:** **SRS-FR-044**, **SRS-FR-045**, **SRS-FR-046**, **SRS-FR-051**, **SRS-FR-054**, **SRS-FR-058**, **SRS-FR-060**, **SRS-FR-062**, **SRS-FR-064**, **SRS-FR-068**, **SRS-NFR-011**, **SRS-NFR-019**

### Requirements

- **SRS-FR-044** (must): The system shall display a verified or unverified flag for each interpreted item, based on the result of the legend validation or, for shape and text items, the agreement between the AI read and the local analysis. (FR-9.6, UC-2; local-first change)
- **SRS-FR-045** (must): The system shall allow typed follow up questions, grounded in the same image context. (FR-9.7)
- **SRS-FR-046** (must): The system shall show a clear message when the AI service is unavailable. (FR-9.9, UC-2)
- **SRS-FR-051** (must): The system shall expose AI chart type, legend entries, summary, follow-up answers, and each item's verified or unverified state as semantically structured text available to screen readers. (FR-9.4, FR-9.6, FR-9.7, NFR-4.1; inferred low-vision requirement)
- **SRS-FR-054** (must): With no CVD selected, the system shall skip confusable pair flagging and enhancement, show the original image, and still provide the color list, local analysis results, color identification, and AI interpretation. (FR-1.7, FR-2.1; inferred severe low-vision requirement; local-first change)
- **SRS-FR-058** (must): The system shall take the name and values of each color item from its palette entry and the bundled named color dataset, not from the AI text, and shall flag a color item as unverified when it has no valid palette ID. (FR-7.3, FR-9.5; inferred severe low-vision requirement)
- **SRS-FR-060** (must): The AI panel shall explain in text what each flag means, including that a verified color was checked against the image's pixels, that verified text or a verified shape means the AI read and the local analysis agreed, and that neither guarantees correctness. (FR-9.6; severe low-vision requirement; local-first change)
- **SRS-FR-062** (must): The system shall announce the start and the completion or failure of an upload, the pipeline, and each AI request to screen readers, without moving keyboard focus. (FR-1.6, FR-1.7, FR-9.9, NFR-4.1; inferred severe low-vision requirement)
- **SRS-FR-064** (must): Each image in the portal shall have a text alternative that states which view it shows, a summary of the local analysis, and, once an interpretation exists, its summary. (NFR-4.1; severe low-vision requirement; local-first change)
- **SRS-FR-068** (must): The system shall show the local analysis results after upload without any request to the AI service, naming each item's source and flagging each local text and shape item as unverified until an AI read agrees with it. (FR-9.6; local-first change)
- **SRS-NFR-011** (must): The server shall stop AI requests when a configurable global spend cap is reached. (NFR-2.4, UC-2)
- **SRS-NFR-019** (must): The portal shall recover from AI or network failures without losing the current results. (NFR-5.2)

### Capability

A user can click Explain, read or hear each AI item with its flag, ask questions, and keep working when AI fails.

### What may change

`static/js/ai_panel.js`, `web_ui/templates/workspace.html`, `static/js/workspace.js` (only to update the image text alternative), `static/css/app.css`, and `src/portal/tests/browser/`.

### What must stay

The AI endpoints and policy stay as earlier increments left them.

### Implementation notes

- **Structure**: headings and lists for chart type, summary, legend, text items, shape items, and color items. Each item has its source and flag.
- **Explanation** (SRS-FR-060): a keyboard-reachable section that states all three points: a verified color was checked against the image's pixels, verified text or a verified shape means that the AI read and the local analysis agreed, and neither guarantees correctness.
- **Question**: a labeled text field and a button. Each answer has its flag and the items it cites. On a 409, tell the user to click Explain first.
- **Status**: announce start, completion, and failure through `announce.js`. Do not move focus. Use `aria-busy` on the panel during a request.
- **Messages**: distinct messages for AI unavailable (503) and rate limited (429).
- **After Explain**: update matching local items to their new flags, and add the interpretation summary to each image's text alternative.
- **Browser tests**: run a small stub HTTP provider in `conftest.py` and point `CHROMASENSE_PROVIDER_URL` at it. Include an unreachable case.

### Verification

Show each SRS observation in full:

- **SRS-FR-044**: The AI panel shows a text flag of verified or unverified on each item, matching the validation or agreement result.
- **SRS-FR-045**: With a stubbed AI provider, a typed question produces a request with the same image and palette, and the answer appears in the AI panel.
- **SRS-FR-046**: With the provider unreachable, clicking Explain shows the message and the other features still work.
- **SRS-FR-051**: A screen reader announces the AI result content and the matching verified or unverified state for each interpreted item.
- **SRS-FR-054**: With no CVD selected, an upload shows the original image, the color list, and the local analysis results with no enhanced image, and color identification and Explain both work.
- **SRS-FR-058**: With a stubbed response that calls a palette color by the wrong name, the panel shows the dataset name; an item with an invalid palette ID is flagged unverified.
- **SRS-FR-060**: The explanation is reachable by keyboard from the AI panel, and a screen reader announces all three points.
- **SRS-FR-062**: During an upload and an Explain, each message appears in an `aria-live` element and focus stays on the same control, including when the request fails.
- **SRS-FR-064**: A screen reader announces the view name and the local analysis summary for each image after upload, and the interpretation summary after Explain completes.
- **SRS-FR-068**: With a stubbed provider, an upload makes no provider request, the results list each item as local and unverified, and a matching item becomes verified after Explain.
- **SRS-NFR-011**: With a low test cap, the request past the cap makes no provider call, and the user sees that AI is temporarily unavailable.
- **SRS-NFR-019**: After a failed Explain, the enhanced image and confusable pairs remain on screen and the next request works.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Send nothing to AI until the user clicks Explain. Add no confirmation step.
- A failed request must leave all current results on screen.
- Every flag is the text verified or unverified, and it is never shown by color alone.
