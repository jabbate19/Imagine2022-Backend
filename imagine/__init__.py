from flask import Flask, abort, request
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
import os
from pymongo import MongoClient
from pymongo.collection import Collection
from imagine.utilities import Triangulator
import time
import datetime
import pytz
from _thread import *

app = Flask(__name__)
auth = HTTPTokenAuth(scheme='Bearer')
CORS(app)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

tokens = {
    app.config["ADMIN_TOKEN"]: "admin",
}

mongo = MongoClient(
    host=f'{app.config["MONGO_HOST"]}/{app.config["MONGO_DB"]}',
    username=app.config["MONGO_USER"],
    password=app.config["MONGO_PASS"],
    tls=app.config["MONGO_SSL"],
)

frames: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_FRAMES_COLLECTION"]
]
esps: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_ESP_COLLECTION"]
]
output: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_OUTPUT_COLLECTION"]
]
command: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_COMMAND_COLLECTION"]
]
beacons: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_BEACON_COLLECTION"]
]
heartbeats: Collection = mongo[app.config["MONGO_DB"]][
    app.config["MONGO_HEARTBEAT_COLLECTION"]
]

triangulator = Triangulator(
    app.config["TRIANGULATION_ENV_FACTOR"],
    app.config["TRIANGULATION_ONE_METER_RSSI"],
    [float(i) for i in app.config["TRIANGULATION_ZERO"].split(",")],
    mongo_client=mongo,
    mongo_database=app.config["MONGO_DB"],
    mongo_frames_collection=app.config["MONGO_FRAMES_COLLECTION"],
    mongo_esp_collection=app.config["MONGO_ESP_COLLECTION"],
    mongo_output_collection=app.config["MONGO_OUTPUT_COLLECTION"]
)

_ovr = os.environ.get("TRIANGULATION_TIMESTAMP_OVERRIDE", default="no")
TIME_OVERRIDE: float = float(_ovr) if _ovr != "no" else False

@auth.verify_token
def verify_token(token):
    if token in tokens:
        return tokens[token]

@app.route('/beacons/locations', methods=['GET'])
def locations():
    res = output.find()
    out = {}
    for i in res:
        beacon_id = i["beacon_id"]
        beacon_find = beacons.find({"id": beacon_id})
        beacon_hidden = True
        for bool in beacon_find:
            if not bool["hidden"]:
                beacon_hidden = False
                break
        if not beacon_hidden:
            out[beacon_id] = {k: v for k, v in i.items() if not k in ["_id", "testpos"]}
    return out

@app.route('/beacons/heartbeat', methods=['GET'])
def get_heartbeats():
    args = request.args
    id = args.get("id")
    if id:
        res = heartbeats.find({"sniffaddr": id})
    else:
        res = heartbeats.find()
    out = {}
    for i in res:
        addr = i["sniffaddr"]
        if addr in out:
            if i["timestamp"] > out[addr]:
                out[addr] = i["timestamp"]
        else:
            out[addr] = i["timestamp"]
    for key in out:
        timestamp = datetime.datetime.fromtimestamp(out[key]-14400)
        out[key] = timestamp.strftime("%m/%d/%Y %H:%M:%S")
    return out

# @app.route("/config/zero", methods=['GET'])
# def get_zero():
#     return triangulator.zero_zero

@app.route("/esp", methods=['POST'])
@auth.login_required
def new_esp():
    args = request.args
    id = args.get("id")
    lat = args.get("lat")
    lon = args.get("lon")
    if not (id and lat and lon):
        abort(400)
    triangulator.add_esp([float(lat), float(lon)], id)
    return "OK", 200

@app.route("/remove/esp", methods=['POST'])
@auth.login_required
def remove_esp():
    args = request.args
    id = args.get("id")
    result = triangulator.remove_esp(id)
    if result:
        return "OK", 200
    return "ESP Not Found", 400

@app.route("/hide", methods=['POST'])
@auth.login_required
def hide_beacon():
    args = request.args
    id = args.get("id")
    beacons.update_one({"id": id}, {"$set": {"hidden": True}})
    return "OK", 200

@app.route("/unhide", methods=['POST'])
@auth.login_required
def unhide_beacon():
    args = request.args
    id = args.get("id")
    beacons.update_one({"id": id}, {"$set": {"hidden": False}})
    return "OK", 200

def update_constant():
    while True:
        triangulator.run_once(TIME_OVERRIDE if TIME_OVERRIDE else (time.time() - 2.5), bounds=2.5)
        time.sleep(5)

start_new_thread(update_constant, ())