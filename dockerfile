FROM alpine:latest

WORKDIR /app

ARG PYTHON_VERSION=3.13.1

RUN apk add --update python3 py3-pip py3-requests py3-beautifulsoup4 py3-tqdm py3-colorama
RUN pip install --no-cache-dir --break-system-packages EbookLib

COPY mkepub.py .


