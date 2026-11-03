# Increment 14: Image storage and expiry

### Main rules

- Storage Adapter holds no business rule. Application Core computes expiry times and passes `now`.
- Keep the port method names from `architecture.md`.
- Never build a path from unchecked input.

### Header

- **Increment:** 14
- **Capability:** Image storage and expiry
- **Status:** `Standard`
- **Depends on:** `13-upload-pipeline.md`
- **Traces to:** Storage Adapter and `PurgeExpired` in `architecture.md`
- **SRS IDs:** **SRS-FR-006**, **SRS-FR-010** (part; finished in increment 16)

### Requirements

- **SRS-FR-006** (must): The system shall downscale images larger than 12 megapixels for analysis while preserving the original for export. (FR-1.5)
- **SRS-FR-010** (must): The system shall automatically delete uploaded images and working copies after a configurable period, with a default of 24 hours. (Sections 2.5 and 7)

### Capability

Uploaded originals, working copies, and local analysis persist on the filesystem and are deleted on expiry.

### What may change

`chromasense/storage/filesystem_image_store.py`, `core/use_cases/purge_expired.py`, and tests in `src/portal/tests/storage/` and `src/portal/tests/core/`.

### What must stay

Port signatures and pipeline use cases stay as increment 13 left them.

### Implementation notes

- **Layout** (`derived`): `<data_dir>/images/<image_id>/` holds `original.bin`, `working.png`, `record.json`, and `analysis.json`.
- Write to a temporary folder, then rename it, so a partly written image is never loaded.
- Reject an `image_id` that does not match `^[0-9a-f]{32}$`, and return `None` from `load`.
- `delete_expired(now)` removes each image whose `expires_at` is at or before `now`.
- `PurgeExpired` calls `delete_expired` on the store. Increment 18 adds the cache call. Server Main schedules it in increment 16.
- `ProcessUpload` with the real store on a 20 megapixel fixture proves SRS-FR-006. Keep the fixture under 10 MB, because SRS-NFR-009 limits uploads. A flat PNG fits.

### Verification

Show each SRS observation in full:

- **SRS-FR-006**: For a 20 megapixel upload, the analysis image is at most 12 megapixels and the stored original keeps its 20 megapixel dimensions.

Show this part now. A later increment finishes the row:

- **SRS-FR-010**: With a fake clock past the expiry time, `PurgeExpired` removes the image folder from a temporary directory.

Run from the repository root:

```
docker compose run --rm dev pytest src/portal/tests/storage
docker compose run --rm dev pytest src/portal/tests/core/test_purge_expired.py
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Storage Adapter holds no business rule. Application Core computes expiry times and passes `now`.
- Keep the port method names from `architecture.md`.
- Never build a path from unchecked input.
