# LoRa testbed consisting of ESP32 devices

## Features:
* Currently, the testbed consists of 1-channel gateways
* 2 receive windows, 1 and 2 seconds after the uplink
* 1% and 10% duty cycle for RX1 and RX2, respectively
* Over-the-air update using webrepl (over wifi)

## Setup:
* The router's DHCP must be configured to give the same IP to specific MAC addresses.
* assets.txt can be used to feed the devices with specific settings
* The initiator script can be used on a PC to initiate an experiment with the devices listed in assets.txt

`python3 init_exp_f.py -m U` will update all devices in assets.txt with the new main.py

`python3 init_exp_f.py -m C` will initiate a new experiment with the devices and settings in assets.txt

## Achitecture:
```
------    wifi   ----------
| PC |-----------| Router |
------           ----------
192.168.1.230     192.168.1.1
                      |     
                      |wifi 
                      | 
----------------------------------------
|                                      |
|  ------------    LoRa   --------     |
|  | gateways |-----------|  ED  |     |
|  ------------           --------     |
|   192.168.1.x          192.168.1.x   |
|                                      |
----------------------------------------
```
