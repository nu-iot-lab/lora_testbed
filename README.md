# LoRa testbed consisting of ESP32 devices

The testbed consists of 1-channel and SF gateways which all together emulate a single channel / all SFs gateway (GW) with the help of Network Server.
The hardware is based on LILYGO TTGO v1.2 and/or Heltec LoRa v2.

## Features
* 2 receive windows (RW), 1 and 2 seconds after the uplink
* 1% and 10% duty cycle for RW1 and RW2, respectively (for the entire emulated GW)
* Configurable ED/GW and experiment settings
* Experiment initialization and statistics collection script
* Over-the-air updates for all EDs and GWs using webrepl (over wifi)

## Setup
* The router's DHCP must be configured to give the same IP to specific MAC addresses.
* assets.txt can be used to feed the devices with specific settings
* The initiator script can be used on a PC to initiate an experiment with the devices listed in assets.txt

`python3 init_exp_f.py -m U` will update all devices in assets.txt with the new main.py

`python3 init_exp_f.py -m C` will initiate a new experiment with the devices and settings in assets.txt

## Network achitecture
```
------------------    wifi   ----------
| Network Server |-----------| Router |
------------------           ----------
  192.168.1.230             192.168.1.1
                                 | 
                                 |wifi
                                 |
                                 |
--------------------------------------
|                                    |
|  ------------    LoRa    -------   |
|  | gateways |------------| EDs |   |
|  ------------            -------   |
|   192.168.1.x          192.168.1.x |
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
