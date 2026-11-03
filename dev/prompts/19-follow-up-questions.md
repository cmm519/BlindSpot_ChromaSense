# Increment 19: Follow up questions

### Main rules

- An answer is verified only when it cites at least one item and every cited item is verified.
- Follow up requests count toward the rate limit and spend cap.
- Add no spoken input for questions, because `srs.md` puts that out of scope.

### Header

- **Increment:** 19
- **Capability:** Follow up questions
- **Status:** `Standard`
- **Depends on:** `18-ai-cache-and-limits.md`
- **Traces to:** `AnswerQuestion` and `verify_answer` in `architecture.md`
- **SRS IDs:** **SRS-FR-059**, **SRS-FR-045** (part; finished in increment 24)

### Requirements

- **SRS-FR-059** (must): Each follow up answer shall cite the interpreted items it relies on, and the system shall flag the answer as verified only when every cited item is verified. (FR-9.6, FR-9.7; inferred severe low-vision requirement)
- **SRS-FR-045** (must): The system shall allow typed follow up questions, grounded in the same image context. (FR-9.7)

### Capability

`POST /api/ask` answers a typed question about an interpreted image, with citations and a flag.

### What may change

`core/use_cases/answer_question.py`, `verify_answer` in `core/policy/ai_verification.py`, `ask` in `ai_gateway/http_vision_reader.py`, `web_api/routers/ai.py`, `web_api/schemas.py`, and tests.

### What must stay

`read` and the `InterpretImage` flow stay as earlier increments left them.

### Implementation notes

- **`derived`**: `AiAnswer(text, cited_item_ids, estimated_cost)`. `POST /api/ask` body: `{"image_id", "question"}`, with a question of 1 to 1000 characters.
- Get the `Interpretation` for the image's hash from the cache. If none exists, raise `NotInterpreted`, mapped to status 409 (`derived`, because the endpoint table says "an interpreted image").
- `VisionReader.ask(image, palette, items, question)` receives the interpreted items with their IDs and flags. Decision 3's independence rule applies only to the read.
- An unknown cited ID counts as unverified.
- Each question stands alone. Do not store a conversation, because `srs.md` names no such data.

### Verification

Show each SRS observation in full:

- **SRS-FR-059**: Stubbed answers citing only verified items are flagged verified; answers citing an unverified item or no items are flagged unverified.

Show this part now. A later increment finishes the row:

- **SRS-FR-045**: With a stubbed provider, `POST /api/ask` sends the same image and palette, and returns the answer.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/core
docker compose run --rm dev pytest src/portal/tests/ai_gateway
docker compose run --rm dev pytest src/portal/tests/web_api
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- An answer is verified only when it cites at least one item and every cited item is verified.
- Follow up requests count toward the rate limit and spend cap.
- Add no spoken input for questions, because `srs.md` puts that out of scope.
