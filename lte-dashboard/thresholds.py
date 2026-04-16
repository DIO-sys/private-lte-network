THRESHOLDS = {
    'bladerf_temperature': {
        'measurement': 'bladerf_hw', 'field': 'temperature',
        'warn': 60, 'critical': 75, 'unit': '°C', 'direction': 'above'},
    'cpu_frequency': {
        'measurement': 'system', 'field': 'cpu_freq_mhz',
        'warn': 2500, 'critical': 1800, 'unit': 'MHz', 'direction': 'below'},
    'surface_temperature': {
        'measurement': 'system_temp', 'field': 'temp_c',
        'warn': 80, 'critical': 90, 'unit': '°C', 'direction': 'above'},
    'sample_drops': {
        'measurement': 'rf_health', 'field': 'sample_drops',
        'warn': 1, 'critical': 10, 'unit': '/sec', 'direction': 'above'},
    'snr': {
        'measurement': 'enb_phy_dl', 'field': 'snr',
        'warn': 15, 'critical': 8, 'unit': 'dB', 'direction': 'below'},
    'mcs': {
        'measurement': 'enb_phy_dl', 'field': 'mcs',
        'warn': 10, 'critical': 5, 'unit': '', 'direction': 'below'},
    'ue_count': {
        'measurement': 'epc_state', 'field': 'ue_count',
        'warn': 1, 'critical': 0, 'unit': 'UEs', 'direction': 'below'},
    'auth_failures': {
        'measurement': 'epc_state', 'field': 'auth_failure',
        'warn': 1, 'critical': 5, 'unit': '', 'direction': 'above'},
    'jitter': {
        'measurement': 'voice_quality', 'field': 'jitter_ms',
        'warn': 20, 'critical': 50, 'unit': 'ms', 'direction': 'above'},
    'packet_loss': {
        'measurement': 'voice_quality', 'field': 'packet_loss_pct',
        'warn': 1, 'critical': 5, 'unit': '%', 'direction': 'above'},
    'mos': {
        'measurement': 'voice_quality', 'field': 'mos',
        'warn': 3.5, 'critical': 3.0, 'unit': '', 'direction': 'below'},
    'latency': {
        'measurement': 'latency', 'field': 'avg_ms',
        'warn': 100, 'critical': 200, 'unit': 'ms', 'direction': 'above'},
}
