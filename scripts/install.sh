#!/bin/bash
echo "Installing Private LTE Network dependencies..."

# System packages
sudo apt update
sudo apt install -y \
    build-essential cmake libfftw3-dev \
    libmbedtls-dev libboost-program-options-dev \
    libconfig++-dev libsctp-dev libzmq3-dev \
    libuhd-dev uhd-host libliquid-dev \
    libsoapysdr-dev soapysdr-tools \
    soapysdr-module-bladerf bladerf \
    pcscd pcsc-tools libpcsclite-dev \
    asterisk docker.io docker-compose-v2 \
    git python3-pip python3-setuptools \
    baresip

# Python packages
pip3 install influxdb-client psutil --break-system-packages

# Build srsRAN
cd ~
git clone https://github.com/srsran/srsRAN_4G.git
cd srsRAN_4G
mkdir build && cd build
cmake .. -DENABLE_SOAPYSDR=ON
make -j$(nproc)

# Install pysim
cd ~
git clone https://github.com/osmocom/pysim
cd pysim
sudo pip3 install -r requirements.txt --break-system-packages

# Copy configs
REPO_DIR=$(dirname $(realpath $0))
cp $REPO_DIR/*.conf ~/srsRAN_4G/build/
cp $REPO_DIR/user_db.csv ~/srsRAN_4G/build/
cp $REPO_DIR/start_all.sh ~/
cp $REPO_DIR/stop_all.sh ~/
cp $REPO_DIR/kill_all.sh ~/
cp $REPO_DIR/fix_routing.sh ~/
chmod +x ~/start_all.sh ~/stop_all.sh ~/kill_all.sh ~/fix_routing.sh

# Asterisk configs
sudo cp $REPO_DIR/asterisk_pjsip_wizard.conf /etc/asterisk/pjsip_wizard.conf
sudo cp $REPO_DIR/asterisk_extensions.conf /etc/asterisk/extensions.conf
sudo cp $REPO_DIR/asterisk_manager.conf /etc/asterisk/manager.conf
sudo cp $REPO_DIR/asterisk_logger.conf /etc/asterisk/logger.conf
sudo systemctl restart asterisk

# baresip configs
mkdir -p ~/.baresip ~/.baresip2
cp $REPO_DIR/baresip_config ~/.baresip/config
cp $REPO_DIR/baresip_accounts ~/.baresip/accounts
cp $REPO_DIR/baresip2_config ~/.baresip2/config
cp $REPO_DIR/baresip2_accounts ~/.baresip2/accounts

# Dashboard
mkdir -p ~/lte-dashboard/grafana/provisioning/datasources
mkdir -p ~/incidents
cp -r $REPO_DIR/lte-dashboard/* ~/lte-dashboard/

# Docker stack
cd ~/lte-dashboard
docker compose up -d

# Flash FPGA to BladeRF (run after plugging in BladeRF)
echo ""
echo "====================================="
echo "Installation complete."
echo ""
echo "Next steps:"
echo "1. Plug in BladeRF via USB 3.0"
echo "2. Run: bladeRF-cli -e 'flash_fpga /usr/share/Nuand/bladerf/hostedxA4-latest.rbf'"
echo "3. Unplug and replug BladeRF"
echo "4. Update INFLUX_TOKEN in ~/lte-dashboard/lte_monitor.py"
echo "5. Run: ~/start_all.sh"
echo "====================================="
