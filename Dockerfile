FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY openworld_methane ./openworld_methane
COPY examples ./examples
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install .

FROM python:3.11-slim AS runtime

ENV VIRTUAL_ENV=/venv
ENV PATH="/venv/bin:$PATH"
WORKDIR /app
COPY --from=builder /venv /venv
COPY examples ./examples
COPY config.example.toml ./config.example.toml
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["owm"]
CMD ["--help"]

