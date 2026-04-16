#!/bin/bash
echo "Starting LTE Network Stack..."

cd ~/srsRAN_4G/build

# Namespaces and addresses
sudo ip netns add ue2 2>/dev/null
sudo ip addr add 127.0.1.1/8 dev lo 2>/dev/null
sudo ip addr add 127.0.1.2/8 dev lo 2>/dev/null

# Kernel settings
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null
sudo sysctl -w net.ipv4.conf.all.send_redirects=0 > /dev/null

# Start srsRAN
echo "Starting EPC..."
sudo srsepc epc.conf > /tmp/epc_stdout.log 2>&1 &
sleep 3

echo "Starting BladeRF eNB..."
sudo srsenb enb_bladerf.conf > /tmp/enb_bladerf_stdout.log 2>&1 &
sleep 2

echo "Starting ZMQ eNB..."
sudo srsenb enb2_zmq.conf > /tmp/enb2_stdout.log 2>&1 &
sleep 2

echo "Starting virtual UE..."
sudo srsue ue2_zmq.conf > /tmp/ue2_stdout.log 2>&1 &
sleep 10

# Fix routing
sudo sysctl -w net.ipv4.conf.srs_spgw_sgi.send_redirects=0 > /dev/null
sudo iptables -A FORWARD -s 172.16.0.0/24 -d 172.16.0.0/24 -j ACCEPT
sudo ip netns exec ue2 ip route add default via 172.16.0.1 dev tun_srsue 2>/dev/null

# Start Asterisk
sudo systemctl start asterisk
sleep 2

# Start dashboard stack
echo "Starting dashboard..."
cd ~/lte-dashboard
docker compose up -d 2>/dev/null
sleep 3

# Start monitor
python3 ~/lte-dashboard/lte_monitor.py &
echo $! > /tmp/monitor.pid

# Start incident capture
python3 ~/lte-dashboard/incident_capture.py &
echo $! > /tmp/incident.pid

echo ""
echo "==============================="
echo "Stack running:"
echo "  EPC:          127.0.1.100"
echo "  BladeRF eNB:  127.0.1.1"
echo "  ZMQ eNB:      127.0.1.2"
echo "  SGi gateway:  172.16.0.1"
echo "  Dashboard:    http://localhost:3000"
echo "  Incidents:    ~/incidents/"
echo "==============================="
echo ""
echo "Watch attach:   tail -f /tmp/epc.log"
echo "Watch eNB:      tail -f /tmp/enb_bladerf.log"
echo "Watch monitor:  tail -f /tmp/monitor.pid"
