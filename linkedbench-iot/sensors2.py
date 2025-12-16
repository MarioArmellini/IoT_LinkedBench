#!/usr/bin/env python3
"""
Hardware abstraction layer for LinkedBench - VERSION FINAL CORREGIDA
Incluye: Debounce 0.2s, Clase BlinkingLED con hilos y velocidades.
"""

import RPi.GPIO as GPIO
import time
import logging
import threading

try:
    import smbus2
except ImportError:
    smbus2 = None

logger = logging.getLogger('LinkedBench.Sensors')

class PressurePlate:
    """
    CONFIGURACIÓN INVERTIDA PARA GROVE LED BUTTON
    Asume que:
    - Cable AMARILLO (Pin base) = LED
    - Cable BLANCO (Pin base + 1) = BOTÓN
    """
    def __init__(self, pin: int, name: str = "PressurePlate"):
        # AQUÍ ESTÁ EL CAMBIO MÁGICO:
        self.led_pin = pin          # Asignamos el 18 (Amarillo) al LED
        self.btn_pin = pin + 1      # Asignamos el 19 (Blanco) al BOTÓN
        
        self.name = name
        self.last_state = False
        self.debounce_time = 0.2
        self.last_change = 0

        # Configuramos el botón (Pin 19) como entrada con resistencia PULL-DOWN
        # Esto es vital: obliga al botón a marcar "0" si no se toca.
        GPIO.setup(self.btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Configuramos el LED (Pin 18) como salida
        GPIO.setup(self.led_pin, GPIO.OUT)
        
        # Nos aseguramos que el LED empiece apagado
        self.set_led(False)

    def is_pressed(self) -> bool:
        current_time = time.time()
        # Leemos el pin BLANCO (19)
        current_state = not GPIO.input(self.btn_pin)

        # Encendemos el LED si se pulsa (Feedback visual)
        if current_state:
            self.set_led(True)
        else:
            self.set_led(False)

        # Lógica para evitar rebotes (falsos contactos rápidos)
        if current_state != self.last_state:
            if current_time - self.last_change > self.debounce_time:
                self.last_state = current_state
                self.last_change = current_time
                return current_state
        return self.last_state

    def set_led(self, state: bool):
        # Controlamos el pin AMARILLO (18)
        GPIO.output(self.led_pin, GPIO.HIGH if state else GPIO.LOW)

class ModeButton:
    """
    Botón lateral para cambiar modos
    """
    def __init__(self, pin: int):
        self.pin = pin
        self.last_state = False
        self.debounce_time = 0.2 # TIEMPO AUMENTADO
        self.last_change = 0
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def is_pressed(self) -> bool:
        current_time = time.time()
        current_state = GPIO.input(self.pin)

        if current_state != self.last_state:
            if current_time - self.last_change > self.debounce_time:
                self.last_state = current_state
                self.last_change = current_time
                return current_state
        return self.last_state

class BlinkingLED:
    """
    Controlador para Variable Color LED v1.1 usando Hilos (Threading)
    Soporta: OFF, SOLID, FAST, MEDIUM, SLOW
    """
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.stop_event = threading.Event()
        self.thread = None
        self.off()

    def _blink_loop(self, on_time, off_time):
        """Proceso en segundo plano para parpadear"""
        while not self.stop_event.is_set():
            GPIO.output(self.pin, GPIO.HIGH)
            if self.stop_event.wait(on_time): break
            GPIO.output(self.pin, GPIO.LOW)
            if self.stop_event.wait(off_time): break

    def set_pattern(self, pattern_type):
        # 1. Detener hilo anterior si existe
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        
        self.stop_event.clear()

        # 2. Configurar nuevo patrón
        if pattern_type == 'OFF':
            GPIO.output(self.pin, GPIO.LOW)
        
        elif pattern_type == 'SOLID':
            GPIO.output(self.pin, GPIO.HIGH)
            
        elif pattern_type == 'FAST': # Estudiando (Muy rápido)
            self.thread = threading.Thread(target=self._blink_loop, args=(0.1, 0.1))
            self.thread.start()

        elif pattern_type == 'MEDIUM': # Charla (Velocidad media)
            self.thread = threading.Thread(target=self._blink_loop, args=(0.5, 0.5))
            self.thread.start()
            
        elif pattern_type == 'SLOW': # Buscando compañero (Lento)
            self.thread = threading.Thread(target=self._blink_loop, args=(1.0, 1.0))
            self.thread.start()

    def off(self):
        self.set_pattern('OFF')

    def cleanup(self):
        self.off()

class Buzzer:
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
    def beep(self, duration: float = 0.1):
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(self.pin, GPIO.LOW)
    def beep_short(self): self.beep(0.1)
    def beep_confirm(self):
        self.beep(0.1); time.sleep(0.05); self.beep(0.1)
    def beep_error(self): self.beep(0.3)
    def beep_startup(self):
        self.beep(0.05); time.sleep(0.05); self.beep(0.05)
    def cleanup(self): GPIO.output(self.pin, GPIO.LOW)

class I2CDisplay:
    LCD_ADDRESS = 0x3E
    def __init__(self, bus: int = 1):
        if smbus2 is None: self.bus = None; return
        try:
            self.bus = smbus2.SMBus(bus)
            self._command(0x38); time.sleep(0.05)
            self._command(0x38); time.sleep(0.05)
            self._command(0x0C); self._command(0x01); time.sleep(0.05)
            self._command(0x06)
        except: self.bus = None
    def _command(self, cmd):
        if self.bus:
            try: self.bus.write_byte_data(self.LCD_ADDRESS, 0x80, cmd)
            except: pass
    def _write_char(self, char):
        if self.bus:
            try: self.bus.write_byte_data(self.LCD_ADDRESS, 0x40, ord(char))
            except: pass
    def clear(self):
        self._command(0x01); time.sleep(0.05)
    def show_message(self, line1: str, line2: str = ""):
        if not self.bus: return
        try:
            self.clear()
            for char in line1[:16]: self._write_char(char)
            if line2:
                self._command(0xC0)
                for char in line2[:16]: self._write_char(char)
        except: pass
