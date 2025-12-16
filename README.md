[README.md](https://github.com/user-attachments/files/24193993/README.md)
# LinkedBench IoT System

**Smart social bench for campus interaction**

LinkedBench is an end-to-end Internet of Things (IoT) system designed to transform traditional campus benches into intelligent social interaction points. The system detects physical occupancy, allows users to express their social availability, provides visual and audio feedback, and publishes data to cloud services for monitoring and analysis.

This project has been developed as the final assignment for the IoT course and builds upon the initial idea proposed during the IoT Challenge.

---

## Project Objectives

- Detect bench occupancy using physical pressure sensors
- Interpret occupancy semantically (0, 1 or 2 users)
- Allow social interaction modes only when applicable
- Provide immediate visual and audio feedback
- Expose system state via REST API
- Publish events using MQTT
- Store events locally for later analysis
- Demonstrate a complete end-to-end IoT solution

---

## System States and Logic

The system operates as a **state-driven system**, where physical occupancy determines the available interactions.

### Physical States (Automatic)

| Occupancy | State        | Mode Button | LED |
|----------|--------------|-------------|-----|
| 0 users  | Empty        | Disabled    | OFF |
| 1 user   | Available    | Enabled     | SOLID |
| 2 users  | Study Buddy  | Disabled    | SOLID |

### User-Selectable Modes (Only with 1 user)

When exactly **one user** is seated, the mode button cycles through:

| Mode | Meaning | LED Pattern |
|-----|--------|-------------|
| Studying | Do not disturb | FAST blinking |
| Open to Chat | Willing to interact | MEDIUM blinking |

Mode selection is automatically blocked when the bench is empty or when two users are detected.

---

## Hardware Components

- Raspberry Pi (Raspberry Pi OS)
- 2× Pressure Plates (GPIO)
- 1× Mode Selection Button (GPIO)
- RGB LED (GPIO)
- Buzzer (GPIO)
- I2C LCD Display (16×2)

### GPIO Pin Configuration (BCM)

- BCM 18 → Pressure Plate 1
- BCM 16 → Pressure Plate 2
- BCM 22 → Mode Button
- BCM 24 → RGB LED
- BCM 5 → Buzzer
- I2C → LCD Display (0x3E)

---

## Software Architecture

- **linkedbench2.py** → Core system logic
- **sensors2.py** → Hardware abstraction layer
- **REST API (Flask)** → Remote monitoring and control
- **MQTT** → Event publication
- **SQLite** → Local event storage
- **Multithreading** → Sensors, API, MQTT, monitoring
- **Systemd service** → Automatic startup

---

## Installation

### Requirements
- Python 3.7+
- Raspberry Pi OS
- Enabled I2C interface

### Setup

```bash
git clone https://github.com/yourusername/linkedbench-iot.git
cd linkedbench-iot
sudo bash install.sh
sudo reboot
```
## Running the System

### Manual Execution

```bash
python3 linkedbench2.py
python3 linkedbench2.py --bench-id BENCH_002
```

## As a System Service

```bash
sudo systemctl enable linkedbench
sudo systemctl start linkedbench
sudo systemctl status linkedbench
```

## REST API (Overview)

- GET /api/status → Current system state

- POST /api/mode → Change mode (only if allowed)

- GET /api/events → Retrieve recent events

Example:

```bash
curl http://localhost:5000/api/status
```

## MQTT Integration

Events are published in JSON format.

```bash
linkedbench/{bench_id}/events
linkedbench/{bench_id}/status
```

## Data Storage

Events are stored locally using SQLite.

Example queries:

```bash
SELECT COUNT(*) FROM events;
SELECT mode_name, COUNT(*) FROM events GROUP BY mode_name;
SELECT AVG(cpu_temp) FROM system_health;
```

## Future Improvements
- Bluetooth integration

- Grafana / InfluxDB dashboards

- Mobile application

- Advanced data analytics

- Notification system (email / Telegram)
