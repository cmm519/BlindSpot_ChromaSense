# Increment 17: AI read and verification

### Main rules

- The AI read request must not contain local text, shape, or legend results. `VisionReader.read` takes only `image`, `palette`, and `image_type`.
- One Explain makes exactly one provider request. Never make a second read.
- Only AI Gateway calls the provider. The API key appears in no response, page, script, or log.

### Header

- **Increment:** 17
- **Capability:** AI read and verification
- **Status:** `CRITICAL`
- **Depends on:** `16-server-and-image-api.md`
- **Traces to:** `InterpretImage`, `HttpVisionReader`, and decision 3 in `architecture.md`
- **SRS IDs:** **SRS-FR-042**, **SRS-FR-043**, **SRS-FR-057**, **SRS-FR-067**, **SRS-FR-044** (part; finished in increment 24), **SRS-FR-046** (part; finished in increment 24), **SRS-FR-058** (part; finished in increment 24), **SRS-FR-068** (part; finished in increment 24)

### Requirements

- **SRS-FR-042** (must): When the user clicks Explain, the server shall send the image, its extracted color palette with an ID for each color, and the local image type, and request structured output containing chart type, legend entries mapped to palette IDs, text items, shape items, and a summary. The request shall not include the local text, shape, or legend results, so that the AI read stays independent of them. (FR-9.4; local-first change)
- **SRS-FR-043** (must): The system shall validate each legend entry against the extracted palette and flag entries with a missing palette ID or a palette ID used by more than one entry. (FR-9.5)
- **SRS-FR-057** (must): When the user clicks Explain, the system shall make one AI read of the image, and shall flag a text or shape item as verified only when that read and the local analysis agree on it. Text agrees when it matches after normalizing case and whitespace. A shape agrees when its kind and palette ID match. (FR-9.5, FR-9.6; severe low-vision requirement; local-first change)
- **SRS-FR-067** (should): The system shall detect a legend of color swatches and nearby text locally, map each entry to a palette ID, and flag an AI legend entry as unverified when a local entry for the same palette ID has different text. (FR-9.2, FR-9.5; local-first change)
- **SRS-FR-044** (must): The system shall display a verified or unverified flag for each interpreted item, based on the result of the legend validation or, for shape and text items, the agreement between the AI read and the local analysis. (FR-9.6, UC-2; local-first change)
- **SRS-FR-046** (must): The system shall show a clear message when the AI service is unavailable. (FR-9.9, UC-2)
- **SRS-FR-058** (must): The system shall take the name and values of each color item from its palette entry and the bundled named color dataset, not from the AI text, and shall flag a color item as unverified when it has no valid palette ID. (FR-7.3, FR-9.5; inferred severe low-vision requirement)
- **SRS-FR-068** (must): The system shall show the local analysis results after upload without any request to the AI service, naming each item's source and flagging each local text and shape item as unverified until an AI read agrees with it. (FR-9.6; local-first change)

### Capability

`POST /api/interpret` gets one structured AI read and returns each item with a verification flag from the comparison with local analysis.

### What may change

`core/use_cases/interpret_image.py`, `core/policy/ai_verification.py`, AI additions to `core/models.py`, `ai_gateway/http_vision_reader.py`, `ai_gateway/read_schema.json`, `web_api/routers/ai.py`, `web_api/schemas.py`, `main/settings.py`, `main/wiring.py`, and tests in `src/portal/tests/core/`, `ai_gateway/`, and `web_api/`.

### What must stay

Nothing runs at upload that calls the provider. Color Engine and the pipeline use cases stay as earlier increments left them.

### Implementation notes

**Flow in `InterpretImage`**: load the stored image, call `VisionReader.read` once, call `AiUsageLedger.record`, run `verify_items`, return the `Interpretation`. Increment 18 adds the cache and limit checks.

**`verify_items(read, local, palette)`** in `core/policy/ai_verification.py`

- Text: normalize with `" ".join(text.split()).casefold()`. Match one to one against local text items. A match is `VERIFIED` with source `both`.
- Shape: match one to one on `kind` and `palette_id`. A match is `VERIFIED` with source `both`.
- An item found by only one source is `UNVERIFIED`, with source `ai` or `local`.
- Color: one `ColorItem` for each palette ID that the read references. A valid ID is `VERIFIED`, with its name and values from `ColorNamer`. An invalid ID is `UNVERIFIED`.
- Legend: `validate_legend(entries, palette)` flags a missing or unknown palette ID and an ID used by more than one entry, with the reason. A legend entry is also `UNVERIFIED` when a local legend entry for the same palette ID has different normalized text (SRS-FR-067).

**`derived` contracts**

- `AiRead(chart_type, legend, text_items, shape_items, summary, estimated_cost)`.
- Each provider legend entry and shape item may carry an optional `color_name`. Parse it and discard it, so that SRS-FR-058 is testable.
- `read_schema.json` has chart type, legend entries with palette IDs, text items (one per line of text), shape items (kind from `circle`, `rectangle`, `triangle`, `other`, plus palette ID), and summary.
- The image sent is the working copy as a base64 PNG, with the palette as `{id, hex}` and the image type.
- `estimated_cost` is `CHROMASENSE_COST_PER_REQUEST` (default 0).
- `POST /api/interpret` body: `{"image_id"}`. `AiUnavailable` maps to status 503.

**Provider wire format** (`derived`): `architecture.md` says that the provider has not been chosen. Use the OpenAI-compatible chat completions shape, with a `json_schema` response format, a bearer token, and `CHROMASENSE_PROVIDER_URL` and `CHROMASENSE_MODEL`. Keep it in two private functions in `http_vision_reader.py`, so that choosing a provider changes only those functions.

**Failure**: a missing setting, connection error, timeout (25 seconds, `derived`, under SRS-NFR-004), non-2xx status, or malformed response raises `AiUnavailable`. Its message never contains the key.

**Tests**: `httpx.MockTransport` for the gateway, and a fake `VisionReader` for the core.

### Verification

Show each SRS observation in full:

- **SRS-FR-042**: With a stubbed AI provider, the captured request has the image, the palette with IDs, the image type, and the output schema, it contains none of the local text, shape, or legend results, and no request is sent before Explain is clicked.
- **SRS-FR-043**: Stubbed responses with a missing ID and a duplicated ID have those entries flagged, and a valid response has none flagged.
- **SRS-FR-057**: With a stubbed provider, one Explain makes exactly one provider request, items that match are flagged verified, items that differ or appear in only one source are flagged unverified, and the request counts toward the rate limit and spend cap.
- **SRS-FR-067**: For a chart with a known legend, the local entries match it with no AI provider configured, and a stubbed AI entry with different text for the same palette ID is flagged unverified.

Show this part now. A later increment finishes the row:

- **SRS-FR-044**: The `POST /api/interpret` response has a verified or unverified state on each item that matches the validation or agreement result.
- **SRS-FR-046**: With the provider unreachable, `POST /api/interpret` returns a clear message with status 503.
- **SRS-FR-058**: With a stubbed response that gives a wrong color name, the response has the dataset name. An invalid palette ID is unverified.
- **SRS-FR-068**: A stubbed read that matches a local item changes that item to verified.

Also confirm:

- A test inspects the captured provider request and finds none of the local text, shape, or legend strings from the fixture.
- With no provider configured, the server still starts, and upload still works.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/core
docker compose run --rm dev pytest src/portal/tests/ai_gateway
docker compose run --rm dev pytest src/portal/tests/web_api
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

An architectural boundary and conflicting requirements. Verification is only meaningful if the two sources stay independent, and the provider has not been chosen, so the wire format is a best guess.

### How to recognize failure

Items are verified with a read that saw local results, text items fail to match because of line grouping, or a provider failure becomes a 5xx traceback instead of the clear message.

### Isolation test

Test `verify_items` and `validate_legend` with hand-built `AiRead` and `ImageAnalysis` values and no gateway. Test `HttpVisionReader` with `httpx.MockTransport` and no core. Then run `InterpretImage` with a fake reader.

### Rollback

Return the tree to the state that **`prompts/16-server-and-image-api.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/16-server-and-image-api.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- The AI read request must not contain local text, shape, or legend results. `VisionReader.read` takes only `image`, `palette`, and `image_type`.
- One Explain makes exactly one provider request. Never make a second read.
- Only AI Gateway calls the provider. The API key appears in no response, page, script, or log.
