# Wi-Fi Shadow: Passive RF Sensing Radar

**Wi-Fi Shadow** is an opportunistic RF sensing application that transforms an ordinary laptop into a passive occupancy and motion detector. By leveraging ambient Wi-Fi signals as a continuous radar illumination field, the system detects physical disruptions in the environment without relying on cameras or dedicated sensing hardware.

---

## How It Works

### The Physics

The human body is composed of approximately 70% water, which naturally attenuates, scatters, and refracts radio frequency (RF) signals. When a person moves through a room, they disturb the otherwise stable multipath propagation of surrounding Wi-Fi signals. These disturbances appear as high-variance fluctuations in the Received Signal Strength Indicator (RSSI).

### The AI

The system uses an unsupervised **Isolation Forest** model trained exclusively on a quiet, motionless baseline dataset collected from the target environment. The model learns the RF “fingerprint” of an empty room and identifies deviations from that baseline as physical motion anomalies.

---

## File Descriptions

### `harvester.py`

Automatically detects the operating system (Windows or Linux) and executes native command-line Wi-Fi scans to collect uncached wireless telemetry. The script processes and exports the data as a pivoted time-series matrix for training.

### `wifishadow_daemon.py`

The live deployment daemon. It loads the trained AI model, continuously captures real-time Wi-Fi signal snapshots every 400 milliseconds, computes variance profiles, and emits motion detection alerts when anomalies are detected.

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Terminal sessions must be run with Administrative (Windows) or Root (Linux) privileges to force active Wi-Fi hardware scans.

---

### 2. Collect Baseline Data

Run the harvester in an undisturbed empty room for several minutes to generate the baseline dataset:

```bash
python harvester.py
```

This will create:

```text
wifi_signal_matrix.csv
```

---

### 3. Train the Model

1. Upload `wifi_signal_matrix.csv` to Google Colab.
2. Execute the preprocessing and training notebook/scripts.
3. Download the generated model file:

```text
wifishadow_model.p
```

---

### 4. Deploy the Live Radar

Place `wifishadow_model.p` in the same directory as the scripts and start the daemon:

```bash
python wifishadow_daemon.py
```

The system will begin monitoring live RF fluctuations and output motion alerts in real time.

---

## Features

* Passive RF sensing using existing Wi-Fi infrastructure
* No cameras or wearable devices required
* Cross-platform telemetry collection (Windows/Linux)
* Real-time motion anomaly detection
* Lightweight unsupervised machine learning pipeline
* Works with commodity consumer hardware

---

## Research Concept

Wi-Fi Shadow explores the concept of passive radar sensing through opportunistic RF analysis. Rather than transmitting its own signal, the system observes disruptions in ambient wireless propagation caused by human movement.

This project demonstrates how low-cost wireless telemetry combined with anomaly detection can approximate environmental awareness using only existing Wi-Fi signals.

---

## Disclaimer

This project is intended strictly for educational and research purposes. RF sensing accuracy can vary significantly depending on environmental conditions, Wi-Fi density, hardware limitations, and signal interference.
