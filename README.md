# Private LTE Network — srsRAN 4G

Private 4G LTE network built on Ubuntu using srsRAN 4G, BladeRF xA4, and a Raspberry Pi 4.

## Architecture

```
                    SURFACE PRO 7 (Ubuntu)                    RASPBERRY PI 4
               ┌──────────────────────────┐              ┌──────────────────┐
               │  srsepc (EPC)            │◄──Ethernet──►│  srsenb (eNB)    │
               │  Asterisk PBX            │  192.168.1.x │  BladeRF xA4    │
               │  Wireshark / Grafana     │              │                  │
               │                          │              │    TX1 ──► 🔺    │
               │  ┌─ ZMQ Virtual UEs ──┐  │              │    RX1 ──► 🔺    │
               │  │ srsue (ue1, ue2)   │  │              └──────────────────┘
               │  │ srsenb (zmq x2)    │  │                      ▼ RF
               │  │ baresip (x2)       │  │              ┌──────────────────┐
               │  └────────────────────┘  │              │  COTS UE Phone   │
               └──────────────────────────┘              │  + Programmed SIM│
                                                         └──────────────────┘
```

## Hardware

| Component | Details |
|---|---|
| SDR | BladeRF 2.0 Micro xA4 (FW: v2.6.0, FPGA: v0.16.0) |
| eNB Host | Raspberry Pi 4B 4GB (CanaKit Starter PRO) |
| EPC Host | Surface Pro 7 (dual-boot Windows/Ubuntu) |
| COTS UE | Motorola Moto G Power 5G 2023 (Snapdragon 480+, unlocked) |
| COTS UE (backup) | Samsung Galaxy S8 Duos SM-G950FD (Exynos — not recommended) |
| SIM Reader | Identiv SCR3310v2 USB |
| SIM Cards | OYEITIMES programmable LTE USIM |
| Antennas | 2x Eightwood 5G/4G LTE SMA (1710-2700MHz, 2dBi) |
| Antenna (spare) | 1x Nuand Tri-Band (700-2600MHz, 5dBi) |
| Ethernet | USB-to-Ethernet adapter + Cat5e cable (Pi ↔ Surface Pro) |

## Network Config

| Parameter | Value |
|---|---|
| PLMN | 310/260 |
| Band | 4 (dl_earfcn=1950) |
| DL Freq | 2110 MHz |
| UL Freq | 1710 MHz |
| PRBs | 6 |
| EPC MME | 192.168.1.10 (Surface Pro) |
| eNB (Pi) | 192.168.1.20 |
| SGi gateway | 172.16.0.1 |
| UE1 virtual | 172.16.0.2 |
| UE2 virtual | 172.16.0.3 |
| Phone | 172.16.0.4 (dynamic) |

## Config Files

### BladeRF eNB (runs on Pi)
- `enb_bladerf.conf` — eNB config for BladeRF RF mode
- `sib.conf` — SIB parameters (prach_freq_offset=4 for 6 PRBs)
- `rr.conf` — Radio resource config
- `rb.conf` — Radio bearer config

### EPC (runs on Surface Pro)
- `epc.conf` — EPC config for BladeRF mode (mme_bind=192.168.1.10)
- `epc_zmq.conf` — EPC config for ZMQ virtual mode
- `user_db.csv` — Subscriber database (IMSI, Ki, OPc)

### ZMQ Virtual UEs (runs on Surface Pro)
- `enb_zmq.conf` — eNB1 for virtual UE1
- `enb2_zmq.conf` — eNB2 for virtual UE2
- `ue_zmq.conf` — Virtual UE1 (IMSI: 310260123456789)
- `ue2_zmq.conf` — Virtual UE2 (IMSI: 310260123456780)

### Voice
- `baresip_config` — Baresip config for UE1
- `baresip2_config` — Baresip config for UE2
- `baresip_accounts` — SIP account for UE1
- `baresip2_accounts` — SIP account for UE2

### Scripts
- `start_all.sh` — Start all ZMQ components
- `stop_all.sh` — Stop all components
- `kill_all.sh` — Force kill all components
- `fix_routing.sh` — Enable IP forwarding and routing between virtual UEs
- `install.sh` — Install dependencies on new machine

## SIM Card Programming

| Parameter | Value |
|---|---|
| Software | GRSIMWrite 4.4.4 (Windows only) |
| Reader | Identiv SCR3310v2 |
| ADM Key | 11111111 |
| Algorithm | Milenage |
| IMSI | 310260123456790 |
| Ki | 00112233445566778899aabbccddeeff |
| OPc | 63bfa50ee6523365ff14c1f45f88737d |
| PLMNwAct | 310260:4000 |
| HPLMNwAct | 310260:4000 |

## Raspberry Pi Setup

### Prerequisites
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y cmake build-essential libfftw3-dev libmbedtls-dev \
  libboost-program-options-dev libconfig++-dev libsctp-dev libusb-1.0-0-dev \
  pkg-config git libcurl4-openssl-dev libncurses-dev
```

### BladeRF Drivers
```bash
git clone https://github.com/Nuand/bladeRF.git
cd bladeRF/host && mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local -DINSTALL_UDEV_RULES=ON ..
make -j4 && sudo make install && sudo ldconfig
```

### SoapySDR + SoapyBladeRF
```bash
cd ~
git clone https://github.com/pothosware/SoapySDR.git
cd SoapySDR && mkdir build && cd build
cmake .. && make -j4 && sudo make install && sudo ldconfig

cd ~
git clone https://github.com/pothosware/SoapyBladeRF.git
cd SoapyBladeRF && mkdir build && cd build
cmake .. && make -j4 && sudo make install && sudo ldconfig
```

### srsRAN 4G
```bash
cd ~
git clone https://github.com/srsRAN/srsRAN_4G.git
cd srsRAN_4G && mkdir build && cd build
cmake ../ && make -j4 && sudo make install && sudo ldconfig
```

### FPGA Image
```bash
sudo mkdir -p /etc/Nuand/bladeRF
sudo wget https://www.nuand.com/fpga/hostedxA4-latest.rbf -O /etc/Nuand/bladeRF/hostedxA4.rbf
```

## Quick Start — BladeRF Mode

### Surface Pro (EPC)
```bash
sudo ip addr add 192.168.1.10/24 dev enx50a03006073b
cd ~/lte-project
sudo srsepc epc.conf
```

### Raspberry Pi (eNB)
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
sudo srsenb ~/enb_bladerf.conf
```

### Phone
1. Insert programmed OYEITIMES SIM
2. Set phone to LTE only mode (`*#*#4636#*#*` → Phone Info → LTE only)
3. Settings → Network → Mobile Networks → Network Operators → Search
4. Look for 310/260 and connect

## Quick Start — ZMQ Virtual Mode

```bash
# Terminal 1 — EPC
cd ~/lte-project && sudo srsepc epc_zmq.conf

# Terminal 2 — eNB1
cd ~/lte-project && sudo srsenb enb_zmq.conf

# Terminal 3 — UE1
sudo ip netns add ue1
cd ~/lte-project && sudo srsue ue_zmq.conf

# Terminal 4 — eNB2
cd ~/lte-project && sudo srsenb enb2_zmq.conf

# Terminal 5 — UE2
sudo ip netns add ue2
cd ~/lte-project && sudo srsue ue2_zmq.conf

# Terminal 6 — Routing
sudo bash ~/lte-project/fix_routing.sh

# Terminal 7 — Baresip UE1
sudo ip netns exec ue1 baresip

# Terminal 8 — Baresip UE2
sudo ip netns exec ue2 baresip -f /root/.baresip2

# Make a call from UE1
/dial sip:ue2@172.16.0.1

# Answer on UE2
/answer
```

## Wireshark & PCAP

### Capture (enabled in enb_bladerf.conf and epc.conf)
```bash
# Copy PCAPs from Pi
scp timopi@192.168.1.20:/tmp/enb_mac.pcap ~/
scp timopi@192.168.1.20:/tmp/enb_s1ap.pcap ~/

# Open in Wireshark
wireshark ~/enb_mac.pcap &
wireshark ~/enb_s1ap.pcap &
wireshark /tmp/epc.pcap &

# Capture SIP/RTP traffic
sudo tcpdump -i srs_spgw_sgi -w ~/sip_capture.pcap
```

### PCAP Types
| Capture | Location | What it shows |
|---|---|---|
| MAC | Pi: /tmp/enb_mac.pcap | Radio layer — RACH, RRC, scheduling |
| S1AP | Pi: /tmp/enb_s1ap.pcap | eNB↔EPC signaling — attach, bearer setup |
| NAS | Surface: /tmp/epc.pcap | Authentication, security mode, session mgmt |
| SIP/RTP | Surface: ~/sip_capture.pcap | Voice call setup and audio |

## Dashboard

- InfluxDB 2.0 + Grafana running in Docker
- http://localhost:3000 (admin/ltepassword)
- Metrics: UE count, latency, CPU, RAM, temperature, SNR, MOS, jitter

## Current Status

- [x] ZMQ virtual UE attach and data
- [x] ZMQ virtual UE-to-UE voice calls via Asterisk/baresip
- [x] BladeRF eNB starts on Pi, connects to EPC via S1
- [x] S1AP handshake confirmed in Wireshark
- [x] SIB1/SIB2 broadcast confirmed in debug logs
- [x] RF status clean (O=295, U=0, L=0)
- [x] SIM card programmed with matching credentials
- [x] Moto G Power (Qualcomm) acquired for COTS UE testing
- [x] Eightwood LTE antennas acquired
- [ ] COTS phone discovers network (RF issue — see Known Issues)
- [ ] COTS phone attach and data
- [ ] Voice call between COTS phone and virtual UE

## Known Issues

### Phone has difficulty finding entwork
The eNB broadcasts SIB1/SIB2, connects to EPC, reports clean RF status, but no phone (Samsung S8 Exynos, Moto G Power Qualcomm, iPhone 13) can find the cell during manual network search. Root cause is suspected to be BladeRF VCTCXO frequency offset — the internal clock is slightly off from the target frequency, causing phones to fail PSS/SSS synchronization decode.

**Planned fixes (in order):**
1. Frequency offset sweep using `dl_freq`/`ul_freq` parameters
2. SoapyUHD bridge for tighter TX timing
3. HackRF One as spectrum analyzer to measure actual TX frequency
4. Leo Bodnar GPSDO (10MHz reference clock) for the BladeRF REFIN input
5. Email Nuand support for factory VCTCXO calibration value

### Other issues
- Surface Pro 7 USB power management corrupts BladeRF IQ → migrated eNB to Raspberry Pi 4
- BladeRF native srsRAN driver (`rf_blade_imp.c`) incompatible with bladeRF 2.0 micro → must use SoapySDR
- FPGA v0.14.0 incompatible with firmware v2.6.0 → locked to FPGA v0.16.0
- BladeRF TX output is ~+6 dBm (4mW) — very low power, may need BT-100 amplifier
- Samsung S8 Duos (Exynos) baseband too picky for SDR clock accuracy → switched to Qualcomm phone
- OYEITIMES SIM programming requires Windows + GRSIMWrite (no Linux support)
- Pi 4 limited to 6-15 PRBs max (50 PRBs crashes)
- BladeRF TX errors are intermittent — sometimes requires multiple power cycles to get clean start

## References

- [srsRAN 4G COTS UE Guide](https://docs.srsran.com/projects/4g/en/latest/app_notes/source/cots_ue/source/)
- [srsRAN Pi4 App Note](https://docs.srsran.com/projects/4g/en/latest/app_notes/source/pi4/source/index.html)
- [BladeRF xA4 + srsRAN (Issue #693)](https://github.com/srsran/srsRAN_4G/issues/693)
- [BladeRF xA4 + srsRAN 5G (Issue #657)](https://github.com/srsran/srsRAN_Project/issues/657)
- [BladeRF intermittent attach (Issue #1247)](https://github.com/srsran/srsRAN_4G/issues/1247)
- [Nick vs Networking — srsLTE BladeRF Install](https://nickvsnetworking.com/srslte-install-for-bladerf-limesdr-on-debian-ubuntu/)
- [Nuand BladeRF Power Consumption](https://github.com/Nuand/bladeRF/wiki/bladeRF-Power-Consumption)
- [Nuand Factory Calibration](http://www.nuand.com/calibration.php)
