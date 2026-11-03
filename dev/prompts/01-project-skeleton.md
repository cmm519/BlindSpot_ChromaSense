# Increment 1: Project skeleton

### Main rules

- Treat the tree root `ChromaSense/` in `structure.md` as the repository root. Leave `dev/` and `archive/` as they are.
- Create folders, package markers, and package definitions only. Write no application behavior.
- Use only the paths in the `structure.md` tree.

### Header

- **Increment:** 1
- **Capability:** Project skeleton
- **Status:** `Standard`
- **Depends on:** none
- **Traces to:** Directory tree and ownership table in `structure.md`
- **SRS IDs:** **SRS-NFR-027** (part; finished in increment 2)

### Requirements

- **SRS-NFR-027** (must): The color engine shall be a separate Python package. (NFR-7.1)

### Capability

The repository has the top-level files and the two Python package folders from the tree, and both packages can be compiled.

### What may change

Create `.dockerignore`, `.env.example`, `README.md`, `src/color_engine/pyproject.toml`, `src/portal/pyproject.toml`, and each `__init__.py` in the tree. Add project entries to `.gitignore` only if a generated file would otherwise be tracked.

### What must stay

`AGENTS.md`, `dev/`, and `archive/` stay as they are. Do not create a root `pyproject.toml`, because the tree has none.

### Implementation notes

- Create every `__init__.py` that the tree lists. `web_ui/` has none, because it is not a Python package.
- **`src/color_engine/pyproject.toml`**: package name `color_engine`, Python `>=3.11`, package data `data/*`. List no dependency yet.
- **`src/portal/pyproject.toml`**: package name `chromasense`, Python `>=3.11`, dependency on `color_engine`, package data for `web_ui/**/*`, `storage/schema.sql`, and `ai_gateway/read_schema.json`.
- **`.dockerignore`**: exclude `.git/`, `dev/`, `archive/`, `.env`, and Python caches.
- **`.env.example`** (`derived` names, no real values): `CHROMASENSE_PROVIDER_URL`, `CHROMASENSE_API_KEY`, `CHROMASENSE_MODEL`, `CHROMASENSE_RETENTION_HOURS`, `CHROMASENSE_CONFUSION_THRESHOLD`, `CHROMASENSE_RATE_LIMIT_SESSION`, `CHROMASENSE_RATE_LIMIT_IP`, `CHROMASENSE_RATE_WINDOW_SECONDS`, `CHROMASENSE_SPEND_CAP`, `CHROMASENSE_COST_PER_REQUEST`, `CHROMASENSE_PURGE_INTERVAL_SECONDS`, `CHROMASENSE_DATA_DIR`.
- **`README.md`**: a title and one sentence. Increment 16 writes the setup guide.

### Verification

Show this part now. A later increment finishes the row:

- **SRS-NFR-027**: `src/color_engine/` exists as its own package folder with its own `pyproject.toml`.

Also confirm:

- Each path that this increment names exists, and `git status` shows no change in `dev/` or `archive/`.

Run from the repository root:

```
python3 -m compileall src
```

### Main rules again

- Treat the tree root `ChromaSense/` in `structure.md` as the repository root. Leave `dev/` and `archive/` as they are.
- Create folders, package markers, and package definitions only. Write no application behavior.
- Use only the paths in the `structure.md` tree.
