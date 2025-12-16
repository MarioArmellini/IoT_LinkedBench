#!/usr/bin/env python3
"""
LinkedBench IoT System - Main Application
Smart bench system for campus social connection
"""

import RPi.GPIO as GPIO
import time
import json
import logging
from datetime import datetime
from threading import Thread, Lock
import queue
import signal
import sys

# Import custom modules
from sensors import PressurePlate, ModeButton, GroveRGBLED, Buzzer, I2CDisplay
from mqtt_client import MQTTPublisher
from rest_api import start_api_server
from database import EventDatabase

# Pin definitions (BCM mode)
PIN_PRESSURE_1 = 18  # Pressure plate 1 with integrated LED
PIN_PRESSURE_2 = 16  # Pressure plate 2 with integrated LED
PIN_MODE_BUTTON = 22  # Mode selection button
PIN_BUZZER = 5       # Buzzer output
PIN_RGB_LED = 24     # RGB LED (RCGB Grove)

# Mode definitions
MODE_EMPTY = 0       # Libre/Vacío
MODE_STUDYING = 1    # Estudiando (no molestar) - RED
MODE_CHAT = 2        # Abierto a conversar - GREEN
MODE_STUDY_BUDDY = 3 # Buscando compañero - BLUE

MODE_NAMES = {
    MODE_EMPTY: "Empty",
    MODE_STUDYING: "Studying",
    MODE_CHAT: "Open to chat",
    MODE_STUDY_BUDDY: "Study buddy"
}

MODE_COLORS = {
    MODE_EMPTY: (0, 0, 255),      # Blue (dim)
    MODE_STUDYING: (255, 0, 0),   # Red
    MODE_CHAT: (0, 255, 0),       # Green
    MODE_STUDY_BUDDY: (0, 128, 255)  # Light blue
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/linkedbench.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('LinkedBench')


class LinkedBenchSystem:
    """Main LinkedBench system controller"""
    
    def __init__(self, bench_id="BENCH_001"):
        self.bench_id = bench_id
        self.current_mode = MODE_EMPTY
        self.occupied = False
        self.lock = Lock()
        self.running = False
        self.event_queue = queue.Queue()
        
        # Initialize hardware components
        logger.info("Initializing LinkedBench hardware...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.pressure1 = PressurePlate(PIN_PRESSURE_1, "Seat1")
        self.pressure2 = PressurePlate(PIN_PRESSURE_2, "Seat2")
        self.mode_button = ModeButton(PIN_MODE_BUTTON)
        self.rgb_led = GroveRGBLED(PIN_RGB_LED)
        self.buzzer = Buzzer(PIN_BUZZER)
        self.display = I2CDisplay()
        
        # Initialize software components
        self.db = EventDatabase()
        self.mqtt = MQTTPublisher(bench_id)
        
        # API server will share state with this instance
        self.api_thread = None
        
        logger.info(f"LinkedBench {bench_id} initialized successfully")
    
    def start(self):
        """Start the LinkedBench system"""
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start threads
        self.sensor_thread = Thread(target=self._sensor_loop, daemon=True)
        self.event_thread = Thread(target=self._event_processor, daemon=True)
        self.api_thread = Thread(target=lambda: start_api_server(self), daemon=True)
        
        self.sensor_thread.start()
        self.event_thread.start()
        self.api_thread.start()
        
        # Initial state
        self._update_display()
        self._update_led()
        self.buzzer.beep_startup()
        
        logger.info("LinkedBench system started")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the LinkedBench system"""
        logger.info("Stopping LinkedBench system...")
        self.running = False
        
        # Cleanup
        self.display.clear()
        self.rgb_led.off()
        self.mqtt.disconnect()
        self.db.close()
        GPIO.cleanup()
        
        logger.info("LinkedBench system stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False
    
    def _sensor_loop(self):
        """Main sensor reading loop"""
        last_occupied = False
        last_button_state = False
        
        while self.running:
            try:
                # Check pressure plates
                seat1_pressed = self.pressure1.is_pressed()
                seat2_pressed = self.pressure2.is_pressed()
                currently_occupied = seat1_pressed or seat2_pressed
                
                # Detect occupation changes
                if currently_occupied != last_occupied:
                    with self.lock:
                        self.occupied = currently_occupied
                        
                        if currently_occupied:
                            logger.info("Bench occupied")
                            self._handle_occupation()
                        else:
                            logger.info("Bench vacated")
                            self._handle_vacation()
                    
                    last_occupied = currently_occupied
                
                # Check mode button
                if self.mode_button.is_pressed():
                    if not last_button_state:  # Button press detected (edge)
                        last_button_state = True
                        with self.lock:
                            self._cycle_mode()
                else:
                    last_button_state = False
                
                time.sleep(0.1)  # 100ms polling interval
                
            except Exception as e:
                logger.error(f"Error in sensor loop: {e}", exc_info=True)
                time.sleep(1)
    
    def _handle_occupation(self):
        """Handle bench occupation event"""
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
    
    def _handle_vacation(self):
        """Handle bench vacation event"""
        # Reset to empty mode when bench is vacated
        self.current_mode = MODE_EMPTY
        
        event = {
            'event_type': 'vacation',
            'bench_id': self.bench_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_queue.put(event)
        self._update_display()
        self._update_led()
    
    def _cycle_mode(self):
        """Cycle through available modes"""
        if not self.occupied:
            logger.info("Cannot change mode when bench is empty")
            self.buzzer.beep_error()
            return
        
        # Cycle: STUDYING -> CHAT -> STUDY_BUDDY -> STUDYING
        if self.current_mode == MODE_EMPTY:
            self.current_mode = MODE_STUDYING
        elif self.current_mode == MODE_STUDYING:
            self.current_mode = MODE_CHAT
        elif self.current_mode == MODE_CHAT:
            self.current_mode = MODE_STUDY_BUDDY
        else:
            self.current_mode = MODE_STUDYING
        
        logger.info(f"Mode changed to: {MODE_NAMES[self.current_mode]}")
        
        event = {
            'event_type': 'mode_change',
            'bench_id': self.bench_id,
            'mode': self.current_mode,
            'mode_name': MODE_NAMES[self.current_mode],
            'timestamp': datetime.now().isoformat()
        }
        
        self.event_queue.put(event)
        self.buzzer.beep_confirm()
        self._update_display()
        self._update_led()
    
    def _update_display(self):
        """Update LCD display with current status"""
        if not self.occupied:
            self.display.show_message("LinkedBench", "Available")
        else:
            mode_name = MODE_NAMES[self.current_mode]
            self.display.show_message("LinkedBench", mode_name)
    
    def _update_led(self):
        """Update RGB LED based on current mode"""
        color = MODE_COLORS[self.current_mode]
        self.rgb_led.set_color(*color)
    
    def _event_processor(self):
        """Process events from queue - save to DB and publish via MQTT"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                
                # Save to database
                self.db.save_event(event)
                
                # Publish via MQTT
                self.mqtt.publish_event(event)
                
                logger.info(f"Event processed: {event['event_type']}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
    
    def get_status(self):
        """Get current system status (for REST API)"""
        with self.lock:
            return {
                'bench_id': self.bench_id,
                'occupied': self.occupied,
                'mode': self.current_mode,
                'mode_name': MODE_NAMES[self.current_mode],
                'timestamp': datetime.now().isoformat()
            }
    
    def set_mode(self, mode):
        """Set mode remotely (for REST API)"""
        if mode not in MODE_NAMES:
            raise ValueError(f"Invalid mode: {mode}")
        
        if not self.occupied and mode != MODE_EMPTY:
            raise ValueError("Cannot set mode when bench is empty")
        
        with self.lock:
            self.current_mode = mode
            self._update_display()
            self._update_led()
            self.buzzer.beep_confirm()
            
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
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedBench IoT System')
    parser.add_argument('--bench-id', default='BENCH_001', help='Bench identifier')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start system
    system = LinkedBenchSystem(bench_id=args.bench_id)
    system.start()


if __name__ == '__main__':
    main()
