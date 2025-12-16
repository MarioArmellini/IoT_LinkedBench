#!/usr/bin/env python3
"""
Hardware abstraction layer for LinkedBench sensors and actuators
"""

import RPi.GPIO as GPIO
import time
import logging
from typing import Tuple

try:
    import smbus2
except ImportError:
    smbus2 = None

logger = logging.getLogger('LinkedBench.Sensors')


class PressurePlate:
    """Grove pressure plate (button) with integrated LED"""
    
    def __init__(self, pin: int, name: str = "PressurePlate"):
        self.pin = pin
        self.name = name
        self.last_state = False
        self.debounce_time = 0.05  # 50ms debounce
        self.last_change = 0
        
        # Setup pin as input with pull-up
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        logger.info(f"{self.name} initialized on pin {self.pin}")
    
    def is_pressed(self) -> bool:
        """Check if pressure plate is pressed (with debouncing)"""
        current_time = time.time()
        
        # Read state (LOW = pressed due to pull-up)
        current_state = not GPIO.input(self.pin)
        
        # Debounce logic
        if current_state != self.last_state:
            if current_time - self.last_change > self.debounce_time:
                self.last_state = current_state
                self.last_change = current_time
                return current_state
        
        return self.last_state
    
    def set_led(self, state: bool):
        """Control integrated LED (if supported)"""
        # Note: For Grove button modules, LED is typically controlled by the button state
        # This method is here for API consistency
        pass


class ModeButton:
    """Button for mode selection"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.last_state = False
        self.debounce_time = 0.05
        self.last_change = 0
        
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        logger.info(f"Mode button initialized on pin {self.pin}")
    
    def is_pressed(self) -> bool:
        """Check if button is pressed (with debouncing)"""
        current_time = time.time()
        current_state = not GPIO.input(self.pin)
        
        if current_state != self.last_state:
            if current_time - self.last_change > self.debounce_time:
                self.last_state = current_state
                self.last_change = current_time
                return current_state
        
        return self.last_state


class GroveRGBLED:
    """Grove RGB LED (Chainable LED or similar)"""
    
    def __init__(self, pin: int):
        self.pin = pin
        self.current_color = (0, 0, 0)
        
        # For simple RGB control, we'll use software PWM on 3 pins
        # In production, you might use a dedicated RGB LED library
        # For now, we'll simulate with a single pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 100)  # 100Hz frequency
        self.pwm.start(0)
        
        logger.info(f"RGB LED initialized on pin {self.pin}")
    
    def set_color(self, r: int, g: int, b: int):
        """Set RGB color (0-255 for each component)"""
        self.current_color = (r, g, b)
        
        # Calculate brightness (simple average)
        brightness = (r + g + b) / (3 * 255) * 100
        self.pwm.ChangeDutyCycle(brightness)
        
        logger.debug(f"LED color set to RGB({r}, {g}, {b})")
    
    def off(self):
        """Turn off LED"""
        self.pwm.ChangeDutyCycle(0)
        self.current_color = (0, 0, 0)
    
    def cleanup(self):
        """Cleanup PWM"""
        self.pwm.stop()


class Buzzer:
    """Buzzer for audio feedback"""
    
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 2000)  # 2kHz tone
        
        logger.info(f"Buzzer initialized on pin {self.pin}")
    
    def beep(self, duration: float = 0.1, frequency: int = 2000):
        """Generate a beep"""
        self.pwm.ChangeFrequency(frequency)
        self.pwm.start(50)  # 50% duty cycle
        time.sleep(duration)
        self.pwm.stop()
    
    def beep_short(self):
        """Short confirmation beep"""
        self.beep(0.1, 2000)
    
    def beep_confirm(self):
        """Confirmation beep sequence"""
        self.beep(0.1, 2000)
        time.sleep(0.05)
        self.beep(0.1, 2500)
    
    def beep_error(self):
        """Error beep"""
        self.beep(0.3, 1000)
    
    def beep_startup(self):
        """Startup sequence"""
        self.beep(0.1, 1500)
        time.sleep(0.05)
        self.beep(0.1, 2000)
        time.sleep(0.05)
        self.beep(0.1, 2500)
    
    def cleanup(self):
        """Cleanup PWM"""
        self.pwm.stop()


class I2CDisplay:
    """I2C LCD Display (16x2 or 20x4)"""
    
    # LCD Commands
    LCD_CLEARDISPLAY = 0x01
    LCD_RETURNHOME = 0x02
    LCD_ENTRYMODESET = 0x04
    LCD_DISPLAYCONTROL = 0x08
    LCD_CURSORSHIFT = 0x10
    LCD_FUNCTIONSET = 0x20
    LCD_SETCGRAMADDR = 0x40
    LCD_SETDDRAMADDR = 0x80
    
    # Flags for display entry mode
    LCD_ENTRYRIGHT = 0x00
    LCD_ENTRYLEFT = 0x02
    LCD_ENTRYSHIFTINCREMENT = 0x01
    LCD_ENTRYSHIFTDECREMENT = 0x00
    
    # Flags for display on/off control
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00
    
    # Flags for display/cursor shift
    LCD_DISPLAYMOVE = 0x08
    LCD_CURSORMOVE = 0x00
    LCD_MOVERIGHT = 0x04
    LCD_MOVELEFT = 0x00
    
    # Flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00
    
    # Flags for backlight control
    LCD_BACKLIGHT = 0x08
    LCD_NOBACKLIGHT = 0x00
    
    En = 0b00000100  # Enable bit
    Rw = 0b00000010  # Read/Write bit
    Rs = 0b00000001  # Register select bit
    
    def __init__(self, i2c_addr: int = 0x27, bus: int = 1, width: int = 16, height: int = 2):
        self.i2c_addr = i2c_addr
        self.width = width
        self.height = height
        
        if smbus2 is None:
            logger.warning("smbus2 not available, display will be simulated")
            self.bus = None
        else:
            try:
                self.bus = smbus2.SMBus(bus)
                self._init_display()
                logger.info(f"I2C Display initialized at 0x{i2c_addr:02X}")
            except Exception as e:
                logger.error(f"Failed to initialize I2C display: {e}")
                self.bus = None
    
    def _init_display(self):
        """Initialize the display"""
        if self.bus is None:
            return
        
        try:
            # Initialize display
            self._write(0x03)
            self._write(0x03)
            self._write(0x03)
            self._write(0x02)
            
            self._write(self.LCD_FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS | self.LCD_4BITMODE)
            self._write(self.LCD_DISPLAYCONTROL | self.LCD_DISPLAYON)
            self._write(self.LCD_CLEARDISPLAY)
            self._write(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT)
            time.sleep(0.2)
        except Exception as e:
            logger.error(f"Display initialization error: {e}")
    
    def _write(self, cmd):
        """Write command to display"""
        if self.bus is None:
            return
        
        try:
            self.bus.write_byte(self.i2c_addr, cmd)
            time.sleep(0.0001)
        except Exception as e:
            logger.error(f"I2C write error: {e}")
    
    def _write_four_bits(self, data):
        """Write 4 bits"""
        if self.bus is None:
            return
        
        self.bus.write_byte(self.i2c_addr, data | self.LCD_BACKLIGHT)
        self._strobe(data)
    
    def _strobe(self, data):
        """Toggle enable"""
        if self.bus is None:
            return
        
        self.bus.write_byte(self.i2c_addr, data | self.En | self.LCD_BACKLIGHT)
        time.sleep(0.0005)
        self.bus.write_byte(self.i2c_addr, ((data & ~self.En) | self.LCD_BACKLIGHT))
        time.sleep(0.0001)
    
    def _write_byte(self, data, mode):
        """Write a byte in 4-bit mode"""
        if self.bus is None:
            return
        
        high = mode | (data & 0xF0) | self.LCD_BACKLIGHT
        low = mode | ((data << 4) & 0xF0) | self.LCD_BACKLIGHT
        
        self._write_four_bits(high)
        self._write_four_bits(low)
    
    def clear(self):
        """Clear display"""
        if self.bus is None:
            logger.info("[DISPLAY] Clear")
            return
        
        self._write_byte(self.LCD_CLEARDISPLAY, 0)
        time.sleep(0.002)
    
    def show_message(self, line1: str, line2: str = ""):
        """Show message on display"""
        if self.bus is None:
            logger.info(f"[DISPLAY] Line1: {line1}")
            logger.info(f"[DISPLAY] Line2: {line2}")
            return
        
        self.clear()
        
        # Write first line
        line1 = line1[:self.width].ljust(self.width)
        for char in line1:
            self._write_byte(ord(char), self.Rs)
        
        # Write second line if display has 2+ lines
        if self.height >= 2 and line2:
            line2 = line2[:self.width].ljust(self.width)
            self._write_byte(0xC0, 0)  # Move to second line
            for char in line2:
                self._write_byte(ord(char), self.Rs)
    
    def backlight(self, state: bool):
        """Control backlight"""
        if self.bus is None:
            return
        
        if state:
            self.bus.write_byte(self.i2c_addr, self.LCD_BACKLIGHT)
        else:
            self.bus.write_byte(self.i2c_addr, self.LCD_NOBACKLIGHT)
