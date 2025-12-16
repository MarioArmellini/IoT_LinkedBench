# LinkedBench IoT System

**Smart bench system for campus social connection**

LinkedBench is an End-to-End IoT solution developed for the "IoT Application Development" course (2025-2026). It strengthens social cohesion on campus by transforming traditional benches into interactive hubs that detect presence, manage social availability, and analyze usage patterns.

## 🎯 Project Overview & Scope

### Concept
The system transforms a passive furniture piece into a smart object using:
* **Input Sensors:** Pressure plates (GPIO) and Buttons (GPIO) to detect presence and intent.
* **Feedback Actuators:** RGB LEDs (GPIO) and Buzzer (PWM) for immediate feedback.
* **Visual Interface:** I2C LCD Display for status information.
* **Connectivity:** MQTT for cloud integration and REST API for remote management.
* **Data Intelligence:** Local SQLite storage and data analytics.

### Functional Description
When a user sits down, the pressure sensors trigger an "Occupied" state. The user can then toggle through social modes (Studying, Open to Chat, etc.) using the physical button. The system logs these events locally and publishes them to the MQTT broker for real-time monitoring. Parallel threads manage the REST API server to allow external queries about the bench status.

## 🏗️ Technical Architecture & Code Structure

This project is structured around a multi-threaded Python application orchestrated by `linkedbench.py`.

### System Logic
1.  **Hardware Layer (`sensors.py`):**
    * Abstracts the complexity of GPIO (Buttons/LEDs) and I2C (Display).
    * Implements debounce logic for buttons and PWM control for the buzzer.
2.  **Data Layer (`database.py`):**
    * Manages a persistent SQLite connection.
    * Handles schema creation and atomic insertions of events.
3.  **Communication Layer:**
    * **MQTT (`mqtt_client.py`):** Publishes JSON payloads to the broker asynchronously.
    * **REST API (`rest_api.py`):** A Flask-based web server running on a separate thread to serve status and stats without blocking sensor loops.
4.  **Orchestrator (`linkedbench.py`):**
    * Main entry point. Initializes all subsystems, manages the main event loop, and handles graceful shutdowns (signal handling).

### Project Tree
```text
linkedbench-iot/
├── linkedbench.py      # MAIN: Orchestrates threads and event loop
├── sensors.py          # DRIVER: Hardware abstraction (GPIO/I2C classes)
├── mqtt_client.py      # COMMS: MQTT Publisher/Subscriber logic
├── rest_api.py         # COMMS: Flask REST API endpoints
├── database.py         # DATA: SQLite database management
├── config.ini          # CONFIG: Central configuration (Pins, IP, Creds)
└── install.sh          # OPS: Automated deployment script