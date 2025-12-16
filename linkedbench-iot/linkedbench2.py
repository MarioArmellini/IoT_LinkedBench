#!/usr/bin/env python3
"""
LinkedBench IoT System - VERSION FINAL CORREGIDA
- Pines de botones corregidos via software (sensors.py).
- Bloqueo lógico: El botón de modo no funciona si el banco está vacío.
- Monitor de temperatura CPU incluido.
"""

import RPi.GPIO as GPIO
import time
import logging
from datetime import datetime
from threading import Thread, Lock
import queue
import signal
import sys

# Importamos las clases de hardware
from sensors2 import PressurePlate, ModeButton, BlinkingLED, Buzzer, I2CDisplay
# Importamos los módulos de comunicación y datos
from mqtt_client import MQTTPublisher
from rest_api import start_api_server
from database import EventDatabase

# --- DEFINICIÓN DE PINES ---
PIN_PRESSURE_1 = 18  # Asiento 1
PIN_PRESSURE_2 = 16  # Asiento 2
PIN_MODE_BUTTON = 22 # Botón de modos
PIN_BUZZER = 5       # Altavoz
PIN_RGB_LED = 24     # LED Variable (Pin 24)

# --- DEFINICIÓN DE MODOS ---
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

# --- PATRONES DE LUZ ---
MODE_PATTERNS = {
    MODE_STUDYING: 'FAST',
    MODE_CHAT: 'MEDIUM'
}


# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('LinkedBench')

def get_cpu_temperature():
    """Lee la temperatura del CPU de la Raspberry Pi"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
        return temp
    except Exception as e:
        logger.error(f"Error reading CPU temp: {e}")
        return 0.0

class LinkedBenchSystem:
    def __init__(self, bench_id="BENCH_001"):
        self.bench_id = bench_id
        self.current_mode = MODE_EMPTY
        self.occupied = False
        
        # Estado individual de asientos
        self.seat1_active = False
        self.seat2_active = False
        
        self.lock = Lock()
        self.running = False
        self.event_queue = queue.Queue()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Hardware
        # Nota: La lógica de pines invertidos (blanco/amarillo) se maneja dentro de sensors.py
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
        """Inicia todos los hilos y procesos"""
        self.running = True
        
        # Manejadores para cerrar con Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 1. Hilo de Sensores (Lee botones)
        self.sensor_thread = Thread(target=self._sensor_loop, daemon=True)
        # 2. Hilo de Eventos (Guarda en DB y MQTT)
        self.event_thread = Thread(target=self._event_processor, daemon=True)
        # 3. Hilo de API (Servidor Web)
        self.api_thread = Thread(target=lambda: start_api_server(self), daemon=True)
        # 4. Hilo de Monitorización (Temperatura CPU cada min)
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)

        self.sensor_thread.start()
        self.event_thread.start()
        self.api_thread.start()
        self.monitor_thread.start()

        # Estado inicial
        self._update_display()
        self._update_led()
        self.buzzer.beep_startup()
        logger.info("SISTEMA LISTO: Esperando usuarios...")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Apagado limpio del sistema"""
        self.running = False
        logger.info("Apagando sistema...")
        if self.display: self.display.clear()
        self.led.cleanup()
        self.mqtt.disconnect()
        self.db.close()
        GPIO.cleanup()

    def _signal_handler(self, signum, frame):
        self.running = False

    def _monitor_loop(self):
        """Monitor de salud del sistema (Temperatura CPU)"""
        logger.info("Monitor de CPU iniciado.")
        while self.running:
            try:
                # Esperar 60 segundos
                for _ in range(60):
                    if not self.running: return
                    time.sleep(1)
                
                # Leer y enviar temperatura
                cpu_temp = get_cpu_temperature()
                status_payload = {
                    'bench_id': self.bench_id,
                    'type': 'system_health',
                    'cpu_temp': cpu_temp,
                    'occupied': self.occupied,
                    'timestamp': datetime.now().isoformat()
                }
                # Usamos publish_status (no guarda evento en DB, solo MQTT)
                self.mqtt.publish_status(status_payload)
                logger.debug(f"Salud del sistema: CPU {cpu_temp}°C")
                
            except Exception as e:
                logger.error(f"Error en monitor: {e}")

    def _sensor_loop(self):
        """Bucle principal de lectura de sensores"""
        last_occupied = False
        last_button_state = False

        while self.running:
            try:
                # 1. Leer Sensores de Presión
                p1 = self.pressure1.is_pressed()
                p2 = self.pressure2.is_pressed()
                
                # 2. Gestionar cambios de ocupación
                if (p1 != self.seat1_active) or (p2 != self.seat2_active):
                    with self.lock:
                        self.seat1_active = p1
                        self.seat2_active = p2

                        count = int(p1) + int(p2)

                        if count == 0:
                            self.occupied = False
                            self.current_mode = MODE_EMPTY
                            self._update_display()
                            self._update_led()

                        elif count == 1:
                            self.occupied = True
                            if self.current_mode in (MODE_EMPTY, MODE_STUDY_BUDDY):
                                self.current_mode = MODE_AVAILABLE
                            self._update_display()
                            self._update_led()

                        elif count == 2:
                            self.occupied = True
                            self.current_mode = MODE_STUDY_BUDDY
                            self._update_display()
                            self._update_led()


                # 3. Leer Botón de Modo
                if self.mode_button.is_pressed():
                    if not last_button_state: # Solo actuar al pulsar (flanco de subida)
                        last_button_state = True
                        with self.lock:
                            self._cycle_mode()
                else:
                    last_button_state = False

                time.sleep(0.1) # Pequeña pausa para no saturar la CPU

            except Exception as e:
                logger.error(f"Error Loop Sensores: {e}")
                time.sleep(1)

    def _cycle_mode(self):

        count = int(self.seat1_active) + int(self.seat2_active)

        # 0 o 2 personas → NO se puede cambiar
        if count != 1:
            logger.warning("Cambio de modo bloqueado por ocupación")
            self.buzzer.beep_error()
            return

        # SOLO con 1 persona
        if self.current_mode == MODE_AVAILABLE:
            self.current_mode = MODE_STUDYING
        elif self.current_mode == MODE_STUDYING:
            self.current_mode = MODE_CHAT
        elif self.current_mode == MODE_CHAT:
            self.current_mode = MODE_AVAILABLE

        logger.info(f"Modo cambiado a: {MODE_NAMES[self.current_mode]}")
        self.buzzer.beep_confirm()
        self._update_display()
        self._update_led()


    def _handle_occupation(self):
        """Se ejecuta cuando alguien se sienta"""
        logger.info("Alguien se ha sentado.")
        
        # if self.current_mode == MODE_EMPTY: self.current_mode = MODE_STUDYING
        
        event = {
            'event_type': 'occupation',
            'bench_id': self.bench_id,
            'mode': self.current_mode,
            'mode_name': MODE_NAMES[self.current_mode],
            'timestamp': datetime.now().isoformat()
        }
        self.event_queue.put(event)
        
        self.buzzer.beep_short()
        self._update_display()
        self._update_led()

    def _handle_vacation(self):
        """Se ejecuta cuando el banco queda vacío"""
        logger.info("Banco liberado.")
        self.current_mode = MODE_EMPTY
        
        event = {
            'event_type': 'vacation',
            'bench_id': self.bench_id,
            'timestamp': datetime.now().isoformat()
        }
        self.event_queue.put(event)
        
        self._update_display()
        self._update_led()

    def _update_led(self):
        try:
            # LEDs fijos
            if self.current_mode == MODE_EMPTY:
                self.led.set_pattern('OFF')
                return

            if self.current_mode in (MODE_AVAILABLE, MODE_STUDY_BUDDY):
                self.led.set_pattern('SOLID')
                return

            # Modos parpadeantes
            pattern = MODE_PATTERNS.get(self.current_mode)
            if pattern:
                self.led.set_pattern(pattern)

        except Exception as e:
            logger.error(f"Error LED: {e}")

    def _update_display(self):
        if not self.display:
            return

        if self.current_mode == MODE_EMPTY:
            self.display.show_message("LinkedBench", "Empty")

        elif self.current_mode == MODE_AVAILABLE:
            self.display.show_message("LinkedBench", "Available")

        else:
            self.display.show_message("LinkedBench", MODE_NAMES[self.current_mode])


    def _event_processor(self):
        """Procesa la cola de eventos para guardarlos y enviarlos"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self.db.save_event(event)
                self.mqtt.publish_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")

    # API Helpers
    def get_status(self):
        with self.lock:
            return {
                'bench_id': self.bench_id, 
                'occupied': self.occupied, 
                'mode': self.current_mode, 
                'mode_name': MODE_NAMES[self.current_mode],
                'timestamp': datetime.now().isoformat()
            }

    def set_mode(self, mode):
        if mode not in MODE_NAMES: return {'error': 'Invalid mode'}
        with self.lock:
            if not self.occupied:
                return {'error': 'Cannot set mode while empty'}
                
            self.current_mode = mode
            self._update_display()
            self._update_led()
            
            # Crear evento de cambio remoto
            event = {
                'event_type': 'mode_change_remote',
                'bench_id': self.bench_id,
                'mode': self.current_mode,
                'mode_name': MODE_NAMES[self.current_mode],
                'timestamp': datetime.now().isoformat()
            }
            self.event_queue.put(event)
            
            return self.get_status()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bench-id', default='BENCH_001')
    args = parser.parse_args()
    
    system = LinkedBenchSystem(bench_id=args.bench_id)
    system.start()

if __name__ == '__main__':
    main()
