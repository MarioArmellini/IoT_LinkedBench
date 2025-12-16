import time
from grove.chainable_rgb_led import ChainableLED

# Configuración: 
# El puerto D24 en el Hat usa el GPIO 24 y el GPIO 25.
# (24 es el pin amarillo, 25 es el pin blanco).
pin_clk = 24
pin_data = 25
num_leds = 1 # Tienes solo 1 módulo conectado

# Inicializamos el LED complejo
led = ChainableLED(pin_clk, pin_data, num_leds)

print("Probando colores...")

while True:
    # Rojo
    print("Rojo")
    led.setColorRGB(0, 255, 0, 0) 
    time.sleep(1)
    
    # Verde
    print("Verde")
    led.setColorRGB(0, 0, 255, 0)
    time.sleep(1)
    
    # Azul
    print("Azul")
    led.setColorRGB(0, 0, 0, 255)
    time.sleep(1)
