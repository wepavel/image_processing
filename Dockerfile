FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.1

RUN apt update \
    && apt install python3-pip -y \
    && ln -sf /usr/bin/* /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY src/ /app/src
COPY config.yaml /config.yaml

WORKDIR /app/src

CMD ["python3", "app.py"]