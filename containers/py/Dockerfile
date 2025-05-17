FROM ghcr.io/astral-sh/uv:debian-slim
MAINTAINER "Arjun Guha <a.guha@northeastern.edu>"

RUN apt-get update && apt-get install -y --no-install-recommends build-essential

COPY requirements.txt /requirements.txt

# TensorFlow does not support Python 3.10 as of May 14 2025.
RUN uv venv -p 3.10 /venv
RUN . /venv/bin/activate && uv pip install -r /requirements.txt

COPY driver.py /driver.py
COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["/venv/bin/python3", "/entrypoint.py"]