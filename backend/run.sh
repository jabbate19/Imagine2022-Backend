# Setup virutal env
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Set environment vars
# Set mongodb conf
export MONGO_HOST="mongodb://tide.csh.rit.edu" # host:port or host
export MONGO_DB="imagine2022" # imagine2022 probably
export MONGO_USER="USERNAME HERE"
export MONGO_PASS="PASSWORD HERE"
export MONGO_SSL="yes" # Or no
export MONGO_FRAMES_COLLECTION="test_frames" # Collection to pull frames from
export MONGO_ESP_COLLECTION="test_esps" # Collection to pull ESP positions from
export MONGO_OUTPUT_COLLECTION="test_output" # Collection to output beacon positions to
export MONGO_COMMAND_COLLECTION="test_command" # Collection to store running config (which beacons are active, etc)

# Set triangulation parameters
export TRIANGULATION_ZERO="43.084587,-77.6742849" # lat,lon - (0, 0) point to get meter positions from
export TRIANGULATION_ENV_FACTOR="3" # Environmental factor
export TRIANGULATION_ONE_METER_RSSI="-62.5" # 1-meter RSSI of the beacons when detected by the ESPs in an ideal environment
export TRIANGULATION_TIMESTAMP_OVERRIDE="1645563358" # If included, this will be used as the constant time (testing only)

# Run API
uvicorn --no-access-log --reload --host=127.0.0.1 --port=8000 main:app