# LinkedBench - Hardware Wiring Guide

## 🔌 Complete Wiring Diagram

### Pin Assignments (BCM Mode)

| Component | BCM Pin | Physical Pin | Type | Description |
|-----------|---------|--------------|------|-------------|
| Pressure Plate 1 | 18 | 12 | Digital Input | Seat detection with LED |
| Pressure Plate 2 | 16 | 36 | Digital Input | Seat detection with LED |
| Mode Button | 22 | 15 | Digital Input | Mode selection |
| Buzzer | 5 | 29 | PWM Output | Audio feedback |
| RGB LED | 24 | 18 | PWM Output | Visual mode indicator |
| I2C SDA | 2 | 3 | I2C Data | LCD Display data |
| I2C SCL | 3 | 5 | I2C Clock | LCD Display clock |
| Ground | GND | 6, 9, 14, 20, 25, 30, 34, 39 | Ground | Common ground |
| 3.3V Power | 3.3V | 1, 17 | Power | For 3.3V devices |
| 5V Power | 5V | 2, 4 | Power | For 5V devices |

## 📐 Raspberry Pi Pinout Reference

```
     3.3V  (1) (2)  5V
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND
    GPIO4  (7) (8)  GPIO14
      GND  (9) (10) GPIO15
   GPIO17 (11) (12) GPIO18  <-- Pressure 1
   GPIO27 (13) (14) GND
   GPIO22 (15) (16) GPIO23  <-- Mode Button (22)
     3.3V (17) (18) GPIO24  <-- RGB LED
   GPIO10 (19) (20) GND
    GPIO9 (21) (22) GPIO25
   GPIO11 (23) (24) GPIO8
      GND (25) (26) GPIO7
    GPIO0 (27) (28) GPIO1
    GPIO5 (29) (30) GND     <-- Buzzer (5)
    GPIO6 (31) (32) GPIO12
   GPIO13 (33) (34) GND
   GPIO19 (35) (36) GPIO16  <-- Pressure 2
   GPIO26 (37) (38) GPIO20
      GND (39) (40) GPIO21
```

## 🔧 Component Wiring Details

### 1. Pressure Plates (Grove Button Modules)

**Pressure Plate 1:**
```
Grove Button Module
┌─────────────┐
│  ⚪ ⚪ ⚪ ⚪  │
│  V  G  NC S │
└─────────────┘
   │  │     │
   │  │     └─→ Pin 18 (BCM) - Signal
   │  └───────→ GND - Ground
   └──────────→ 3.3V - Power
```

**Pressure Plate 2:**
```
Grove Button Module
┌─────────────┐
│  ⚪ ⚪ ⚪ ⚪  │
│  V  G  NC S │
└─────────────┘
   │  │     │
   │  │     └─→ Pin 16 (BCM) - Signal
   │  └───────→ GND - Ground
   └──────────→ 3.3V - Power
```

**Connection Notes:**
- VCC connects to 3.3V or 5V (check module specifications)
- GND connects to any ground pin
- SIG connects to designated GPIO pin
- NC (Not Connected) can be left unconnected
- Built-in LED typically lights when button is pressed

### 2. Mode Button

```
Grove Button
┌─────────────┐
│  ⚪ ⚪ ⚪ ⚪  │
│  V  G  NC S │
└─────────────┘
   │  │     │
   │  │     └─→ Pin 22 (BCM) - Signal
   │  └───────→ GND - Ground
   └──────────→ 3.3V - Power
```

**Connection Notes:**
- Configure with internal pull-up resistor (done in software)
- Button press connects signal to ground
- No external resistors needed

### 3. RGB LED (Grove Chainable LED or similar)

**Option A: Grove Chainable LED**
```
Grove Chainable LED
┌─────────────┐
│  ⚪ ⚪ ⚪ ⚪  │
│  V  G  CI CO│
└─────────────┘
   │  │  │
   │  │  └────→ Pin 24 (BCM) - Clock In
   │  └───────→ GND - Ground
   └──────────→ 5V - Power
```

**Option B: Simple RGB LED**
```
RGB LED (Common Cathode)
    ┌─────┐
  R │     │ B
  ──┤     ├──
    │ LED │
  G │     │ -
  ──┤     ├──
    └─────┘
     │ │ │
     │ │ └──→ GND - Ground
     │ └────→ Pin 24 via resistor
     └──────→ Additional pins if 3-pin RGB
```

**Connection Notes:**
- For simple RGB LED, use 220Ω resistors on each color pin
- Grove Chainable LED requires clock and data pins
- Adjust code based on LED type used

### 4. Buzzer

```
Grove Buzzer (Passive)
┌─────────────┐
│  ⚪ ⚪      │
│  +  -      │
└─────────────┘
   │  │
   │  └────→ GND - Ground
   └───────→ Pin 5 (BCM) - Signal
```

**Connection Notes:**
- Passive buzzer for tone generation (required for PWM control)
- Active buzzer works but can't change frequency
- Some buzzers may need 5V instead of GPIO output
- Consider transistor amplifier for louder sound

### 5. I2C LCD Display

```
I2C LCD Module (16x2 or 20x4)
┌──────────────────┐
│  ⚪ ⚪ ⚪ ⚪      │
│  G  V  SD SC     │
└──────────────────┘
    │  │  │  │
    │  │  │  └────→ Pin 3 (BCM) - SCL (Clock)
    │  │  └───────→ Pin 2 (BCM) - SDA (Data)
    │  └──────────→ 5V - Power
    └─────────────→ GND - Ground
```

**Connection Notes:**
- Most I2C displays use 5V power
- I2C address is typically 0x27 or 0x3F
- Check with: `sudo i2cdetect -y 1`
- Some displays have built-in pull-up resistors
- May need external 4.7kΩ pull-ups if not working

## ⚡ Power Considerations

### Power Requirements

| Component | Voltage | Current | Notes |
|-----------|---------|---------|-------|
| Raspberry Pi | 5V | 2-3A | Via USB-C or GPIO |
| LCD Display | 5V | 100-200mA | With backlight |
| RGB LED | 3.3-5V | 20-60mA | Per color |
| Buzzer | 3.3-5V | 10-30mA | Depends on type |
| Buttons | 3.3V | <1mA | Minimal |

### Power Supply Options

**Option 1: USB Power (Recommended)**
```
Wall Adapter (5V, 3A)
        │
        ├─→ Raspberry Pi USB-C
        └─→ All sensors via GPIO pins
```

**Option 2: External Power for Sensors**
```
Wall Adapter → Raspberry Pi USB-C
Separate 5V Supply → Sensors (common GND with Pi)
```

**Important Notes:**
- Always connect grounds together (common ground)
- Don't exceed 50mA total from 3.3V pins
- GPIO pins can source ~16mA each
- Use transistors for high-current devices

## 🛡️ Safety & Best Practices

### DO's ✅
- ✅ Double-check connections before powering on
- ✅ Use appropriate resistors for LEDs
- ✅ Connect all grounds together
- ✅ Use heat shrink or electrical tape on exposed wires
- ✅ Secure components to prevent shorts
- ✅ Test with multimeter when uncertain
- ✅ Power off before changing connections

### DON'Ts ❌
- ❌ Never connect 5V directly to 3.3V GPIO pins
- ❌ Don't exceed 16mA per GPIO pin
- ❌ Don't connect motors directly to GPIO
- ❌ Avoid shorts between power and ground
- ❌ Don't hot-plug I2C devices
- ❌ Never exceed 50mA total from 3.3V supply

## 🧪 Testing Individual Components

### Test Pressure Plates
```bash
# Monitor GPIO input
gpio -g mode 18 in
gpio -g read 18  # Should be 1 (high) when not pressed
# Press button, run again - should be 0 (low)
```

### Test Buzzer
```bash
# Generate tone with PWM
gpio -g mode 5 pwm
gpio pwm-ms
gpio pwmc 192
gpio pwmr 200
gpio -g pwm 5 100  # 50% duty cycle
# Should hear tone
gpio -g pwm 5 0    # Stop
```

### Test I2C Display
```bash
# Detect I2C devices
sudo i2cdetect -y 1

# Should show device at 0x27 (or 0x3F)
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- -- 
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
```

### Test RGB LED
```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)

pwm = GPIO.PWM(24, 100)
pwm.start(0)

for brightness in range(0, 101, 10):
    pwm.ChangeDutyCycle(brightness)
    time.sleep(0.2)

pwm.stop()
GPIO.cleanup()
```

## 📸 Assembly Photos

It's recommended to take photos of your assembly at these stages:

1. **Components Laid Out**: All parts before connection
2. **Breadboard Assembly**: Components on breadboard
3. **Wiring in Progress**: Partially completed wiring
4. **Completed Assembly**: Fully connected system
5. **Running System**: System powered on and working
6. **Final Installation**: Installed on bench (if applicable)

## 🔍 Troubleshooting Wiring Issues

### No Response from Sensor
1. Check power connection (use multimeter)
2. Verify ground connection
3. Test signal continuity
4. Check pin number (BCM vs physical)
5. Try different pin

### Intermittent Operation
1. Check for loose connections
2. Verify adequate power supply
3. Look for shorts or crossed wires
4. Check wire gauge (use 22-26 AWG)
5. Secure breadboard connections

### I2C Device Not Detected
1. Check SDA/SCL not swapped
2. Verify I2C enabled in raspi-config
3. Check pull-up resistors
4. Test with different I2C address
5. Verify 5V power (not 3.3V)

## 📋 Wiring Checklist

Before powering on:

- [ ] All grounds connected together
- [ ] Power connections correct (3.3V vs 5V)
- [ ] No shorts between adjacent pins
- [ ] Correct pin numbers (BCM mode)
- [ ] Resistors in place for LEDs
- [ ] I2C pull-ups present (if needed)
- [ ] All components secured
- [ ] Wires properly insulated
- [ ] No loose connections
- [ ] Multimeter tested all connections

## 🎓 Educational Notes

This wiring setup demonstrates:

- **GPIO Digital I/O**: Button inputs with pull-up resistors
- **PWM Output**: LED brightness and buzzer tone control
- **I2C Communication**: Serial bus for display
- **Interrupt Handling**: Can be added for button events
- **Power Management**: Proper current distribution
- **Signal Integrity**: Pull-up/pull-down resistors

Perfect for learning embedded systems and IoT hardware integration!

---

**Safety First!** Always disconnect power before modifying connections.
**Test Incrementally!** Connect and test one component at a time.
**Document Everything!** Take photos and notes of your setup.
