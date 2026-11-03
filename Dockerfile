FROM python:3.11-slim-bookworm AS base
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
# RapidOCR declares opencv-python, which conflicts with opencv-python-headless and needs libGL.
# Installing it with --no-deps keeps headless OpenCV. src/color_engine/pyproject.toml lists
# the rest of its runtime dependencies. docs/ocr-evaluation.md records why this engine is used.
RUN pip install --no-deps rapidocr-onnxruntime==1.4.4
WORKDIR /workspace

FROM base AS engine-test
COPY src/color_engine src/color_engine
RUN pip install "./src/color_engine[test]"
RUN pytest src/color_engine/tests

FROM base AS dev
COPY src src
RUN pip install -e "./src/color_engine[test]"
RUN pip install -e "./src/portal[test]"
RUN playwright install --with-deps chromium

FROM base AS runtime
COPY src src
RUN pip install ./src/color_engine
RUN pip install ./src/portal
CMD ["python", "-m", "chromasense.main"]
