import os
import sys
import time
import csv
import subprocess
import re
import pickle
import pandas as pd
import numpy as np
import warnings

# Mute all unnecessary Python version warnings to keep the dashboard clean
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
MODEL_FILENAME = "wifishadow_model.p"
CSV_FILENAME = "wifi_signal_matrix.csv"
POLL_INTERVAL_MS = 400
ALERT_DURATION_THRESHOLD_SEC = 3.0
DEFAULT_MISSING_RSSI = -100

def load_radar_system():
    print("[*] Initializing Wi-Fi Shadow Core...")
    if not os.path.exists(CSV_FILENAME):
        print(f"[ERROR] Cannot find {CSV_FILENAME}. Ensure it is on your desktop.")
        sys.exit(1)
        
    with open(CSV_FILENAME, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
    tracked_bssids = headers[1:] 
    
    if not os.path.exists(MODEL_FILENAME):
        print(f"[ERROR] AI Model file '{MODEL_FILENAME}' not found on Desktop.")
        sys.exit(1)
        
    with open(MODEL_FILENAME, 'rb') as f:
        model = pickle.load(f)
        
    print(f"[+] System Armed. Tracking {len(tracked_bssids)} RF channels simultaneously.")
    return tracked_bssids, model

def scan_live_wifi():
    networks = {}
    try:
        cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='cp437')
        
        current_bssid = None
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("BSSID"):
                match = re.search(r"BSSID \d+\s*:\s*(.+)", line)
                if match:
                    current_bssid = match.group(1).strip().upper()
            elif line.startswith("Signal") and current_bssid:
                match = re.search(r"Signal\s*:\s*(\d+)%", line)
                if match:
                    pct = int(match.group(1))
                    dbm = int((pct / 2) - 100)
                    networks[current_bssid] = dbm
                    current_bssid = None
    except Exception:
        pass
    return networks

def main():
    tracked_bssids, ai_model = load_radar_system()
    raw_history = []
    anomaly_streak_start = None
    
    print("[*] Live Radar Daemon active. Standing by for environment disruptions...")
    print("-" * 75)
    
    try:
        while True:
            loop_start = time.time()
            live_signals = scan_live_wifi()
            
            snapshot = []
            for bssid in tracked_bssids:
                snapshot.append(live_signals.get(bssid, DEFAULT_MISSING_RSSI))
            
            raw_history.append(snapshot)
            if len(raw_history) > 7:  
                raw_history.pop(0)
                
            if len(raw_history) < 7:
                time.sleep(POLL_INTERVAL_MS / 1000.0)
                continue
                
            df_window = pd.DataFrame(raw_history, columns=tracked_bssids).replace(-100, np.nan)
            df_window = df_window.interpolate(method='linear').fillna(-90)
            
            current_variance = df_window.var(ddof=0).fillna(0).values.reshape(1, -1)
            prediction = ai_model.predict(current_variance)[0]
            
            if prediction == -1:
                if anomaly_streak_start is None:
                    anomaly_streak_start = time.time()
                
                elapsed_anomaly_time = time.time() - anomaly_streak_start
                
                if elapsed_anomaly_time >= ALERT_DURATION_THRESHOLD_SEC:
                    print(f"[ALERT] Physical Motion Detected in RF Environment! (Disruption Time: {elapsed_anomaly_time:.1f}s)")
                else:
                    print("[*] Scan Status: Minor RF scattering detected... evaluating threat level.")
            else:
                anomaly_streak_start = None
                print("[*] Scan Status: Environment Clear (Room Static)")
                
            elapsed = time.time() - loop_start
            sleep_time = (POLL_INTERVAL_MS / 1000.0) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n[+] Wi-Fi Shadow Radar shutdown cleanly.")

if __name__ == "__main__":
    main()