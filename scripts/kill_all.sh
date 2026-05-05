#!/bin/bash
echo "Killing everything..."
sudo killall srsenb srsue srsepc 2>/dev/null
pkill -f lte_monitor.py 2>/dev/null
pkill -f incident_capture.py 2>/dev/null
pkill -f baresip 2>/dev/null
sudo systemctl stop asterisk 2>/dev/null
sudo ip netns del ue2 2>/dev/null
echo "Done."
