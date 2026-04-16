
# Private LTE Network — srsRAN 4G

Private 4G LTE network built on Ubuntu 25.10 using srsRAN 4G and BladeRF xA4.

## Hardware
- BladeRF 2.0 Micro xA4
- Surface Pro 7 (Ubuntu 25.10)
- Samsung Galaxy S8 Duos SM-G950FD
- Identiv SCR3310v2 SIM reader
- OYEITIMES programmable USIM cards

## Architecture
- Band 4 (2110MHz DL / 1710MHz UL)
- PLMN 001/01
- Two eNBs: BladeRF (real RF) + ZMQ (virtual UE)
- srsEPC core network
- Asterisk PBX for voice
- baresip SIP clients
- InfluxDB + Grafana dashboard

## Launch
```bash
bladeRF-cli -l /usr/share/Nuand/bladerf/hostedxA4-latest.rbf
~/start_all.sh
```

## Dashboard
http://localhost:3000 (admin/ltepassword)
