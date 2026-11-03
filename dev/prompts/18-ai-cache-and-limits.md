# Increment 18: AI cache, rate limit, and spend cap

### Main rules

- The rules for limits and expiry belong in Application Core. The SQLite adapters only store and query.
- A cached result makes no provider call and does not count toward a limit.
- Check limits before the provider call.

### Header

- **Increment:** 18
- **Capability:** AI cache, rate limit, and spend cap
- **Status:** `Standard`
- **Depends on:** `17-ai-read-and-verification.md`
- **Traces to:** `SqliteInterpretationCache`, `SqliteAiUsageLedger`, and `AiLimits` in `architecture.md`
- **SRS IDs:** **SRS-FR-047**, **SRS-FR-048**, **SRS-NFR-010**, **SRS-NFR-011** (part; finished in increment 24)

### Requirements

- **SRS-FR-047** (should): The system shall cache each AI interpretation by image and return the cached result for the same image. (UC-2, Section 7)
- **SRS-FR-048** (should): The system shall expire cached interpretations after 30 days. (Section 7)
- **SRS-NFR-010** (must): The server shall rate limit AI requests per browser session and IP address. (NFR-2.4)
- **SRS-NFR-011** (must): The server shall stop AI requests when a configurable global spend cap is reached. (NFR-2.4, UC-2)

### Capability

AI reads are cached by image hash for 30 days, and refused past a rate limit or spend cap.

### What may change

`storage/schema.sql`, `storage/sqlite_interpretation_cache.py`, `storage/sqlite_ai_usage_ledger.py`, `core/policy/ai_limits.py`, `core/use_cases/interpret_image.py`, `core/use_cases/purge_expired.py`, `main/settings.py`, `main/wiring.py`, `web_api/routers/ai.py`, and tests.

### What must stay

`verify_items` and `HttpVisionReader` stay as increment 17 left them.

### Implementation notes

**Flow in `InterpretImage`**: cache `get`, then `AiLimits.check`, then `read`, then `record`, then verify, then cache `put`. The cache stores the final flags (decision 3).

**`derived` contracts**

- `Interpretation.expires_at` is `created_at + 30 days`, computed in core. The adapter compares `expires_at` with `now`, and holds no retention rule.
- `AiUsage(session_count, ip_count, total_cost)` is what `AiLimits.check` receives.
- `AiLimits(session_limit, ip_limit, spend_cap)`: raise `AiRateLimited` past either count, and `AiSpendCapReached` at or past the cap.
- A failed provider call is recorded with cost 0, so that it counts toward the rate limit.
- `usage` counts requests in the last `CHROMASENSE_RATE_WINDOW_SECONDS`. `total_cost` sums the current UTC calendar month. `srs.md` says "each period" without a length.

**`derived` defaults**: 20 requests per session and 60 per IP address per hour, and a spend cap of 5.00.

**`derived` statuses**: `AiRateLimited` maps to 429. `AiSpendCapReached` maps to 503, with the message "AI is temporarily unavailable".

**Purge**: `PurgeExpired` also calls `InterpretationCache.delete_expired`.

**Storage**: open a new `sqlite3` connection for each call, on a file in the data directory.

### Verification

Show each SRS observation in full:

- **SRS-FR-047**: A second Explain on the same image returns the result without a new request to the stubbed provider.
- **SRS-FR-048**: An entry dated 31 days ago is not returned, and the next Explain makes a new provider request.
- **SRS-NFR-010**: Requests past the configured limit from one session, and from one IP address, are refused, and no provider call is made.

Show this part now. A later increment finishes the row:

- **SRS-NFR-011**: With a low test cap, the request past the cap makes no provider call, and the response says that AI is temporarily unavailable.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/storage
docker compose run --rm dev pytest src/portal/tests/core
docker compose run --rm dev pytest src/portal/tests/web_api
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- The rules for limits and expiry belong in Application Core. The SQLite adapters only store and query.
- A cached result makes no provider call and does not count toward a limit.
- Check limits before the provider call.
