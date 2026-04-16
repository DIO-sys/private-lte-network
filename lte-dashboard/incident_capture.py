#!/usr/bin/env python3
import time, json, os, threading
from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient
from thresholds import THRESHOLDS

INFLUX_URL    = "http://localhost:8086"
INFLUX_TOKEN  = "INFLUX_TOKEN_HERE"
INFLUX_ORG    = "lte-network"
INFLUX_BUCKET = "srsran"
INCIDENT_DIR  = "/home/timodagoat/incidents"
CAPTURE_WIN   = 30
CHECK_SECS    = 15

os.makedirs(INCIDENT_DIR, exist_ok=True)

client    = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

active_incidents = {}
incident_lock    = threading.Lock()

def query_window(measurement, field, start, stop):
    q = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: {start}, stop: {stop})
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        |> sort(columns: ["_time"])
    '''
    try:
        result = query_api.query(q)
        return [{'time': r.get_time().isoformat(),
                 'value': r.get_value()}
                for table in result for r in table.records]
    except:
        return []

def get_latest(measurement, field):
    q = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -1m)
        |> filter(fn: (r) => r._measurement == "{measurement}")
        |> filter(fn: (r) => r._field == "{field}")
        |> last()
    '''
    try:
        result = query_api.query(q)
        for table in result:
            for record in table.records:
                return record.get_value()
    except:
        pass
    return None

def check_crossed(value, threshold):
    if value is None: return None
    d = threshold.get('direction', 'above')
    if d == 'above':
        if value >= threshold['critical']: return 'CRITICAL'
        if value >= threshold['warn']:     return 'WARNING'
    else:
        if value <= threshold['critical']: return 'CRITICAL'
        if value <= threshold['warn']:     return 'WARNING'
    return None

def find_crossings(start, stop):
    crossings = []
    for name, t in THRESHOLDS.items():
        data = query_window(t['measurement'], t['field'], start, stop)
        if not data: continue
        values   = [d['value'] for d in data]
        min_val  = min(values)
        max_val  = max(values)
        avg_val  = round(sum(values)/len(values), 3)
        d        = t.get('direction', 'above')
        severity = None
        if d == 'above':
            if max_val >= t['critical']: severity = 'CRITICAL'
            elif max_val >= t['warn']:   severity = 'WARNING'
        else:
            if min_val <= t['critical']: severity = 'CRITICAL'
            elif min_val <= t['warn']:   severity = 'WARNING'
        if severity:
            first = next((d['time'] for d in data if
                (d['value'] >= t['warn'] if d == 'above'
                 else d['value'] <= t['warn'])), None)
            crossings.append({
                'metric': name, 'severity': severity,
                'warn': t['warn'], 'critical': t['critical'],
                'unit': t['unit'], 'min': min_val,
                'max': max_val, 'avg': avg_val,
                'first_crossing': first
            })
    return crossings

def capture_incident(trigger_name, trigger_value, severity):
    now = datetime.now(timezone.utc)
    with incident_lock:
        if trigger_name in active_incidents:
            if (now - active_incidents[trigger_name]).seconds < 300:
                return
        active_incidents[trigger_name] = now

    incident_id  = now.strftime('%Y%m%d_%H%M%S') + f'_{trigger_name}'
    trigger_ts   = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    before_start = (now - timedelta(minutes=CAPTURE_WIN))\
                   .strftime('%Y-%m-%dT%H:%M:%SZ')
    after_end_dt = now + timedelta(minutes=CAPTURE_WIN)

    print(f"\n{'='*60}")
    print(f"INCIDENT: {trigger_name} = {trigger_value} [{severity}]")
    print(f"ID: {incident_id}")
    print(f"{'='*60}\n")

    key_metrics = [
        ('bladerf_hw',    'temperature',  'bladerf_temp_c'),
        ('system',        'cpu_freq_mhz', 'cpu_freq_mhz'),
        ('system_temp',   'temp_c',       'surface_temp_c'),
        ('enb_phy_dl',    'snr',          'snr_db'),
        ('enb_phy_dl',    'mcs',          'mcs'),
        ('rf_health',     'sample_drops', 'sample_drops'),
        ('epc_state',     'ue_count',     'ue_count'),
        ('voice_quality', 'mos',          'mos'),
        ('latency',       'avg_ms',       'latency_ms'),
        ('heartbeat',     'alive',        'heartbeat'),
    ]

    def capture_window(start, stop):
        crossings = find_crossings(start, stop)
        metrics   = {}
        for meas, field, label in key_metrics:
            data = query_window(meas, field, start, stop)
            if data:
                values = [d['value'] for d in data]
                metrics[label] = {
                    'timeseries': data,
                    'min': min(values),
                    'max': max(values),
                    'avg': round(sum(values)/len(values), 3)
                }
        return crossings, metrics

    print("Capturing before-window...")
    before_crossings, before_metrics = capture_window(
        before_start, trigger_ts)

    incident = {
        'incident_id': incident_id,
        'trigger': {
            'metric': trigger_name, 'value': trigger_value,
            'severity': severity, 'timestamp': trigger_ts
        },
        'window': {
            'before_start': before_start,
            'trigger': trigger_ts,
            'after_end': after_end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        },
        'before_window': {
            'crossings': before_crossings,
            'metrics':   before_metrics
        },
        'after_window':  {'crossings': [], 'metrics': {}},
        'summary':       {'capture_complete': False}
    }

    path = os.path.join(INCIDENT_DIR, f'{incident_id}.json')
    with open(path, 'w') as f:
        json.dump(incident, f, indent=2, default=str)

    print(f"Waiting {CAPTURE_WIN} minutes for after-window...")
    time.sleep(CAPTURE_WIN * 60)

    print("Capturing after-window...")
    actual_end = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    after_crossings, after_metrics = capture_window(trigger_ts, actual_end)

    incident['after_window'] = {
        'crossings': after_crossings,
        'metrics':   after_metrics
    }

    all_c      = before_crossings + after_crossings
    critical_l = [c for c in all_c if c['severity'] == 'CRITICAL']
    warning_l  = [c for c in all_c if c['severity'] == 'WARNING']
    ue_after   = after_metrics.get('ue_count', {}).get('timeseries', [])
    recovered  = any(d['value'] > 0 for d in ue_after)
    hb_after   = after_metrics.get('heartbeat', {}).get('timeseries', [])
    outage     = len(hb_after) < (CAPTURE_WIN * 60 / 10 * 0.5)

    incident['summary'] = {
        'total_crossings':   len(all_c),
        'critical_count':    len(critical_l),
        'warning_count':     len(warning_l),
        'critical_metrics':  [c['metric'] for c in critical_l],
        'warning_metrics':   [c['metric'] for c in warning_l],
        'network_recovered': recovered,
        'outage_detected':   outage,
        'capture_complete':  True
    }

    with open(path, 'w') as f:
        json.dump(incident, f, indent=2, default=str)

    # Human readable summary
    summary_path = os.path.join(INCIDENT_DIR, f'{incident_id}_summary.txt')
    with open(summary_path, 'w') as f:
        f.write(f"INCIDENT REPORT\n")
        f.write(f"{'='*50}\n")
        f.write(f"ID:        {incident_id}\n")
        f.write(f"Trigger:   {trigger_name}\n")
        f.write(f"Value:     {trigger_value}\n")
        f.write(f"Severity:  {severity}\n")
        f.write(f"Time:      {trigger_ts}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"BEFORE WINDOW (30 min prior):\n")
        for c in before_crossings:
            f.write(f"  [{c['severity']}] {c['metric']}: "
                    f"min={c['min']} max={c['max']} "
                    f"avg={c['avg']} {c['unit']}\n")
        f.write(f"\nAFTER WINDOW (30 min after):\n")
        for c in after_crossings:
            f.write(f"  [{c['severity']}] {c['metric']}: "
                    f"min={c['min']} max={c['max']} "
                    f"avg={c['avg']} {c['unit']}\n")
        f.write(f"\nSUMMARY:\n")
        f.write(f"  Critical: {len(critical_l)}\n")
        f.write(f"  Warning:  {len(warning_l)}\n")
        f.write(f"  Recovered: {'Yes' if recovered else 'No'}\n")
        f.write(f"  Outage:    {'Yes' if outage else 'No'}\n")

    print(f"Incident fully captured → {path}")
    print(f"Summary → {summary_path}")

    with incident_lock:
        active_incidents.pop(trigger_name, None)

def monitor_loop():
    print(f"Incident monitor started — checking {len(THRESHOLDS)} thresholds every {CHECK_SECS}s\n")
    while True:
        for name, t in THRESHOLDS.items():
            value    = get_latest(t['measurement'], t['field'])
            severity = check_crossed(value, t)
            if severity == 'CRITICAL':
                thread = threading.Thread(
                    target=capture_incident,
                    args=(name, value, severity),
                    daemon=True)
                thread.start()
        time.sleep(CHECK_SECS)

if __name__ == '__main__':
    monitor_loop()
