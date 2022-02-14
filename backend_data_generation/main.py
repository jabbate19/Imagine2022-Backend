from pymongo import MongoClient
import json
import random
import math
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import threading
import time
from argparse import ArgumentParser
import hashlib

def generate_mac():
    return ":".join("%02x" % random.randint(0, 255) for x in range(6))


def get_distance(pos1, pos2):  # The haversine function
    """
    Get meter distance between lat/lon 1 and lat/lon 2
    https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters - JS implementation
    """
    R = 6378.137  # Radius of the earth in KM
    dlat = pos2[0] * math.pi / 180 - pos1[0] * math.pi / 180
    dlon = pos2[1] * math.pi / 180 - pos1[1] * math.pi / 180
    a = math.pow(math.sin(dlat / 2), 2) + math.cos(pos1[0] * math.pi / 180) * math.cos(
        pos2[0] * math.pi / 180
    ) * math.pow(math.sin(dlon / 2), 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c
    return abs(d * 1000)  # Meters


class Geofence:
    def __init__(self, *vertices):
        self.vertices = vertices
        self.poly = Polygon(self.vertices)
        self.bounds = self.poly.bounds

    def check_inside(self, x: float, y: float):
        return self.poly.contains(Point(x, y))

    def random_point(self):
        while True:
            x = random.uniform(self.bounds[0], self.bounds[2])
            y = random.uniform(self.bounds[1], self.bounds[3])
            if self.check_inside(x, y):
                return x, y


# The entire campus
"""GEOFENCE = Geofence(
    (43.092327, -77.679133),
    (43.092637, -77.653776),
    (43.083232, -77.658793),
    (43.083120, -77.665875),
    (43.079003, -77.681400),
    (43.082734, -77.686674),
)"""

# Smol area for testing
GEOFENCE = Geofence(
    (43.087631, -77.679164),
    (43.087689, -77.674476),
    (43.084588, -77.674325),
    (43.083906, -77.679396)
)

# Formula: 10 ^ ((Measured Power – RSSI)/(10 * N))
class RSSIDist:
    N_VALUE = 3
    MEASURED_POWER = (
        -62.5
    )  # https://github.com/neXenio/BLE-Indoor-Positioning/wiki/RSSI-Measurements

    @classmethod
    def distance(cls, rssi):
        return 10 ** ((cls.MEASURED_POWER - rssi) / (10 * cls.N_VALUE))

    @classmethod
    def rssi(cls, dist):
        return (math.log10(dist) * (10 * cls.N_VALUE) - cls.MEASURED_POWER) * -1


class Beacon:
    def __init__(self, bid: str, geofence: Geofence):
        self.bid = bid
        self.geofence = geofence
        self.x, self.y = self.geofence.random_point()
        self.speed = random.uniform(0.000002, 0.000008)
        self.d = random.uniform(0, 2 * math.pi)

    def move(self):
        while True:
            self.d += random.uniform(-0.25 * math.pi, 0.25 * math.pi)
            if self.d > 2 * math.pi:
                self.d = self.d - 2 * math.pi
            elif self.d < 0:
                self.d = abs(self.d)

            self.speed += random.uniform(-0.000001, 0.000001)
            self.speed = min(0.000009, max(0.000001, self.speed))

            self.x += self.speed * math.cos(self.d)
            self.y += self.speed * math.sin(self.d)
            if self.geofence.check_inside(self.x, self.y):
                return
            else:
                self.x -= self.speed * math.cos(self.d)
                self.y -= self.speed * math.sin(self.d)


class Beacons:
    def __init__(self, num_beacons: int, geofence: Geofence):
        self.beacons = [
            Beacon(
                hashlib.sha256(random.randbytes(8)).hexdigest()[:8], geofence
            )
            for b in range(num_beacons)
        ]

    def step(self):
        [i.move() for i in self.beacons]


class Simulator:
    def __init__(
        self, num_esps: int, num_beacons: int, geofence: Geofence, sweep_interval: float
    ) -> None:
        self.esps = [
            ESP(i + 1, geofence, sweep_interval, self) for i in range(num_esps)
        ]
        self.beacons = Beacons(num_beacons, geofence)
        self.geofence = geofence
        self.frames = []
        self.moveint = sweep_interval / 2

    def simulate(self, _time: float, out: str):
        start = time.time()
        [e.start(_time) for e in self.esps]
        while time.time() < start + _time + 2:
            self.beacons.step()
            time.sleep(self.moveint)

        with open(out, "w") as f:
            json.dump(self.frames, f, indent=4)


class ESP:
    detection_distance = 15  # Meter distance to detect out to

    def __init__(
        self, eid: int, geofence: Geofence, sweep_interval: float, sim: Simulator
    ):
        self.eid = eid
        self.x, self.y = geofence.random_point()
        self.sweep = sweep_interval
        self.sim = sim

    def start(self, _time: float):
        t = threading.Thread(target=self.run, args=[_time])
        t.start()

    def run(self, _time: float):
        start = time.time()
        while time.time() < start + _time:
            for b in self.sim.beacons.beacons:
                dist = get_distance((b.x, b.y), (self.x, self.y))
                if dist <= self.detection_distance:
                    frame = {
                        "time": time.time(),
                        "eid": self.eid,
                        "bid": b.bid,
                        "rssi": RSSIDist.rssi(dist),
                        "_test_distance": dist,
                        "_test_epos": [self.x, self.y],
                        "_test_bpos": [b.x, b.y],
                    }
                    self.sim.frames.append(frame)
            time.sleep(self.sweep)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--esp", type=int, default=30)
    parser.add_argument("--beacon", type=int, default=150)
    parser.add_argument("--time", type=int, default=120)
    parser.add_argument("--sweep", type=float, default=1)
    parser.add_argument("--file", type=str, default="out.json")
    parser.add_argument("--mongohost", type=str, default="mongodb://tide.csh.rit.edu")
    parser.add_argument("--mongouser", type=str)
    parser.add_argument("--mongopassword", type=str)
    parser.add_argument("--mongodb", type=str)

    args = parser.parse_args()
    cli = MongoClient(host=args.mongohost+"/"+args.mongodb, username=args.mongouser, password=args.mongopassword, tls=True)
    sim: Simulator = Simulator(args.esp, args.beacon, GEOFENCE, args.sweep)
    sim.simulate(args.time, args.file)
    cli[args.mongodb]["test_frames"].insert_many(sim.frames)
    cli[args.mongodb]["test_esps"].insert_many([{
        "id": e.eid,
        "position": [e.x, e.y]
    } for e in sim.esps])
    print("Done!")
