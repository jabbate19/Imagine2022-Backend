import json
from utilities import Triangulator
import math

def dist(p1, p2):
    return abs(
        math.sqrt(
            (p1[0] - p2[0]) ** 2
            + (p1[1] - p2[1]) ** 2
        )
    )

with open("test_params.json", "r") as f:
    data = json.load(f)

T = Triangulator(*data["args"], **data["kwargs"])

dat = T.aggregate(data["start_time"], bounds=2.5)
print("\n".join([f"{k}: {v['position']}: {dist(v['position'], v['testpos'])} meter error" for k, v in dat.items()]))
print(len(dat))