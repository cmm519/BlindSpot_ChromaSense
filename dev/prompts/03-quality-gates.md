# Increment 3: Lint, dependency rules, and CI

### Main rules

- Encode the inward dependency rule from `architecture.md` as import-linter contracts.
- After this increment, fix an outward import. Do not edit a contract to make it pass.
- Do not change GitHub repository settings. The team does that in increment 28.

### Header

- **Increment:** 3
- **Capability:** Lint, dependency rules, and CI
- **Status:** `CRITICAL`
- **Depends on:** `02-docker-and-dependencies.md`
- **Traces to:** Quality stack in `architecture.md`; `ci.yml` row in `structure.md`
- **SRS IDs:** **SRS-NFR-029**, **SRS-NFR-030**, **SRS-NFR-031** (part; finished in increment 28)

### Requirements

- **SRS-NFR-029** (must): The codebase shall follow the architecture documented in `architecture.md`. (NFR-7.2)
- **SRS-NFR-030** (must): The codebase shall follow consistent style rules. (NFR-7.2)
- **SRS-NFR-031** (must): Every pull request shall pass automated builds and tests before merging. (NFR-7.3)

### Capability

Ruff, import-linter, and a pull request workflow enforce the style and dependency rules on the whole codebase.

### What may change

Add tool settings to `src/portal/pyproject.toml`. Add a Ruff `extend` setting to `src/color_engine/pyproject.toml`. Create `.github/workflows/ci.yml`.

### What must stay

The image targets from increment 2 stay as they are. Add no application behavior.

### Implementation notes

- **Ruff**: settings live in `src/portal/pyproject.toml`. There is no root `pyproject.toml`, so `src/color_engine/pyproject.toml` needs `[tool.ruff] extend = "../portal/pyproject.toml"`, or files under it get Ruff defaults.
- **import-linter** in `src/portal/pyproject.toml`: `root_packages = ["chromasense", "color_engine"]`, `include_external_packages = true`. Write these contracts:
  - `chromasense.core` does not import `chromasense.web_api`, `chromasense.storage`, `chromasense.ai_gateway`, or `chromasense.main`.
  - `chromasense.core` does not import `fastapi`, `sqlite3`, or `httpx`.
  - `color_engine` does not import `chromasense`, `fastapi`, `httpx`, or `sqlite3`.
  - `chromasense.web_api`, `chromasense.storage`, and `chromasense.ai_gateway` do not import each other.
- **`ci.yml`**: on `pull_request`, run `docker compose build` and then each extra check from `structure.md` as written.

### Verification

Show each SRS observation in full:

- **SRS-NFR-029**: A review or import check finds no source dependency that breaks the rules in `architecture.md`.
- **SRS-NFR-030**: The configured linter and formatter checks pass on the whole codebase.

Show this part now. A later increment finishes the row:

- **SRS-NFR-031**: `.github/workflows/ci.yml` runs each check from `structure.md` on pull requests. The team enables the required check in increment 28.

Also confirm:

- Add a temporary `import fastapi` to `chromasense/core/__init__.py`. `lint-imports` must fail. Remove the line, and it must pass.

Run from the repository root:

```
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Risk

A contract that silently checks nothing. import-linter ignores external packages unless configured, and Ruff silently falls back to defaults for files outside the settings file's folder.

### How to recognize failure

`lint-imports` reports zero analyzed modules for a contract, the deliberate import passes, or `ruff check src/color_engine` applies different rules from `src/portal`.

### Isolation test

Run `lint-imports` alone against the empty packages, with one deliberate violation for each contract. Run `ruff check --show-settings` on one file in each package.

### Rollback

Return the tree to the state that **`prompts/02-docker-and-dependencies.md`** verified: undo every change this increment made to the paths under "What may change". Rerun the verification in **`prompts/02-docker-and-dependencies.md`**, and set this row to `rolled back` in **`prompts/tracking.md`**.

### Main rules again

- Encode the inward dependency rule from `architecture.md` as import-linter contracts.
- After this increment, fix an outward import. Do not edit a contract to make it pass.
- Do not change GitHub repository settings. The team does that in increment 28.
