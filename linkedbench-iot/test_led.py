import RPi.GPIO as GPIO
import time

# CONFIGURACIÓN
PIN_LED = 24       # Puerto D24
CLK_PIN = 24       # Cable Amarillo
DATA_PIN = 25      # Cable Blanco

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def send_byte(clk, data, b):
    for i in range(8):
        if (b & 0x80) != 0: GPIO.output(data, GPIO.HIGH)
        else: GPIO.output(data, GPIO.LOW)
        GPIO.output(clk, GPIO.LOW)
        time.sleep(0.00002)
        GPIO.output(clk, GPIO.HIGH)
        time.sleep(0.00002)
        b <<= 1

def send_color(clk, data, r, g, b):
    # Enviar prefijo (32 ceros)
    for _ in range(4): send_byte(clk, data, 0x00)
    
    # Calcular flag anti-errores
    flag = 0b11000000
    if (b & 0x80) == 0: flag |= 0b00100000
    if (g & 0x80) == 0: flag |= 0b00010000
    if (r & 0x80) == 0: flag |= 0b00001000
    
    send_byte(clk, data, flag)
    send_byte(clk, data, b)
    send_byte(clk, data, g)
    send_byte(clk, data, r)
    
    # Enviar sufijo (32 ceros)
    for _ in range(4): send_byte(clk, data, 0x00)

print("--- DIAGNÓSTICO DE LED RGB ---")
print("Asegúrate de que el cable está en el conector 'IN' del módulo LED.")

# PRUEBA 1: Orden Estándar (Amarillo=CLK, Blanco=DATA)
print("\n[INTENTO 1] Configuración Estándar: Amarillo=Reloj, Blanco=Datos")
GPIO.setup(CLK_PIN, GPIO.OUT)
GPIO.setup(DATA_PIN, GPIO.OUT)
send_color(CLK_PIN, DATA_PIN, 255, 0, 0) # ROJO
print("-> He enviado color ROJO. ¿Se ha encendido?")
time.sleep(2)
send_color(CLK_PIN, DATA_PIN, 0, 0, 0)   # APAGAR

# PRUEBA 2: Orden Invertido (Amarillo=DATA, Blanco=CLK)
print("\n[INTENTO 2] Configuración Invertida: Amarillo=Datos, Blanco=Reloj")
# Invertimos pines
CLK_INV = 25
DATA_INV = 24
GPIO.setup(CLK_INV, GPIO.OUT)
GPIO.setup(DATA_INV, GPIO.OUT)
send_color(CLK_INV, DATA_INV, 0, 255, 0) # VERDE
print("-> He enviado color VERDE. ¿Se ha encendido?")
time.sleep(2)
send_color(CLK_INV, DATA_INV, 0, 0, 0)   # APAGAR

GPIO.cleanup()
print("\nFin de la prueba.")

