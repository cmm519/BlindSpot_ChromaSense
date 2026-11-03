# Increment 6: Decode and downscale

### Main rules

- Keep the names `decode_1(data: bytes)` -> `DecodedImage1` and `downscale_2(image, max_megapixels)` -> `AnalysisImage2`.
- No filter calls another filter.
- Do not enable loading of truncated images.

### Header

- **Increment:** 6
- **Capability:** Decode and downscale
- **Status:** `Standard`
- **Depends on:** `04-color-rules.md`
- **Traces to:** Filters 1 and 2 in `architecture.md`
- **SRS IDs:** **SRS-FR-005**, **SRS-FR-004** (part; finished in increment 20), **SRS-FR-006** (part; finished in increment 14), **SRS-FR-007** (part; finished in increment 20)

### Requirements

- **SRS-FR-005** (must): The system shall convert embedded color profiles in uploaded images to sRGB. (Section 3.3)
- **SRS-FR-004** (must): The system shall accept PNG, JPEG, HEIC, and WEBP images. (FR-1.4)
- **SRS-FR-006** (must): The system shall downscale images larger than 12 megapixels for analysis while preserving the original for export. (FR-1.5)
- **SRS-FR-007** (must): The system shall display an error message for unsupported or corrupted files. (FR-1.6)

### Capability

Uploaded bytes become an sRGB pixel array, and a separate analysis copy of at most 12 megapixels.

### What may change

`pipeline/filter_1_decode/decode_1.py`, `pipeline/filter_2_downscale/downscale_2.py`, output classes in `models.py`, `tests/pipeline/test_filter_1_decode.py`, `tests/pipeline/test_filter_2_downscale.py`, and `tests/data/`.

### What must stay

`rules/` stays as earlier increments left it.

### Implementation notes

- **`derived`**: `DecodedImage1(pixels, width, height)`, `AnalysisImage2(pixels, width, height, scale)`, and `ImageDecodeError(ValueError)` in `models.py`.
- **`decode_1`**: register `pillow_heif.register_heif_opener`, open with `PIL.Image.open`, accept only formats PNG, JPEG, HEIF, and WEBP, apply `ImageOps.exif_transpose`, convert an embedded profile with `ImageCms.profileToProfile` to `ImageCms.createProfile("sRGB")`, and return 3-channel RGB `uint8`.
- **`derived`**: treat an image with no profile as sRGB. Flatten alpha onto white. Use the first frame of an animated WEBP. Raise `ImageDecodeError` for `UnidentifiedImageError`, `OSError`, and `DecompressionBombError`.
- **`downscale_2`**: `Image.resize` with `Image.Resampling.LANCZOS`, preserving aspect ratio. An image already within the limit is returned at its own size and is never enlarged.
- **Display P3 fixture**: commit a Display P3 ICC profile in `tests/data/`, built from the published primaries. Use an in-gamut color and compute the expected sRGB value independently. Allow a tolerance of 2 levels.

### Verification

Show each SRS observation in full:

- **SRS-FR-005**: A test image with an embedded Display P3 profile decodes to the expected sRGB pixel values.

Show this part now. A later increment finishes the row:

- **SRS-FR-004**: `decode_1` decodes one sample file each of PNG, JPEG, HEIC, and WEBP.
- **SRS-FR-006**: `downscale_2` returns at most 12 megapixels for a 20 megapixel input and does not alter the decoded input.
- **SRS-FR-007**: `decode_1` raises `ImageDecodeError` for a text file renamed as PNG and for a truncated JPEG.

Run from the repository root:

```
docker compose run --rm dev pytest src/color_engine/tests/pipeline/test_filter_1_decode.py src/color_engine/tests/pipeline/test_filter_2_downscale.py
docker build --target engine-test .
docker compose run --rm dev ruff check .
docker compose run --rm dev ruff format --check .
docker compose run --rm dev lint-imports --config src/portal/pyproject.toml
```

### Main rules again

- Keep the names `decode_1(data: bytes)` -> `DecodedImage1` and `downscale_2(image, max_megapixels)` -> `AnalysisImage2`.
- No filter calls another filter.
- Do not enable loading of truncated images.
