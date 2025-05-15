FROM kalilinux/kali-rolling

RUN apt-get update && apt-get install -y \
    bluetooth \
    bluez \
    python3-pip \
    python3-venv \
    sqlite3 \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install bleak

WORKDIR /opt/ble-logger
COPY ble_logger.py .

ENV SENSOR_ID="KaliPi1"

CMD ["sh", "-c", "while true; do python3 /opt/ble-logger/ble_logger.py; sleep 60; done"]
