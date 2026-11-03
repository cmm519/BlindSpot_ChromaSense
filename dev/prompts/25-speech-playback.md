# Increment 25: Speech playback

### Main rules

- Use the browser's Web Speech API only. Add no server-side speech.
- Automatic reading is off by default.
- Add no spoken input.

### Header

- **Increment:** 25
- **Capability:** Speech playback
- **Status:** `Standard`
- **Depends on:** `23-color-point.md`, `24-ai-panel.md`
- **Traces to:** Decision 2 and `speech.js` in `architecture.md` and `structure.md`
- **SRS IDs:** **SRS-FR-052**, **SRS-FR-063**

### Requirements

- **SRS-FR-052** (must): The system shall provide keyboard-accessible controls to start, pause or resume, and stop spoken playback of AI responses, local analysis results, and color identification results, including the verified or unverified states of items. (FR-7.6, FR-9.6, NFR-4.1; inferred low-vision requirement; local-first change)
- **SRS-FR-063** (should): The system shall let the user set speech rate and turn on automatic reading of new results, off by default so that speech does not overlap a screen reader, and shall keep these settings in browser storage. (NFR-4.1; inferred severe low-vision requirement)

### Capability

A user can start, pause, resume, and stop spoken playback of results, and set the rate and automatic reading.

### What may change

`static/js/speech.js`, `web_ui/templates/workspace.html`, `settings.html`, `static/js/workspace.js`, `ai_panel.js`, `color_point.js` (only to hand text to `speech.js`), and `src/portal/tests/browser/`.

### What must stay

The server is unchanged. Audio never crosses the server.

### Implementation notes

- **`speech.js`**: use `speechSynthesis` `speak`, `pause`, `resume`, and `cancel`, and `SpeechSynthesisUtterance.rate`. Keep rate and automatic reading in `localStorage`.
- **Controls**: native buttons for start, pause or resume, and stop, for local analysis, AI responses, and color results. Announce the state as text.
- **Spoken text**: use the same text as the page, including each item's verified or unverified state.
- **Settings**: rate range 0.5 to 2, default 1 (`derived`), and an automatic reading checkbox.
- **Unavailable speech** (`derived`): if the browser has no `speechSynthesis`, the controls say so in text, and nothing else changes.
- **Browser tests**: add an init script that replaces `speechSynthesis` with a recorder, because the headless browser has no voices.

### Verification

Show each SRS observation in full:

- **SRS-FR-052**: With speech output enabled, keyboard operation starts, pauses or resumes, and stops playback of an AI response, of the local analysis results, and of a color result; the spoken item content includes each item's verification state.
- **SRS-FR-063**: With automatic reading off, a new result is not spoken; with it on, the result is spoken without further action at the set rate; both settings survive a page reload.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/browser
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Use the browser's Web Speech API only. Add no server-side speech.
- Automatic reading is off by default.
- Add no spoken input.
