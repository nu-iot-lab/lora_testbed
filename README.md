# LoRa testbed consisting of ESP32 devices

The testbed consists of 1-channel and 1-SF gateways which all together emulate a 1-channel / all SFs gateway (GW).
The hardware is based on commonly used LILYGO TTGO v1.2 and/or Heltec LoRa v2.

## Features
* 2 receive windows (RW), 1 and 2 seconds after the uplink
* 1% and 10% duty cycle for RW1 and RW2, respectively (for the entire emulated GW)
* Configurable ED/GW and experiment settings
* Experiment initialization and statistics collection script
* Over-the-air updates for all EDs and GWs using webrepl (over wifi)

## Setup
* The router's DHCP must be configured to give static IPs to the GWs and EDs.
* assets.txt can be used to feed the devices with specific settings
* The initiator script can be used on a PC to initiate an experiment with the devices listed in assets.txt
* Port 8001 is used to communicate between the NS and the GWs
* Port 8002 is used for experiment initialization and statistics

`python3 init_exp_f.py -m U` will update all devices in assets.txt with the new main.py

`python3 init_exp_f.py -m C` will initiate a new experiment with the devices and settings in assets.txt

## Network achitecture
```
------------------    wifi   ----------
| Network Server |-----------| Router |
------------------           ----------
  192.168.0.230             192.168.0.1
                                 | 
                                 |wifi
                                 |
                                 |
--------------------------------------
|                                    |
|  ------------    LoRa    -------   |
|  | gateways |------------| EDs |   |
|  ------------            -------   |
|   192.168.0.x          192.168.0.x |
|                                    |
--------------------------------------
```

## LoRaWAN emulated architecture
```
                         Multi-SF Emulated GW (1ch)
                             ----------------
                             | SF7 Gateway  |
                             | SF8 Gateway  |
------------------    wifi   |              |   LoRa   -------
| Network Server |-----------|    ...       |----------| EDs |
------------------           |              |          -------
                             |              |
                             | SF12 Gateway |
                             ----------------
```
