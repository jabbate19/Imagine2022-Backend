# Data Format Specification

_This document refers specifically to the data being stored in MongoDB. Data pre-ingest is irrelevant to this document._

**Frame Data**
Frame data is raw data post-ingest. It should follow the below spec. Each frame represents **one** detection of **one** beacon by **one** ESP.

```json
{
    "time": float - Detection timestamp,
    "eid": ID of ESP (unique int or str),
    "bid": ID of beacon (unique int or str),
    "rssi": float - RSSI data
}
```

-   Frames could be encoded with a set packet length and set field length coming from the ESPs, as all of these data can be a set length.
-   This format works with constant sweeps or interval sweeps
-   EID and BID can be inserted along with the ESP/Beacon code when we install them, and then placed on a QR code or label on the outside for ease of use.

**ESP Data**
ESP position data linked to ESP ID, so that position doesn't actually need to be known by ESPs or Beacons.

```json
{
    "id": str/int - ESP ID, unique and matched to those in frame data,
    "position": list[float] - GPS position of each ESP. Should be as accurate as possible
}
```

-   Ideally the workflow is the following for each ESP:
    -   Place ESP
    -   Scan QR code/get ID from label
    -   Enter current position
    -   Sent result to DB
-   Entering ESPs into the DB could be easily automated if we add an extra part to the frontend for it, you'd just need to scan the code and then your device would send GPS position data along with the ESP id to the database. We could also do this manually if we want to make sure we have the best position data, if we use a good GPS

**Aggregated Data**
Calculated positions of each beacon based on triangulation

```json
{
    "timestamp": float - time of calculation,
    "beacons": { //Detected becons
        "beacon id": {
            "position": lat/lon,
            "esps": list[int/str] - List of ESP ids that detected it
        }
    }
}
```

-   One of these would be posted to the DB every calculation cycle. It would calculate position based on RSSI from multiple ESPs.
-   These calculations are implemented in backend_data_generation/main.py, but the relevant formula is listed below:
    -   RSSI/Distance calculation
        -   `10 ^ ((Measured Power – RSSI)/(10 * N))` for RSSI -> Distance
        -   Measured Power is the measured RSSI at 1 meter from the device
        -   N is the environmental factor around RIT. We can derive this from the other values, but it should be between 2 and 4
