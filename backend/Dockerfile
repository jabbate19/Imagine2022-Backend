FROM python:3.10.2
WORKDIR /usr/src/app

# MongoDB setup
ENV MONGO_HOST="mongodb://tide.csh.rit.edu"
ENV MONGO_DB="imagine2022"

# Add MONGO_USER and MONGO_PASS for auth

ENV MONGO_SSL="yes"
# Set in OKD [VVV]
# ENV MONGO_FRAMES_COLLECTION="test_frames"
# ENV MONGO_ESP_COLLECTION="test_esps"
# ENV MONGO_OUTPUT_COLLECTION="test_output"
# ENV MONGO_COMMAND_COLLECTION="test_command"

# Set triangulation parameters
# ENV TRIANGULATION_ZERO="43.084587,-77.6742849"
# ENV TRIANGULATION_ENV_FACTOR="3"
# ENV TRIANGULATION_ONE_METER_RSSI="-62.5"
# ENV TRIANGULATION_TIMESTAMP_OVERRIDE="1645563358"

COPY *.py .
COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD uvicorn --no-access-log --host=0.0.0.0 --port=8000 main:app