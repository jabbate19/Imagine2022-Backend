from pymongo import MongoClient
from geopy.distance import geodesic
from triangulator import geo_triangulate, LatLong
import math


class Triangulator:
    def __init__(
        self,
        environmental_value: float,  # Environmental factor of RIT (should be between 2 and 5 i think, but we can derive it later)
        one_meter_rssi: float,  # RSSI of a beacon one meter from an ESP
        zero_zero: list[float],  # lat/lon position of (0, 0) to use as normalization
        mongo_host: str = "mongodb://tide.csh.rit.edu",  # MongoDB host
        mongo_user: str = None,  # MongoDB user
        mongo_password: str = None,  # MongoDB password
        mongo_ssl: bool = True,  # MongoDB SSL/TLS
        mongo_database: str = "imagine2022",  # MongoDB db name
        mongo_frames_collection: str = "frames",  # Raw frame collection name
        mongo_esp_collection: str = "esps",  # ESP position collection name
        mongo_output_collection: str = "positions",  # Collection to output to
        test: bool = False,
    ):
        self.N = environmental_value
        self.MEASURED_VALUE = one_meter_rssi
        self.zero_zero = zero_zero

        self.client = MongoClient(
            host=mongo_host + "/" + mongo_database,
            username=mongo_user,
            password=mongo_password,
            tls=mongo_ssl,
        )
        self.database = self.client[mongo_database]

        self.frames_collection = self.database[mongo_frames_collection]
        self.esp_collection = self.database[mongo_esp_collection]
        self.output_collection = self.database[mongo_output_collection]

        self.esps = {
            i["id"]: i["position"] for i in self.esp_collection.find(filter={})
        }

        self.lat_con = geodesic(
            zero_zero,
            [
                (zero_zero[0] + 1 if zero_zero[0] < 89 else zero_zero[0] - 1),
                zero_zero[1],
            ],
        ).meters
        self.lon_con = geodesic(
            zero_zero,
            [
                zero_zero[0],
                (zero_zero[1] + 1 if zero_zero[1] < 89 else zero_zero[1] - 1),
            ],
        ).meters

        self.test = test

    def _calc_distance(self, rssi):
        return 10 ** ((self.MEASURED_VALUE - rssi) / (10 * self.N))

    def _get_normalized_point(self, lat: float, lon: float) -> list[float]:
        return (lat - self.zero_zero[0]) * self.lat_con, (
            lon - self.zero_zero[1]
        ) * self.lon_con

    def _get_findable_beacons(self, timestamp, bounds):
        beacons = {}
        for frame in self.frames_collection.find(
            filter={"time": {"$lt": timestamp + bounds, "$gt": timestamp - bounds}}
        ):
            if not frame["bid"] in beacons.keys():
                beacons[frame["bid"]] = {
                    "position": None,
                    "esps": {},
                    "testpos": self._get_normalized_point(*frame["_test_bpos"])
                    if self.test
                    else None,
                }

            if (  # Giant condition to check if the new frame is more recent than an old one, if an old one exists
                frame["eid"] in beacons[frame["bid"]]["esps"].keys()
                and beacons[frame["bid"]]["esps"][frame["eid"]]["timestamp"]
                < frame["time"]
            ) or not frame[
                "eid"
            ] in beacons[
                frame["bid"]
            ][
                "esps"
            ].keys():
                beacons[frame["bid"]]["esps"][frame["eid"]] = {
                    "timestamp": frame["time"],
                    "rssi": frame["rssi"],
                    "esp_position": self.esps[frame["eid"]],
                    "esp_position_normal": self._get_normalized_point(
                        *self.esps[frame["eid"]]
                    ),
                    "distance": self._calc_distance(frame["rssi"]),
                }

        findable_beacons = {}
        for b, v in beacons.items():
            if len(v["esps"].keys()) >= 3:
                findable_beacons[b] = v.copy()

        return findable_beacons

    def _triangulate_position(self, edict1: dict, edict2: dict):
        return geo_triangulate(
            LatLong(*edict1["esp_position"]),
            edict1["distance"],
            LatLong(*edict2["esp_position"]),
            edict2["distance"],
        )

    def _calc_position(self, beacon: dict, threshold: float) -> list[float]:
        positions: list[list] = []
        for i, e1 in beacon["esps"].items():
            for j, e2 in beacon["esps"].items():
                if i != j:
                    locs = self._triangulate_position(e1, e2)
                    if locs:
                        positions.extend(
                            [
                                list(self._get_normalized_point(*[k.dlat, k.dlon]))
                                for k in locs
                            ]
                        )

        for p in range(len(positions)):
            for q in range(len(positions)):
                if p != q:
                    if len(positions[p]) == 2:
                        positions[p].append(0)
                    if (
                        abs(
                            math.sqrt(
                                (positions[p][0] - positions[q][0]) ** 2
                                + (positions[p][1] - positions[q][1]) ** 2
                            )
                        )
                        < threshold
                    ):
                        positions[p][2] += 1

        vals = sorted(
            [p for p in positions if len(p) > 2 and p[2] > 0],
            key=lambda x: x[2],
            reverse=True,
        )
        if len(vals) > 0:
            return tuple(vals[0][:2])
        else:
            return None

    def aggregate(self, timestamp: float, bounds: float = 5):
        findable_beacons = self._get_findable_beacons(timestamp, bounds)

        for b in findable_beacons.keys():
            findable_beacons[b]["position"] = self._calc_position(
                findable_beacons[b], 2.5
            )

        return findable_beacons
