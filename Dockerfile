FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir .

COPY web ./web
RUN mkdir -p /opt/ema-weights \
    && pip install --no-cache-dir huggingface_hub \
    && python -c "from huggingface_hub import hf_hub_download; \
d='/opt/ema-weights'; r='canberkkkkkk/ema-lightning'; \
hf_hub_download(r, 'ema.pt', local_dir=d); \
hf_hub_download(r, 'decoder.pt', local_dir=d)"

ENV EMA_WEIGHTS=/opt/ema-weights PORT=8000
EXPOSE 8000
CMD ["python", "web/server.py"]
