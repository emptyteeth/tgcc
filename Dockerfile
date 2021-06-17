FROM python:3-alpine
LABEL org.opencontainers.image.source=https://github.com/emptyteeth/tgcc
WORKDIR /
COPY tgcc.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER nobody
ENTRYPOINT ["/usr/local/bin/python", "tgcc.py"]
