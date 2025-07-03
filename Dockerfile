FROM python:3.11.3-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    libgl1-mesa-glx \
    cmake \
    g++ \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libpq-dev \
    libreoffice \
    supervisor \
    redis-server \
    pkg-config \
    libcairo2-dev \
    build-essential \
    ffmpeg \
    poppler-utils \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN pip install --no-cache-dir pycairo==1.27.0

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV MAX_JOBS=2
RUN pip install --no-cache-dir --no-build-isolation dlib
RUN pip install --no-cache-dir face_recognition redis

RUN python -c "import whisper; print('Descargando modelo Whisper medium...'); whisper.load_model('medium'); print('Descarga completa.')"

COPY . .

EXPOSE 3100 3101

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]