#!/bin/bash
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv4.conf.all.send_redirects=0
sudo sysctl -w net.ipv4.conf.srs_spgw_sgi.send_redirects=0
sudo ip addr add 127.0.1.2/8 dev lo 2>/dev/null
sudo iptables -A FORWARD -s 172.16.0.0/24 -d 172.16.0.0/24 -j ACCEPT
sudo ip netns exec ue1 ip route add default via 172.16.0.1 dev tun_srsue 2>/dev/null
sudo ip netns exec ue2 ip route add default via 172.16.0.1 dev tun_srsue 2>/dev/null
echo "Routing fixed"
