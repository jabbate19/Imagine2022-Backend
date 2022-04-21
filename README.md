# Imagine2022-Backend

Guess what? It's in Flask now.

## Endpoints

`GET /beacons/locations` - Gets beacon locations most recent location

```json
{
  "beacon id": {
    "position": [x, y], // Normalized position in meters
    "absolute_position": [lat, lon], // GPS position of beacon
    "esps": {
      "esp id": {
        "timestamp": float unix time,
        "rssi": float value rssi,
        "esp_position": [lat, lon],
        "esp_position_normal": [x, y], // Normalized position in meters
        "distance": float distance in meters
      }, ...
    }
  }, ...
}
```

`GET /beacons/heartbeat?id=<mac_address>` - Gets time of last heartbeat from sniffer. OPTIONAL id parameter to only get heartbeat of one sniffer.

```json
{
    "SNIFFER_ID": "MM/DD/YYYY HH:MM:SS", // Times given in EDT
    ...
}
```

`POST /esp?id=<mac_address>&lat=<latitude>&lon=<longitude>` - Adds a new sniffer with mac address `id` at `(lat, lon)`.

```
## HTTP Status Codes

200 - Successfully added ESP
400 - Missing Parameters 
```

`POST /remove/esp?id=<mac_address>` - Removes sniffer with mac address `id`.

```
HTTP Status Codes

200 - Successfully removed ESP
400 - Missing Parameter
```

`POST /hide?id=<mac_address>` - Hides beacon with mac address `id`.

```
HTTP Status Codes

200 - Successfully removed ESP
400 - Missing Parameter
```

`POST /unhide?id=<mac_address>` - Unhides beacon with mac address `id`.

```
HTTP Status Codes

200 - Successfully removed ESP
400 - Missing Parameter
```
