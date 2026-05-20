import os
import sys
import time
import csv
import subprocess
import re
from datetime import datetime

# --- CONFIGURATION ---
CSV_FILENAME = "wifi_signal_matrix.csv"
POLL_INTERVAL_MS = 400  
DISCOVERY_DURATION_SEC = 5  
DEFAULT_MISSING_RSSI = -100  

def get_platform():
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('linux'):
        return 'linux'
    else:
        print(f"[ERROR] Unsupported OS: {sys.platform}")
        sys.exit(1)

def scan_wifi(os_type):
    networks = {}
    try:
        if os_type == 'windows':
            cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='cp437')
            
            current_ssid = "Unknown"
            current_bssid = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                # \s*:\s* allows for any number of spaces around the colon
                if line.startswith("SSID"):
                    match = re.search(r"SSID \d+\s*:\s*(.+)", line)
                    if match:
                        current_ssid = match.group(1).strip()
                elif line.startswith("BSSID"):
                    match = re.search(r"BSSID \d+\s*:\s*(.+)", line)
                    if match:
                        current_bssid = match.group(1).strip().upper()
                elif line.startswith("Signal") and current_bssid:
                    match = re.search(r"Signal\s*:\s*(\d+)%", line)
                    if match:
                        pct = int(match.group(1))
                        dbm = int((pct / 2) - 100)
                        networks[current_bssid] = (current_ssid, dbm)
                        current_bssid = None  

        elif os_type == 'linux':
            cmd = ["nmcli", "-t", "-f", "BSSID,SSID,SIGNAL", "dev", "wifi", "list"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if not line:
                    continue
                parts = line.strip().split(':')
                if len(parts) >= 3:
                    bssid = ":".join(parts[0:6]).upper()
                    signal_pct = int(parts[-1])
                    ssid = ":".join(parts[6:-1]) if len(parts) > 3 else "Hidden"
                    dbm = int((signal_pct / 2) - 100)
                    networks[bssid] = (ssid, dbm)

    except Exception:
        pass
        
    return networks

def run_discovery(os_type):
    print(f"[*] Initializing RF Discovery Phase ({DISCOVERY_DURATION_SEC}20)...")
    print("[*] Standing by for environment baseline. Keep the room still.")
    discovered_bssids = set()
    bssid_to_ssid = {}
    
    end_time = time.time() + DISCOVERY_DURATION_SEC
    while time.time() < end_time:
        scan_data = scan_wifi(os_type)
        for bssid, (ssid, _) in scan_data.items():
            discovered_bssids.add(bssid)
            bssid_to_ssid[bssid] = ssid
        time.sleep(0.5)
        
    print(f"[+] Discovery complete. Tracked {len(discovered_bssids)} stable Access Points.")
    return sorted(list(discovered_bssids)), bssid_to_ssid

def main():
    os_type = get_platform()
    tracked_bssids, bssid_map = run_discovery(os_type)
    
    if not tracked_bssids:
        print("[ERROR] No Wi-Fi networks detected. Ensure your Wi-Fi card is enabled.")
        sys.exit(1)
        
    headers = ["Timestamp"] + tracked_bssids
    
    with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    
    print(f"[+] Telemetry Matrix initiated -> Saved to {CSV_FILENAME}")
    print("[*] Harvester active. Press Ctrl+C to terminate recording.")
    print("-" * 65)
    
    try:
        while True:
            loop_start = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            live_scan = scan_wifi(os_type)
            row = [timestamp]
            active_scans_count = 0
            
            for bssid in tracked_bssids:
                if bssid in live_scan:
                    rssi = live_scan[bssid][1]
                    row.append(rssi)
                    active_scans_count += 1
                else:
                    row.append(DEFAULT_MISSING_RSSI)
                    
            with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                
            print(f"[{timestamp}] Logged snapshot. Online APs: {active_scans_count}/{len(tracked_bssids)}")
            
            elapsed = time.time() - loop_start
            sleep_time = (POLL_INTERVAL_MS / 1000.0) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n[+] Telemetry harvesting paused cleanly.")
        print(f"[+] Total structural snapshots saved: {sum(1 for _ in open(CSV_FILENAME)) - 1}")

if __name__ == "__main__":
    main()