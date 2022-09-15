# gve_devnet_people_counting_live_occupancy
People counting and live occupancy solution for Meraki.


## Contacts
* Roaa Alkhalaf
* Stien Vanderhallen

## Solution Components
* Meraki MV Camera
* Python 3.8
* MQTT Broker


## Installation/Configuration


 
## Setup

Add Meraki API Key, Network ID and Camera Serial to the env_var.py file.

```python
MERAKI_API_KEY= " "
NETWORK_ID = " "
CAMERA_SERIAL = " "

```

**_MQTT Setup:_**

In the Meraki dashboard, go to the `Cameras` > `[Camera Name]` > `Settings` > `Sense` page.

Click to `Add` or `Edit` `MQTT Brokers` > `New MQTT Broker` and add you broker information.

Add the MQTT Server settings to the `env_var.py` file:

```python
MQTT_SERVER = " "
MQTT_PORT = None #Please note: integer
```

## Usage

# Screenshots
![/IMAGES/0image.png](/IMAGES/0image.png)
(Screenshot to be added!)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
