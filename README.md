# Private LTE Network — srsRAN 4G

Private 4G LTE network built on Ubuntu using srsRAN 4G and BladeRF xA4.

## Hardware
- BladeRF 2.0 Micro xA4 (FPGA: hostedxA4-latest.rbf)
- Asus Gaming Laptop (Ubuntu) — primary machine
- Samsung Galaxy S8 Duos SM-G950FD (unlocked, Band 4)
- Identiv SCR3310v2 USB SIM reader
- OYEITIMES programmable USIM cards
- 2x Bingfu 2.4GHz 8dBi SMA antennas

## Architecture
Real phone (SM-G950FD + programmed SIM) ↓ RF over air (Band 4, 2110MHz) BladeRF xA4 ↓ srsENB (enb_bladerf.conf) → gtp 127.0.1.1 ↓ srsEPC → MME 127.0.1.100, SGi 172.16.0.1 Virtual UE (srsUE ZMQ) ↓ ZMQ sockets (ports 2004/2005) ↓ srsENB (enb2_zmq.conf) → gtp 127.0.1.2 ↓ baresip → Asterisk PBX

## Network Config
| Parameter | Value |
|-----------|-------|
| PLMN | 001/01 |
| Band | 4 (dl_earfcn=1950) |
| DL Freq | 2110 MHz |
| UL Freq | 1710 MHz |
| EPC MME | 127.0.1.100 |
| eNB1 BladeRF | 127.0.1.1 |
| eNB2 ZMQ | 127.0.1.2 |
| SGi gateway | 172.16.0.1 |
| UE2 virtual | 172.16.0.3 |
| Phone | 172.16.0.4 |

## SIM Card
- Hardware: OYEITIMES blank programmable LTE USIM
- Reader: Identiv SCR3310v2
- Software: GRSIMWrite 4.4.4 (Windows only)
- Algorithm: Milenage
- ADM default: 11111111

## Voice
- Asterisk 22.5.2 PJSIP
- Endpoints: phone, ue2 (password: 1234)
- baresip for virtual UE
- Zoiper on real phone

## Dashboard
- InfluxDB 2.0 + Grafana running in Docker
- http://localhost:3000 (admin/ltepassword)
- Metrics: UE count, latency, CPU, RAM, temperature, SNR, MOS, jitter

## Quick Start
```bash
~/start_all.sh
baresip -f ~/.baresip2 &
```

## Install On New Machine
```bash
git clone https://github.com/timodagoat/private-lte-network.git
cd private-lte-network
./install.sh
```

## Current Status
- ZMQ virtual UE attaching ✓
- Dashboard running ✓
- BladeRF eNB transmitting Band 4 ✓
- Real phone attach: in progress
- Voice calls: pending phone attach

## Known Issues
- Surface Pro 7 USB power management kills BladeRF → moved to Asus laptop
- OYEITIMES SIM cards require Windows + GRSIMWrite for programming
- Wine 10.0 on Ubuntu 25.10 has broken PC/SC passthrough
- SM-G900V Verizon S5 was SIM locked → switched to SM-G950FD S8 Duos

## File Structure
├── install.sh ├── README.md ├── start_all.sh ├── stop_all.sh ├── kill_all.sh ├── fix_routing.sh ├── enb_bladerf.conf ├── enb2_zmq.conf ├── ue2_zmq.conf ├── epc.conf ├── user_db.csv ├── asterisk_pjsip_wizard.conf ├── asterisk_extensions.conf ├── asterisk_manager.conf ├── asterisk_logger.conf ├── baresip_config ├── baresip_accounts ├── baresip2_config ├── baresip2_accounts └── lte-dashboard/ ├── docker-compose.yml ├── lte_monitor.py ├── incident_capture.py ├── thresholds.py └── grafana/ └── provisioning/ └── datasources/ └── influxdb.yml
