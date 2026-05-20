# Wi-Fi Shadow: Passive RF Sensing Radar

**Wi-Fi Shadow** is an opportunistic RF sensing application that turns an ordinary laptop into a passive occupancy and motion detector. By treating ambient Wi-Fi signals as a continuous radar illumination field, the system tracks physical disruptions in the environment without using cameras.

## How It Works
**The Physics:** The human body is roughly 70% water, meaning it attenuates, scatters, and refracts RF signals. When someone moves through a room, they disrupt static multipath propagation, causing high-variance fluctuations in the Received Signal Strength Indicator (RSSI).
**The AI:** An unsupervised **Isolation Forest** model is trained inside Google Colab exclusively on a quiet, still-room baseline dataset. It learns the "fingerprint" of the empty room and highlights dynamic changes as physical structural anomalies.

## File Descriptions
`harvester.py`: Automatically detects the operating system (Windows or Linux) and executes native command-line queries to gather un-cached Wi-Fi telemetry. It outputs a pivoted time-series matrix.
`wifishadow_daemon.py`: The live background deployment script. It loads the trained AI model, collects real-time Wi-Fi signal snapshots every 400 milliseconds, extracts variance profiles, and outputs motion alerts.

## Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
  Note: Terminal sessions must be run with Administrative/Root privileges to force active Wi-Fi hardware scans. 
  
2. **Collect Baseline Data:**
   Run the harvester undisturbed in an empty room for a few minutes to populate your baseline dataset `wifi_signal_matrix.csv`.
   ```bash
   python harvester.py

3. **Train the Model:**
   Upload `wifi_signal_matrix.csv` to Google Colab, execute the filtering and training scripts, and download the resulting `wifishadow_model.p` binary file.

4. **Deploy the Live Radar:**
   Place the `wifishadow_model.p` file in the same directory as your scripts and start the daemon:
    ```bash
    python wifishadow_daemon.py
