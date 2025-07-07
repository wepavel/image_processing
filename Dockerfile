FROM python:3.10-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gdal-bin libgdal-dev \
      python3-dev build-essential \
      python3-pip && \
    rm -rf /var/lib/apt/lists/*

#RUN sed -i 's/^# *\(ru_RU.UTF-8\)/\1/' /etc/locale.gen && \
#    locale-gen && \
#    update-locale LANG=ru_RU.UTF-8

#ENV LANG=ru_RU.UTF-8 \
#    LANGUAGE=ru_RU:ru \
#    LC_ALL=ru_RU.UTF-8

WORKDIR /app

COPY requirements.txt .

RUN GDAL_VERSION=$(gdal-config --version) && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install --no-cache-dir "GDAL==${GDAL_VERSION}"

#COPY . .

WORKDIR /app/src
