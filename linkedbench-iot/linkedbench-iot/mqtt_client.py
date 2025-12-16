#!/usr/bin/env python3
"""
MQTT Client for LinkedBench system
Publishes events to cloud platform
"""

import json
import logging
from typing import Dict, Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

logger = logging.getLogger('LinkedBench.MQTT')


class MQTTPublisher:
    """MQTT publisher for LinkedBench events"""
    
    def __init__(self, bench_id: str, broker: str = "test.mosquitto.org", port: int = 1883):
        self.bench_id = bench_id
        self.broker = broker
        self.port = port
        self.client = None
        self.connected = False
        
        if mqtt is None:
            logger.warning("paho-mqtt not installed, MQTT disabled")
            return
        
        try:
            self.client = mqtt.Client(client_id=f"linkedbench_{bench_id}")
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker {broker}:{port}")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
            self.client = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def publish_event(self, event: Dict[str, Any]):
        """Publish an event to MQTT"""
        if self.client is None or not self.connected:
            logger.warning("MQTT not connected, event not published")
            return False
        
        try:
            topic = f"linkedbench/{self.bench_id}/events"
            payload = json.dumps(event)
            
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published event to {topic}: {event['event_type']}")
                return True
            else:
                logger.error(f"Failed to publish event: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing event: {e}", exc_info=True)
            return False
    
    def publish_status(self, status: Dict[str, Any]):
        """Publish status update"""
        if self.client is None or not self.connected:
            return False
        
        try:
            topic = f"linkedbench/{self.bench_id}/status"
            payload = json.dumps(status)
            
            result = self.client.publish(topic, payload, qos=0)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"Error publishing status: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client disconnected")


# Alternative: ThingSpeak HTTP API
class ThingSpeakPublisher:
    """Publisher for ThingSpeak platform"""
    
    def __init__(self, write_api_key: str, channel_id: str):
        self.write_api_key = write_api_key
        self.channel_id = channel_id
        self.base_url = "https://api.thingspeak.com/update"
        
        logger.info(f"ThingSpeak publisher initialized for channel {channel_id}")
    
    def publish_event(self, event: Dict[str, Any]):
        """Publish event to ThingSpeak"""
        try:
            import requests
            
            # Map event to ThingSpeak fields
            data = {
                'api_key': self.write_api_key,
                'field1': event.get('mode', 0),
                'field2': 1 if event.get('event_type') == 'occupation' else 0,
                'field3': event.get('bench_id', ''),
            }
            
            response = requests.get(self.base_url, params=data, timeout=5)
            
            if response.status_code == 200:
                logger.debug(f"Published to ThingSpeak: {event['event_type']}")
                return True
            else:
                logger.error(f"ThingSpeak publish failed: {response.status_code}")
                return False
                
        except ImportError:
            logger.error("requests library not available")
            return False
        except Exception as e:
            logger.error(f"Error publishing to ThingSpeak: {e}")
            return False
