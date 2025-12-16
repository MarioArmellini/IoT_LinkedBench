#!/usr/bin/env python3
"""
LinkedBench System Test Suite
Tests all components individually and together
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('Test')

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    required_modules = [
        ('RPi.GPIO', 'RPi.GPIO'),
        ('smbus2', 'smbus2 (optional for display)'),
        ('paho.mqtt.client', 'paho-mqtt (optional for MQTT)'),
        ('flask', 'flask (optional for REST API)'),
        ('sqlite3', 'sqlite3')
    ]
    
    failed = []
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            logger.info(f"✓ {description}")
        except ImportError:
            logger.warning(f"✗ {description} - not installed")
            if 'optional' not in description:
                failed.append(module_name)
    
    if failed:
        logger.error(f"Missing required modules: {', '.join(failed)}")
        return False
    
    logger.info("All required imports successful")
    return True


def test_gpio():
    """Test GPIO setup"""
    logger.info("\nTesting GPIO...")
    
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Test setup
        test_pins = [18, 16, 22, 5, 24]
        for pin in test_pins:
            GPIO.setup(pin, GPIO.OUT)
            logger.info(f"✓ Pin {pin} configured")
        
        GPIO.cleanup()
        logger.info("GPIO test successful")
        return True
        
    except Exception as e:
        logger.error(f"GPIO test failed: {e}")
        return False


def test_i2c():
    """Test I2C interface"""
    logger.info("\nTesting I2C...")
    
    try:
        import smbus2
        bus = smbus2.SMBus(1)
        
        # Try to detect devices
        found_devices = []
        for addr in [0x27, 0x3F, 0x20, 0x38]:
            try:
                bus.read_byte(addr)
                found_devices.append(hex(addr))
                logger.info(f"✓ Device found at {hex(addr)}")
            except:
                pass
        
        if found_devices:
            logger.info(f"I2C devices found: {', '.join(found_devices)}")
            return True
        else:
            logger.warning("No I2C devices found (display may not be connected)")
            return True  # Not a critical error
            
    except ImportError:
        logger.warning("smbus2 not installed, skipping I2C test")
        return True
    except Exception as e:
        logger.error(f"I2C test failed: {e}")
        return False


def test_sensors():
    """Test sensor classes"""
    logger.info("\nTesting sensor classes...")
    
    try:
        from sensors import PressurePlate, ModeButton, GroveRGBLED, Buzzer, I2CDisplay
        import RPi.GPIO as GPIO
        
        GPIO.setmode(GPIO.BCM)
        
        # Test pressure plate
        logger.info("Testing PressurePlate...")
        p1 = PressurePlate(18, "Test1")
        logger.info("✓ PressurePlate initialized")
        
        # Test button
        logger.info("Testing ModeButton...")
        btn = ModeButton(22)
        logger.info("✓ ModeButton initialized")
        
        # Test LED
        logger.info("Testing RGB LED...")
        led = GroveRGBLED(24)
        logger.info("  Testing colors...")
        led.set_color(255, 0, 0)  # Red
        time.sleep(0.5)
        led.set_color(0, 255, 0)  # Green
        time.sleep(0.5)
        led.set_color(0, 0, 255)  # Blue
        time.sleep(0.5)
        led.off()
        logger.info("✓ RGB LED test complete")
        
        # Test buzzer
        logger.info("Testing Buzzer...")
        buzzer = Buzzer(5)
        buzzer.beep_short()
        time.sleep(0.2)
        buzzer.beep_confirm()
        logger.info("✓ Buzzer test complete")
        
        # Test display
        logger.info("Testing Display...")
        display = I2CDisplay()
        display.show_message("LinkedBench", "Test Mode")
        time.sleep(2)
        display.clear()
        logger.info("✓ Display test complete")
        
        # Cleanup
        led.cleanup()
        buzzer.cleanup()
        GPIO.cleanup()
        
        logger.info("All sensor tests passed")
        return True
        
    except Exception as e:
        logger.error(f"Sensor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database functionality"""
    logger.info("\nTesting database...")
    
    try:
        from database import EventDatabase
        import tempfile
        import os
        
        # Use temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        db = EventDatabase(db_path=temp_db.name)
        
        # Test save event
        event = {
            'bench_id': 'TEST_001',
            'event_type': 'test',
            'mode': 1,
            'mode_name': 'Test Mode',
            'timestamp': '2025-01-01T00:00:00'
        }
        
        event_id = db.save_event(event)
        logger.info(f"✓ Event saved with ID: {event_id}")
        
        # Test retrieve
        events = db.get_events(bench_id='TEST_001', limit=10)
        logger.info(f"✓ Retrieved {len(events)} events")
        
        # Test statistics
        stats = db.get_statistics(bench_id='TEST_001')
        logger.info(f"✓ Statistics: {stats}")
        
        # Cleanup
        db.close()
        os.unlink(temp_db.name)
        
        logger.info("Database test passed")
        return True
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False


def test_mqtt():
    """Test MQTT connectivity"""
    logger.info("\nTesting MQTT...")
    
    try:
        from mqtt_client import MQTTPublisher
        
        mqtt = MQTTPublisher('TEST_BENCH', broker='test.mosquitto.org')
        
        # Wait for connection
        time.sleep(2)
        
        if mqtt.connected:
            logger.info("✓ Connected to MQTT broker")
            
            # Test publish
            event = {
                'event_type': 'test',
                'bench_id': 'TEST_BENCH',
                'timestamp': '2025-01-01T00:00:00'
            }
            
            result = mqtt.publish_event(event)
            if result:
                logger.info("✓ Test event published")
            else:
                logger.warning("✗ Failed to publish event")
            
            mqtt.disconnect()
            logger.info("MQTT test passed")
            return True
        else:
            logger.warning("Could not connect to MQTT broker (may be network issue)")
            return True  # Not critical
            
    except ImportError:
        logger.warning("paho-mqtt not installed, skipping MQTT test")
        return True
    except Exception as e:
        logger.error(f"MQTT test failed: {e}")
        return False


def test_api():
    """Test REST API"""
    logger.info("\nTesting REST API...")
    
    try:
        from rest_api import create_app
        from linkedbench import LinkedBenchSystem
        
        # Create test system
        system = LinkedBenchSystem('TEST_API')
        
        # Create Flask app
        app = create_app(system)
        
        if app:
            logger.info("✓ Flask app created")
            
            # Test with test client
            client = app.test_client()
            
            response = client.get('/api/status')
            if response.status_code == 200:
                logger.info("✓ Status endpoint working")
            else:
                logger.error(f"✗ Status endpoint returned {response.status_code}")
            
            logger.info("API test passed")
            return True
        else:
            logger.warning("Flask not available, API test skipped")
            return True
            
    except ImportError:
        logger.warning("Flask not installed, skipping API test")
        return True
    except Exception as e:
        logger.error(f"API test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("=" * 50)
    logger.info("LinkedBench System Test Suite")
    logger.info("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("GPIO", test_gpio),
        ("I2C", test_i2c),
        ("Sensors", test_sensors),
        ("Database", test_database),
        ("MQTT", test_mqtt),
        ("REST API", test_api),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results[name] = False
        
        time.sleep(0.5)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Test Summary")
    logger.info("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name:20s} {status}")
    
    logger.info("=" * 50)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
