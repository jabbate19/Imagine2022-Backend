# Imagine2022-Backend
Imagine, nay, CONSIDER RIT

## Endpoints
`https://imagine-2022-backend-git-imagine2022-backend.apps.okd4.csh.rit.edu/beacons/locations` - Gets beacon locations most recently

```json
{
  "beacon id": {
    "position": [x, y] // Normalized position in meters (turns out this doesn't give GPS coord anymore, will fix @spencer
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

`https://imagine-2022-backend-git-imagine2022-backend.apps.okd4.csh.rit.edu/config/zero` - Gets lat/lon of (0, 0) on campus. Returns list of `[lat, lon]`
