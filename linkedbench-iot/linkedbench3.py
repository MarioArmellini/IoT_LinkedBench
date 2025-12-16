#!/usr/bin/env python3
"""
LinkedBench IoT System - VERSION FINAL CORREGIDA + EVENTOS
- Registra eventos de ocupación, liberación y cambios de modo
- Historial de eventos ahora se actualiza correctamente
"""

import RPi.GPIO as GPIO
import time
import logging
from datetime import datetime
from threading import Thread, Lock
import queue
import signal

from sensors2 import PressurePlate, ModeButton, BlinkingLED, Buzzer, I2CDisplay
from mqtt_client import MQTTPublisher
from rest_api import start_api_server
from database import EventDatabase

# --- PINES ---
PIN_PRESSURE_1 = 18
PIN_PRESSURE_2 = 16
PIN_MODE_BUTTON = 22
PIN_BUZZER = 5
PIN_RGB_LED = 24

# --- MODOS ---
MODE_EMPTY = 0
MODE_AVAILABLE = 1
MODE_STUDYING = 2
MODE_CHAT = 3
MODE_STUDY_BUDDY = 4

MODE_NAMES = {
    MODE_EMPTY: "Empty",
    MODE_AVAILABLE: "Available",
    MODE_STUDYING: "Studying",
    MODE_CHAT: "Open to chat",
    MODE_STUDY_BUDDY: "Study buddy"
}

MODE_PATTERNS = {
    MODE_STUDYING: 'FAST',
    MODE_CHAT: 'MEDIUM'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('LinkedBench')


class LinkedBenchSystem:
    def __init__(self, bench_id="BENCH_001"):
        self.bench_id = bench_id
        self.current_mode = MODE_EMPTY
        self.occupied = False
        self.seat1_active = False
        self.seat2_active = False
        self.lock = Lock()
        self.running = False
        self.event_queue = queue.Queue()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.pressure1 = PressurePlate(PIN_PRESSURE_1, "Seat1")
        self.pressure2 = PressurePlate(PIN_PRESSURE_2, "Seat2")
        self.mode_button = ModeButton(PIN_MODE_BUTTON)
        self.led = BlinkingLED(PIN_RGB_LED)
        self.buzzer = Buzzer(PIN_BUZZER)

        try:
            self.display = I2CDisplay()
        except:
            self.display = None

        self.db = EventDatabase()
        self.mqtt = MQTTPublisher(bench_id)

    def start(self):
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        Thread(target=self._sensor_loop, daemon=True).start()
        Thread(target=self._event_processor, daemon=True).start()
        Thread(target=lambda: start_api_server(self), daemon=True).start()

        self._update_display()
        self._update_led()
        self.buzzer.beep_startup()
        logger.info("SISTEMA LISTO")

        while self.running:
            time.sleep(1)

        self.stop()

    def stop(self):
        self.running = False
        if self.display:
            self.display.clear()
        self.led.cleanup()
        self.mqtt.disconnect()
        self.db.close()
        GPIO.cleanup()

    def _signal_handler(self, *_):
        self.running = False

    # ================= EVENTOS =================

    def _handle_occupation(self, seats):
        event = {
            'event_type': 'occupation',
            'bench_id': self.bench_id,
            'seats': seats,
            'mode': self.current_mode,
            'mode_name': MODE_NAMES[self.current_mode],
            'timestamp': datetime.now().isoformat()
        }
        self.event_queue.put(event)
        logger.info("Evento: ocupación")

    def _handle_vacation(self):
        event = {
            'event_type': 'vacation',
            'bench_id': self.bench_id,
            'timestamp': datetime.now().isoformat()
        }
        self.event_queue.put(event)
        logger.info("Evento: liberación")

    def _handle_mode_change(self):
        event = {
            'event_type': 'mode_change',
            'bench_id': self.bench_id,
            'mode': self.current_mode,
            'mode_name': MODE_NAMES[self.current_mode],
            'timestamp': datetime.now().isoformat()
        }
        self.event_queue.put(event)

    # ================= SENSORES =================

    def _sensor_loop(self):
        last_occupied = False
        last_button = False

        while self.running:
            p1 = self.pressure1.is_pressed()
            p2 = self.pressure2.is_pressed()
            seats = int(p1) + int(p2)

            if p1 != self.seat1_active or p2 != self.seat2_active:
                self.seat1_active = p1
                self.seat2_active = p2

                if seats == 0:
                    self.occupied = False
                    self.current_mode = MODE_EMPTY
                    if last_occupied:
                        self._handle_vacation()

                else:
                    self.occupied = True
                    if not last_occupied:
                        self.current_mode = MODE_AVAILABLE if seats == 1 else MODE_STUDY_BUDDY
                        self._handle_occupation(seats)
                    elif seats == 2:
                        self.current_mode = MODE_STUDY_BUDDY

                self._update_display()
                self._update_led()

            last_occupied = self.occupied

            # Botón de modo
            pressed = self.mode_button.is_pressed()
            if pressed and not last_button:
                self._cycle_mode()
            last_button = pressed

            time.sleep(0.1)

    def _cycle_mode(self):
        if int(self.seat1_active) + int(self.seat2_active) != 1:
            self.buzzer.beep_error()
            return

        if self.current_mode == MODE_AVAILABLE:
            self.current_mode = MODE_STUDYING
        elif self.current_mode == MODE_STUDYING:
            self.current_mode = MODE_CHAT
        elif self.current_mode == MODE_CHAT:
            self.current_mode = MODE_AVAILABLE

        self._handle_mode_change()
        self._update_display()
        self._update_led()
        self.buzzer.beep_confirm()

    # ================= SALIDA =================

    def _update_led(self):
        if self.current_mode == MODE_EMPTY:
            self.led.set_pattern('OFF')
        elif self.current_mode in (MODE_AVAILABLE, MODE_STUDY_BUDDY):
            self.led.set_pattern('SOLID')
        else:
            self.led.set_pattern(MODE_PATTERNS[self.current_mode])

    def _update_display(self):
        if not self.display:
            return
        self.display.show_message("LinkedBench", MODE_NAMES[self.current_mode])

    def _event_processor(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self.db.save_event(event)
                self.mqtt.publish_event(event)
            except queue.Empty:
                pass

    # ================= API =================

    def get_status(self):
        return {
            'bench_id': self.bench_id,
            'occupied': self.occupied,
            'mode': self.current_mode,
            'mode_name': MODE_NAMES[self.current_mode],
            'timestamp': datetime.now().isoformat()
        }


def main():
    LinkedBenchSystem().start()


if __name__ == '__main__':
    main()
