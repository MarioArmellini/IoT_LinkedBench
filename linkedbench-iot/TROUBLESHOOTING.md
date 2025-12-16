# LinkedBench - Detailed Troubleshooting Guide

## Hardware Issues

### Pressure Sensors Not Working

**Symptoms:**
- Sensors don't detect presses
- Inconsistent readings
- LED doesn't light up

**Diagnosis:**
```bash
# Test GPIO input
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Testing Pin 18 - Press button repeatedly...")
for i in range(50):
    state = GPIO.input(18)
    print(f"State: {state}", end='\r')
    time.sleep(0.1)

GPIO.cleanup()
EOF
```

**Solutions:**
1. Check wiring connections
2. Verify 3.3V/5V power supply
3. Test with multimeter (continuity mode)
4. Replace sensor if faulty
5. Check pull-up resistor configuration

### RGB LED Not Working

**Symptoms:**
- LED doesn't light up
- Wrong colors displayed
- Flickering

**Diagnosis:**
```bash
# Test LED with simple script
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)

pwm = GPIO.PWM(24, 100)
pwm.start(0)

# Gradually increase brightness
for dc in range(0, 101, 10):
    pwm.ChangeDutyCycle(dc)
    print(f"Brightness: {dc}%")
    time.sleep(0.5)

pwm.stop()
GPIO.cleanup()
EOF
```

**Solutions:**
1. Check if Grove RGB LED requires specific library
2. Verify pin connections (usually needs 3 pins: R, G, B)
3. Check common cathode vs common anode configuration
4. Consider using WS2812B library for addressable LEDs
5. Test with lower brightness (some LEDs are very bright)

### I2C Display Issues

**Symptoms:**
- Display not detected
- Garbled text
- Backlight works but no text

**Diagnosis:**
```bash
# 1. Check I2C is enabled
ls /dev/i2c*

# 2. Detect devices
sudo i2cdetect -y 1

# 3. Read from device
sudo i2cget -y 1 0x27 0x00

# 4. Test with simple script
python3 << 'EOF'
import smbus2
import time

bus = smbus2.SMBus(1)
addr = 0x27

try:
    bus.write_byte(addr, 0x00)
    print("Display found at 0x27!")
except:
    print("Display not found. Try 0x3F:")
    try:
        addr = 0x3F
        bus.write_byte(addr, 0x00)
        print("Display found at 0x3F!")
    except:
        print("Display not detected")
EOF
```

**Common I2C Addresses:**
- 0x27 (most common)
- 0x3F (alternative)
- 0x20, 0x38 (less common)

**Solutions:**
1. Enable I2C in raspi-config
2. Check wiring: SDA to SDA, SCL to SCL
3. Verify voltage (5V for most displays)
4. Try different I2C address in config.ini
5. Add pull-up resistors (4.7kΩ) if needed
6. Check for I2C bus conflicts
7. Slow down I2C clock speed:
   ```bash
   # Add to /boot/config.txt
   dtparam=i2c_arm=on,i2c_arm_baudrate=10000
   ```

### Buzzer Issues

**Symptoms:**
- No sound
- Distorted sound
- Continuous buzzing

**Diagnosis:**
```bash
# Test buzzer
python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT)

# Test with PWM
pwm = GPIO.PWM(5, 2000)  # 2kHz
pwm.start(50)
time.sleep(0.5)
pwm.stop()

# Test different frequencies
for freq in [500, 1000, 2000, 3000]:
    pwm.ChangeFrequency(freq)
    pwm.start(50)
    print(f"Frequency: {freq}Hz")
    time.sleep(0.3)
    pwm.stop()
    time.sleep(0.1)

GPIO.cleanup()
EOF
```

**Solutions:**
1. Check polarity (if polarized buzzer)
2. Verify voltage requirements
3. Add transistor for current amplification
4. Check PWM functionality
5. Adjust frequency (1-4kHz typical range)

## Software Issues

### Import Errors

**Problem:** `ModuleNotFoundError`

**Solutions:**
```bash
# Option 1: System-wide install
pip3 install --break-system-packages <package>

# Option 2: Virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Option 3: Use apt for system packages
sudo apt-get install python3-<package>
```

**Common packages:**
```bash
# RPi.GPIO
sudo apt-get install python3-rpi.gpio

# smbus
sudo apt-get install python3-smbus

# paho-mqtt
pip3 install --break-system-packages paho-mqtt

# Flask
pip3 install --break-system-packages flask flask-cors
```

### Database Errors

**Problem:** `sqlite3.OperationalError: database is locked`

**Solutions:**
1. Close other connections
2. Increase timeout:
   ```python
   conn = sqlite3.connect(db_path, timeout=30.0)
   ```
3. Check file permissions
4. Use WAL mode:
   ```python
   conn.execute("PRAGMA journal_mode=WAL")
   ```

**Problem:** `PermissionError: [Errno 13]`

**Solutions:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER /var/lib/linkedbench

# Fix file permissions
sudo chmod 664 /var/lib/linkedbench/events.db
```

### MQTT Connection Issues

**Problem:** Cannot connect to broker

**Diagnosis:**
```bash
# Test connectivity
ping test.mosquitto.org

# Test MQTT with mosquitto tools
mosquitto_pub -h test.mosquitto.org -t "test" -m "hello"
mosquitto_sub -h test.mosquitto.org -t "test"
```

**Solutions:**
1. Check broker address and port
2. Verify firewall rules
3. Test with public broker first
4. Check credentials if required
5. Enable MQTT in config.ini

### REST API Issues

**Problem:** API not accessible from other devices

**Solutions:**
```bash
# Check if Flask is running
netstat -tulpn | grep :5000

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Verify host setting (should be 0.0.0.0)
# In rest_api.py: app.run(host='0.0.0.0', port=5000)

# Test locally first
curl http://localhost:5000/api/status

# Then from network
curl http://raspberry-pi-ip:5000/api/status
```

### Threading Issues

**Problem:** Deadlocks or race conditions

**Solutions:**
1. Check lock usage is consistent
2. Add timeout to locks
3. Use context managers:
   ```python
   with self.lock:
       # Critical section
   ```
4. Review thread synchronization
5. Add more logging to identify issues

## System Issues

### High CPU Usage

**Diagnosis:**
```bash
# Check CPU usage
top
htop

# Check specific process
ps aux | grep python

# Check temperature
vcgencmd measure_temp
```

**Solutions:**
1. Increase polling intervals
2. Reduce logging verbosity
3. Optimize sensor reading loops
4. Check for infinite loops
5. Use hardware interrupts instead of polling

### Memory Issues

**Diagnosis:**
```bash
# Check memory
free -h

# Check swap
swapon --show

# Monitor process memory
watch -n 1 'ps aux | grep linkedbench'
```

**Solutions:**
1. Limit database query results
2. Clear old events periodically
3. Increase swap size
4. Reduce concurrent connections
5. Check for memory leaks

### Service Won't Start

**Diagnosis:**
```bash
# Check service status
sudo systemctl status linkedbench

# View logs
sudo journalctl -u linkedbench -n 100 --no-pager

# Check service file syntax
sudo systemctl verify linkedbench.service

# Test manual start
cd /opt/linkedbench
sudo -u $USER python3 linkedbench.py
```

**Solutions:**
1. Check file paths in service file
2. Verify user permissions
3. Check Python path
4. Ensure all dependencies installed
5. Review systemctl logs for errors

## Network Issues

### Cannot Access from Outside Network

**Solutions:**
```bash
# Find Pi's IP
hostname -I

# Port forwarding on router
# Forward port 5000 to Pi's IP

# Use dynamic DNS if IP changes
# Services: No-IP, DuckDNS, etc.

# Or use VPN/Tailscale for secure access
```

### MQTT Behind Firewall

**Solutions:**
1. Use WebSocket connection (port 8083)
2. Use MQTT over TLS (port 8883)
3. Configure router port forwarding
4. Use cloud MQTT broker
5. Set up reverse proxy

## Performance Optimization

### Reduce Latency

```python
# Optimize sensor polling
POLL_INTERVAL = 0.05  # 50ms instead of 100ms

# Use interrupt-based detection
GPIO.add_event_detect(pin, GPIO.BOTH, 
                      callback=callback_function,
                      bouncetime=50)

# Batch database writes
events_buffer = []
# ... collect events ...
db.save_events_batch(events_buffer)
```

### Optimize Database

```bash
# Vacuum database
sqlite3 /var/lib/linkedbench/events.db "VACUUM;"

# Add indexes
sqlite3 /var/lib/linkedbench/events.db << EOF
CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_bench_id ON events(bench_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
EOF

# Enable WAL mode
sqlite3 /var/lib/linkedbench/events.db "PRAGMA journal_mode=WAL;"
```

## Recovery Procedures

### Reset System

```bash
# Stop service
sudo systemctl stop linkedbench

# Backup database
cp /var/lib/linkedbench/events.db /var/lib/linkedbench/events.db.backup

# Clear logs
sudo truncate -s 0 /var/log/linkedbench.log

# Restart
sudo systemctl start linkedbench
```

### Factory Reset

```bash
# Stop service
sudo systemctl stop linkedbench

# Remove data
sudo rm -rf /var/lib/linkedbench/*

# Remove logs
sudo rm /var/log/linkedbench.log

# Reinstall
cd /opt/linkedbench
sudo bash install.sh
```

### Database Corruption

```bash
# Stop service
sudo systemctl stop linkedbench

# Dump database
sqlite3 /var/lib/linkedbench/events.db .dump > backup.sql

# Delete corrupted database
rm /var/lib/linkedbench/events.db

# Restore from dump
sqlite3 /var/lib/linkedbench/events.db < backup.sql

# Or start fresh (data loss!)
rm /var/lib/linkedbench/events.db
# Service will create new database on start
```

## Getting Help

### Collect Debug Information

```bash
#!/bin/bash
# debug_info.sh - Collect system information

echo "=== System Info ===" > debug_info.txt
uname -a >> debug_info.txt
python3 --version >> debug_info.txt

echo -e "\n=== I2C Devices ===" >> debug_info.txt
sudo i2cdetect -y 1 >> debug_info.txt 2>&1

echo -e "\n=== GPIO State ===" >> debug_info.txt
gpio readall >> debug_info.txt 2>&1

echo -e "\n=== Service Status ===" >> debug_info.txt
sudo systemctl status linkedbench >> debug_info.txt 2>&1

echo -e "\n=== Recent Logs ===" >> debug_info.txt
sudo journalctl -u linkedbench -n 50 >> debug_info.txt 2>&1

echo -e "\n=== Python Packages ===" >> debug_info.txt
pip3 list | grep -i "gpio\|mqtt\|flask\|smbus" >> debug_info.txt

echo -e "\n=== Disk Space ===" >> debug_info.txt
df -h >> debug_info.txt

echo -e "\n=== Memory ===" >> debug_info.txt
free -h >> debug_info.txt

echo "Debug info saved to debug_info.txt"
```

### Contact & Support

1. Check README.md first
2. Review logs: `sudo journalctl -u linkedbench -f`
3. Test components individually
4. Collect debug information
5. Check GitHub issues (if repository exists)
6. Contact course instructor

## Quick Reference

### Useful Commands

```bash
# Service management
sudo systemctl start linkedbench
sudo systemctl stop linkedbench
sudo systemctl restart linkedbench
sudo systemctl status linkedbench
sudo journalctl -u linkedbench -f

# I2C
sudo i2cdetect -y 1
sudo i2cdump -y 1 0x27

# GPIO
gpio readall
pinout

# Network
hostname -I
sudo netstat -tulpn | grep :5000

# Database
sqlite3 /var/lib/linkedbench/events.db "SELECT * FROM events LIMIT 10;"

# Logs
tail -f /var/log/linkedbench.log
sudo journalctl -u linkedbench --since today

# Process
ps aux | grep python
top -p $(pgrep -f linkedbench)

# Disk
df -h /var/lib/linkedbench
du -sh /var/lib/linkedbench/*
```

### Emergency Commands

```bash
# Force stop
sudo killall python3

# Clean restart
sudo systemctl stop linkedbench
sudo rm /var/lib/linkedbench/events.db-wal
sudo systemctl start linkedbench

# Check errors
sudo journalctl -u linkedbench -p err

# Reboot
sudo reboot
```
