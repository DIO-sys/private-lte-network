#!/usr/bin/env python3
import re, time, threading, subprocess, psutil, os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "INFLUX_TOKEN_HERE"
INFLUX_ORG    = "lte-network"
INFLUX_BUCKET = "srsran"

LOG_ENB  = "/tmp/enb_bladerf.log"
LOG_ENB2 = "/tmp/enb2.log"
LOG_EPC  = "/tmp/epc.log"
LOG_UE2  = "/tmp/ue.log"
LOG_AST  = "/var/log/asterisk/messages.log"

client    = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write(measurement, fields, tags={}):
    try:
        point = Point(measurement)
        for k, v in tags.items():   point = point.tag(k, v)
        for k, v in fields.items():
            if v is not None: point = point.field(k, float(v))
        write_api.write(INFLUX_BUCKET, INFLUX_ORG, point)
    except Exception as e:
        print(f"[Write error] {e}")

def tail_log(filepath, callback, label=""):
    print(f"[{label}] Waiting for: {filepath}")
    while not os.path.exists(filepath):
        time.sleep(2)
    print(f"[{label}] Tailing: {filepath}")
    with open(filepath, 'r') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line: callback(line.strip())
            else:    time.sleep(0.05)

def parse_enb(line, enb_id="enb1"):
    tags = {"enb": enb_id}
    m = re.search(r'PDSCH.*cqi=(\d+).*mcs=(\d+).*snr=([\d.]+)', line)
    if m:
        write("enb_phy_dl", {
            "cqi": int(m.group(1)),
            "mcs": int(m.group(2)),
            "snr": float(m.group(3))
        }, tags)
    m = re.search(r'HARQ.*ack=(\d)', line)
    if m:
        ack = int(m.group(1))
        write("harq", {"ack": ack, "nack": 1-ack}, tags)
    m = re.search(r'[Ss]ample.*drop.*?(\d+)', line)
    if m:
        write("rf_health", {"sample_drops": int(m.group(1))}, tags)
    if 'S1 connected' in line:
        write("epc_state", {"s1ap_connected": 1}, tags)
    if 'S1 disconnected' in line:
        write("epc_state", {"s1ap_connected": 0}, tags)

ue_count = 0
ue_lock  = threading.Lock()

def parse_epc(line):
    global ue_count
    # Auth failure
    if 'Authentication' in line and 'fail' in line.lower():
        write("epc_state", {"auth_failure": 1}, {})
    # Auth success
    if 'Integrity check ok' in line:
        write("epc_state", {"auth_success": 1}, {})
    # UE attached — bearer activated
    if 'Activated EPS Bearer' in line:
        with ue_lock:
            ue_count += 1
            write("epc_state", {"ue_count": ue_count}, {})
    # UE detached
    if 'UE Context Release' in line and 'Complete' in line:
        with ue_lock:
            ue_count = max(0, ue_count - 1)
            write("epc_state", {"ue_count": ue_count}, {})
    # S1AP connected
    if 'S1 Setup Request' in line:
        write("epc_state", {"s1ap_connected": 1}, {})

def parse_ue(line, ue_id="ue2"):
    tags = {"ue": ue_id}
    m = re.search(r'RSRP=([-\d.]+).*RSRQ=([-\d.]+).*SNR=([\d.]+)', line)
    if m:
        write("ue_phy", {
            "rsrp": float(m.group(1)),
            "rsrq": float(m.group(2)),
            "snr":  float(m.group(3))
        }, tags)
    m = re.search(r'[Ss]ample.*drop.*?(\d+)', line)
    if m:
        write("ue_rf", {"sample_drops": int(m.group(1))}, tags)
    if 'Network attach successful' in line:
        write("ue_state", {"attached": 1}, tags)

def parse_asterisk(line):
    if 'registered' in line and 'PJSIP' in line:
        write("sip_state", {"registered": 1}, {})
    m = re.search(
        r'[Ll]oss=([\d.]+)%.*[Jj]itter=([\d.]+).*[Rr]tt=([\d.]+)',
        line)
    if m:
        loss   = float(m.group(1))
        jitter = float(m.group(2))
        rtt    = float(m.group(3))
        r = max(0, min(100, 93.2 - loss*2.5 - jitter*0.2 - rtt*0.1))
        mos = (4.5 if r >= 100 else
               4.0 + (r-80)*0.025 if r >= 80 else
               3.0 + (r-60)*0.05  if r >= 60 else
               2.0 + (r-40)*0.05  if r >= 40 else
               1.0 + r*0.025)
        write("voice_quality", {
            "packet_loss_pct": loss,
            "jitter_ms":       jitter,
            "rtt_ms":          rtt,
            "mos":             round(mos, 2)
        }, {})

def poll_bladerf():
    while True:
        try:
            r = subprocess.run(
                ['bladeRF-cli', '-e', 'print temperature'],
                capture_output=True, text=True, timeout=5)
            m = re.search(r'([\d.]+)', r.stdout)
            if m:
                write("bladerf_hw", {"temperature": float(m.group(1))}, {})
        except: pass
        time.sleep(10)

def poll_system():
    while True:
        try:
            for i, pct in enumerate(psutil.cpu_percent(percpu=True)):
                write("system", {"cpu_pct": pct}, {"core": str(i)})
            freq = psutil.cpu_freq()
            if freq:
                write("system", {"cpu_freq_mhz": freq.current}, {})
            mem = psutil.virtual_memory()
            write("system", {
                "ram_pct":     mem.percent,
                "ram_used_gb": mem.used / 1e9
            }, {})
            for chip, readings in psutil.sensors_temperatures().items():
                for r in readings:
                    label = (r.label or chip).replace(' ', '_')
                    write("system_temp", {"temp_c": r.current},
                          {"sensor": label})
        except: pass
        time.sleep(5)

def poll_latency():
    while True:
        try:
            # Host → EPC
            r = subprocess.run(
                ['ping', '172.16.0.1', '-c', '5', '-i', '0.2', '-W', '1'],
                capture_output=True, text=True, timeout=15)
            m = re.search(
                r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)',
                r.stdout)
            if m:
                write("latency", {
                    "min_ms": float(m.group(1)),
                    "avg_ms": float(m.group(2)),
                    "max_ms": float(m.group(3))
                }, {"path": "host_to_epc"})

            # Host → UE2
            r2 = subprocess.run(
                ['ping', '172.16.0.3', '-c', '5', '-i', '0.2', '-W', '1'],
                capture_output=True, text=True, timeout=15)
            m2 = re.search(
                r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)',
                r2.stdout)
            if m2:
                write("latency", {
                    "min_ms": float(m2.group(1)),
                    "avg_ms": float(m2.group(2)),
                    "max_ms": float(m2.group(3))
                }, {"path": "host_to_ue2"})

            # UE2 namespace → EPC
            r3 = subprocess.run(
                ['sudo', 'ip', 'netns', 'exec', 'ue2',
                 'ping', '172.16.0.1', '-c', '5', '-i', '0.2', '-W', '1'],
                capture_output=True, text=True, timeout=15)
            m3 = re.search(
                r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)',
                r3.stdout)
            if m3:
                write("latency", {
                    "min_ms": float(m3.group(1)),
                    "avg_ms": float(m3.group(2)),
                    "max_ms": float(m3.group(3))
                }, {"path": "ue2_to_epc"})

        except Exception as e:
            print(f"[Latency error] {e}")
        time.sleep(30)

def write_heartbeat():
    while True:
        write("heartbeat", {"alive": 1}, {})
        time.sleep(10)

def main():
    print("="*50)
    print("LTE Network Monitor Starting")
    print("="*50)
    threads = [
        threading.Thread(target=tail_log,
            args=(LOG_ENB,  lambda l: parse_enb(l, "enb1"), "eNB1"),
            daemon=True),
        threading.Thread(target=tail_log,
            args=(LOG_ENB2, lambda l: parse_enb(l, "enb2"), "eNB2"),
            daemon=True),
        threading.Thread(target=tail_log,
            args=(LOG_EPC,  parse_epc, "EPC"),
            daemon=True),
        threading.Thread(target=tail_log,
            args=(LOG_UE2,  lambda l: parse_ue(l, "ue2"), "UE2"),
            daemon=True),
        threading.Thread(target=tail_log,
            args=(LOG_AST,  parse_asterisk, "Asterisk"),
            daemon=True),
        threading.Thread(target=poll_bladerf,  daemon=True),
        threading.Thread(target=poll_system,   daemon=True),
        threading.Thread(target=poll_latency,  daemon=True),
        threading.Thread(target=write_heartbeat, daemon=True),
    ]
    for t in threads: t.start()
    print("All monitors started")
    print("Dashboard: http://localhost:3000")
    try:
        while True:
            time.sleep(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor running")
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == '__main__':
    main()
