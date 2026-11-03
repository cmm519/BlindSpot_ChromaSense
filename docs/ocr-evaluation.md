# Text recognition evaluation

## Selected engine

**RapidOCR** (`rapidocr-onnxruntime` 1.4.4) is the one local text recognition engine that ChromaSense ships. It was more than 5 points more correct than Tesseract, and it fits SRS-NFR-041.

## Labeled set

The set is `src/color_engine/tests/data/labeled/`, with its expected text in `labels.json`. It has 11 generated images that contain text (4 charts, 3 maps, and 4 flat graphics), with 55 expected lines, and 3 photographs that the text comparison does not use.

**This set is generated and small, and all of its text uses one font.** Increment 28 needs the team's real labeled set to report SRS-NFR-042.

A line counts as correct when it matches an expected line after normalizing case and whitespace.

## Results

Timings ran in the `dev` container with the 4 CPU reference limit, on one chart enlarged to 12 megapixels. The timing covers text recognition only.

| Engine and settings | Correct lines | Percent correct | Lines not expected | Time at 12 megapixels |
| --- | --- | --- | --- | --- |
| RapidOCR defaults | 53 of 55 | 96.4 | 2 | 4.9 to 7.5 seconds |
| Tesseract, sparse text (`--psm 11`), adaptive threshold, 2x | 47 of 55 | 85.5 | 3 | 2.6 seconds |
| Tesseract, sparse text, no threshold, 2x | 43 of 55 | 78.2 | 2 | not timed |
| Tesseract, sparse text, adaptive threshold, 1x | 43 of 55 | 78.2 | not recorded | 0.6 seconds |
| Tesseract, sparse text, adaptive threshold, 3x | 41 of 55 | 74.5 | not recorded | not timed |
| Tesseract, automatic layout (`--psm 3`), adaptive threshold, 2x | 26 of 55 | 47.3 | 10 | not timed |
| Tesseract, single block (`--psm 6`), no threshold, 2x | 23 of 55 | 41.8 | 9 | not timed |

The filter that ships adds one step to the engine's output: it rejoins a line that the engine split at a word gap, because one piece is one line. With that step it still scores 53 of 55 lines, with 2 lines not expected. The 2 missed lines are `Monthly Temperature` and `Store Hours`.

The engine can still misread text. On white text on a blue background, it read `Revenue by Region` as `Revenue by f Region`. This is why each text item stays unverified until an AI read agrees with it.

## Selection rule

Keep Tesseract unless RapidOCR is at least 5 points more correct and still fits SRS-NFR-041. RapidOCR is 10.9 points more correct than the best Tesseract setting. Its time leaves room in the 10 second limit, which increment 27 measures for the whole local analysis.

## Constraints checked

- **No network**: the models ship inside the package, and its Python code opens no connection. The filter test runs in a container with no network.
- **No environment variables**: the package's Python code reads none.
- **One engine**: Tesseract and `pytesseract` are removed from every image target and from `pyproject.toml`.
- **Headless OpenCV**: `rapidocr-onnxruntime` declares `opencv-python`, which conflicts with `opencv-python-headless` and needs `libGL`. The `Dockerfile` installs it with `--no-deps`, and `src/color_engine/pyproject.toml` lists its other runtime dependencies. Because of this, the package name is not in `pyproject.toml`, so an install outside the Docker image must add it the same way.
- **Language**: the bundled models are the Chinese and English PP-OCRv4 models. This release only targets English, so a noisy image could produce a non-English line.
