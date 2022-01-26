# API Schema (Working Draft)

## Endpoints

-   `/users/`: Gets JSON dict of all users currently in the DB and their last known location

    ```json
    {
        "user_uuid": { // UUID will be a unique 12-character Base64 string for each user
            "macaddr": "mac address", // Device mac address
            "fakename": "fake username generated for this UUID", // John Smith or whatever
            "position": [latitude, longitude], // Position of device
            "esps": [ // List of ESP nodes that are tracking the user
                {
                    "name": "ESP name", // Name of ESP
                    "position": [latitude, longitude] // Position of ESP
                }, ...
            ],
            "misc_data": { // Other data (device model, etc) that may not be uniform for each device
                "example_data_type": {
                    "display_name": "Example Type",
                    "value": "Example Value"
                }, ...
            }
        }, ...
    }
    ```

-   `/users/uuid/{uuid}/`: Get JSON data of a single user based on UUID, if the user exists

    ```json
    { // UUID will be a unique 12-character Base64 string for each user
        "macaddr": "mac address", // Device mac address
        "fakename": "fake username generated for this UUID", // John Smith or whatever
        "position": [latitude, longitude], // Position of device
        "esps": [ // List of ESP nodes that are tracking the user
            {
                "name": "ESP name", // Name of ESP
                "position": [latitude, longitude] // Position of ESP
            }, ...
        ],
        "misc_data": { // Other data (device model, etc) that may not be uniform for each device
            "example_data_type": {
                "display_name": "Example Type",
                "value": "Example Value"
            }, ...
        }
    }
    ```

-   `/users/esp/{esp_name}`: Gets all users tracked by ESP

    ```json
    {
        "user_uuid": { // UUID will be a unique 12-character Base64 string for each user
            "macaddr": "mac address", // Device mac address
            "fakename": "fake username generated for this UUID", // John Smith or whatever
            "position": [latitude, longitude], // Position of device
            "esps": [ // List of ESP nodes that are tracking the user
                {
                    "name": "ESP name", // Name of ESP
                    "position": [latitude, longitude] // Position of ESP
                }, ...
            ],
            "misc_data": { // Other data (device model, etc) that may not be uniform for each device
                "example_data_type": {
                    "display_name": "Example Type",
                    "value": "Example Value"
                }, ...
            }
        }, ...
    }
    ```
