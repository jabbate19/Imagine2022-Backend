from pymongo import MongoClient
from pymongo.collection import Collection
from fastapi import FastAPI, Response, Request, status
from fastapi_restful.tasks import repeat_every
import os
import time
from utilities import Triangulator

if __name__ == "__main__":
    raise RuntimeError("This api should not be run directly, run using ./run.sh or containerization")

app = FastAPI()

# Load configuration
mongo = MongoClient(
    host=f'{os.environ.get("MONGO_HOST")}/{os.environ.get("MONGO_DB")}',
    username=os.environ.get("MONGO_USER"),
    password=os.environ.get("MONGO_PASS"),
    tls=os.environ.get("MONGO_SSL") == "yes",
)

frames: Collection = mongo[os.environ.get("MONGO_DB")][
    os.environ.get("MONGO_FRAMES_COLLECTION")
]
esps: Collection = mongo[os.environ.get("MONGO_DB")][
    os.environ.get("MONGO_ESP_COLLECTION")
]
output: Collection = mongo[os.environ.get("MONGO_DB")][
    os.environ.get("MONGO_OUTPUT_COLLECTION")
]
command: Collection = mongo[os.environ.get("MONGO_DB")][
    os.environ.get("MONGO_COMMAND_COLLECTION")
]

triangulator = Triangulator(
    float(os.environ.get("TRIANGULATION_ENV_FACTOR")),
    float(os.environ.get("TRIANGULATION_ONE_METER_RSSI")),
    [float(i) for i in os.environ.get("TRIANGULATION_ZERO").split(",")],
    mongo_client=mongo,
    mongo_database=os.environ.get("MONGO_DB"),
    mongo_frames_collection=os.environ.get("MONGO_FRAMES_COLLECTION"),
    mongo_esp_collection=os.environ.get("MONGO_ESP_COLLECTION"),
    mongo_output_collection=os.environ.get("MONGO_OUTPUT_COLLECTION")
)

_ovr = os.environ.get("TRIANGULATION_TIMESTAMP_OVERRIDE", default="no")
TIME_OVERRIDE: float = float(_ovr) if _ovr != "no" else False

@app.on_event("startup")
@repeat_every(seconds=5)
def update_beacon_positions():
    triangulator.run_once(TIME_OVERRIDE if TIME_OVERRIDE else (time.time() - 2.5), bounds=2.5)

@app.get("/beacons/locations", status_code=200)
async def get_beacons():
    res = output.find()
    return {i["beacon_id"]: {k: v for k, v in i.items() if not k in ["_id", "testpos"]} for i in res}

@app.get("/config/zero", status_code=200)
async def get_zero():
    return triangulator.zero_zero

@app.post("/esp", status_code=201)
async def new_esp(id: str, lat: str, lon: str):
    triangulator.add_esp([float(lat), float(lon)], id)
    return {}

@app.post("/remove/esp", status_code=200)
async def remove_esp(id: str, response: Response):
    response.status_code = 200 if triangulator.remove_esp(id) else 404
    return {}
