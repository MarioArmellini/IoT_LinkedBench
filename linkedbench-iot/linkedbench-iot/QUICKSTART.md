# LinkedBench IoT - Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Prerequisites
- Raspberry Pi with Raspberry Pi OS installed
- Grove sensors connected (see pin configuration below)
- Internet connection

### 2. Pin Configuration
```
Pin 18 (BCM): Pressure Plate 1
Pin 16 (BCM): Pressure Plate 2  
Pin 22 (BCM): Mode Button
Pin 5  (BCM): Buzzer
Pin 24 (BCM): RGB LED
I2C (SDA/SCL): LCD Display
```

### 3. Installation (One Command)
```bash
cd /home/pi
git clone YOUR_REPO_URL linkedbench-iot
cd linkedbench-iot
sudo bash install.sh
```

Wait for installation to complete, then reboot if prompted:
```bash
sudo reboot
```

### 4. Test the System
```bash
cd /opt/linkedbench
python3 linkedbench.py
```

You should see:
- LEDs lighting up
- Buzzer playing startup sound
- LCD showing "LinkedBench Available"
- Console logs showing system status

**Test the sensors:**
- Press the pressure plates → Should detect occupation
- Press mode button → Should cycle through modes
- Check LED colors change
- Watch console for events

Press `Ctrl+C` to stop.

### 5. Enable Autostart
```bash
sudo systemctl enable linkedbench
sudo systemctl start linkedbench
```

### 6. Access Dashboard
Open browser and go to:
```
http://raspberry-pi-ip:5000
```

Or open the dashboard.html file included in the project.

### 7. Check Status
```bash
# View logs
sudo journalctl -u linkedbench -f

# Check service status
sudo systemctl status linkedbench

# Test API
curl http://localhost:5000/api/status
```

## 🎯 Common First-Time Issues

### Issue: "No I2C device found"
```bash
# Enable I2C
sudo raspi-config
# Interface Options -> I2C -> Enable
sudo reboot

# Test
sudo i2cdetect -y 1
```

### Issue: "Permission denied on GPIO"
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

### Issue: "Module not found"
```bash
pip3 install --break-system-packages -r requirements.txt
```

### Issue: "Cannot connect to MQTT"
- Check internet connection
- Try a different broker in config.ini
- MQTT is optional - system works without it

## 📱 Quick API Examples

### Get Status
```bash
curl http://localhost:5000/api/status
```

### Change Mode
```bash
curl -X POST http://localhost:5000/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": 2}'
```

### Get Recent Events
```bash
curl http://localhost:5000/api/events?limit=5
```

### Get Statistics
```bash
curl http://localhost:5000/api/statistics?days=7
```

## 🔧 Customization

### Change Bench ID
Edit `/opt/linkedbench/config.ini`:
```ini
[bench]
bench_id = YOUR_CUSTOM_ID
```

Restart service:
```bash
sudo systemctl restart linkedbench
```

### Change Colors
Edit `linkedbench.py`, modify MODE_COLORS dictionary.

### Change API Port
Edit `config.ini`:
```ini
[api]
port = 8080
```

## 📚 Next Steps

1. **Read the full README.md** for detailed documentation
2. **Check TROUBLESHOOTING.md** if you encounter issues
3. **Customize config.ini** for your setup
4. **Set up cloud integration** (ThingSpeak, ThingsBoard, etc.)
5. **Create a custom dashboard** using the REST API
6. **Add more sensors** as extensions

## 🆘 Getting Help

1. Check logs: `sudo journalctl -u linkedbench -f`
2. Run tests: `python3 test_system.py`
3. Read TROUBLESHOOTING.md
4. Check GitHub issues
5. Contact course instructor

## 🎓 For Academic Submission

Make sure to:
- [ ] Document your setup in README.md
- [ ] Add your names to the project
- [ ] Include photos of hardware setup
- [ ] Record a demo video
- [ ] Push code to GitHub
- [ ] Include this file in your submission

Good luck! 🚀
