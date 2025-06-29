from pythonosc import dispatcher, osc_server
try:
    import RPi.GPIO as GPIO
except ImportError:
    class MockGPIO:
        BCM = OUT = HIGH = LOW = None
        def setmode(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, state): pass
        def cleanup(self): pass
    GPIO = MockGPIO()

import threading
import tkinter as tk

# Pin GPIO da usare
GPIO_MAP = {
    "CUORE": [17, 22],
    "MANO": 27,
    "MANI": [17, 27, 22]
}

# Stato dei GPIO per la GUI
gpio_states = {pin: False for pins in GPIO_MAP.values() for pin in (pins if isinstance(pins, list) else [pins])}

# Configurazione GPIO
GPIO.setmode(GPIO.BCM)
for pin in gpio_states.keys():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def update_leds():
    """Aggiorna lo stato dei LED sulla GUI."""
    for pin, led in led_widgets.items():
        led.config(bg="green" if gpio_states[pin] else "red")

def osc_handler(address, *args):
    """Gestisce i messaggi OSC e accende le GPIO corrispondenti."""
    print(f"Received OSC message: {address} {args}")

    if address.startswith("/on") or address.startswith("/off"):
        try:
            command, target = address[1:].split(" ", 1)  # Rimuove lo slash iniziale
            state = GPIO.HIGH if command.lower() == "on" else GPIO.LOW

            if target.upper() in GPIO_MAP:
                pins = GPIO_MAP[target.upper()]
                if not isinstance(pins, list):
                    pins = [pins]
                for pin in pins:
                    GPIO.output(pin, state)
                    gpio_states[pin] = state == GPIO.HIGH
                print(f"GPIO {pins} set to {'HIGH' if state else 'LOW'}")
            else:
                print("Invalid target")
        except (ValueError, IndexError) as e:
            print(f"Error parsing OSC message: {e}")
    elif address == "/mani":
        try:
            level = int(args[0])
            pins = GPIO_MAP["MANI"]

            # Spegne tutti prima di accendere il numero corretto
            for pin in pins:
                GPIO.output(pin, GPIO.LOW)
                gpio_states[pin] = False

            if level >= 1:
                GPIO.output(pins[0], GPIO.HIGH)
                gpio_states[pins[0]] = True
            if level >= 2:
                GPIO.output(pins[1], GPIO.HIGH)
                gpio_states[pins[1]] = True
            if level >= 3:
                GPIO.output(pins[2], GPIO.HIGH)
                gpio_states[pins[2]] = True

            print(f"Set MANI level {level}")
        except (ValueError, IndexError) as e:
            print(f"Error parsing OSC message: {e}")
    update_leds()

# Configurazione server OSC
ip = "0.0.0.0"  # Ascolta su tutte le interfacce di rete
port = 8000     # Porta OSC

disp = dispatcher.Dispatcher()
disp.map("/on *", osc_handler)
disp.map("/off *", osc_handler)
disp.map("/mani", osc_handler)
server = osc_server.ThreadingOSCUDPServer((ip, port), disp)

print(f"Listening for OSC messages on {ip}:{port}")

# Esegui il server in un thread separato per evitare blocchi
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

# Creazione GUI
root = tk.Tk()
root.title("GPIO OSC Monitor")

led_widgets = {}
for i, pin in enumerate(gpio_states.keys()):
    label = tk.Label(root, text=f"GPIO {pin}")
    label.grid(row=i, column=0)
    led = tk.Label(root, text=" ", width=5, height=2, bg="red")
    led.grid(row=i, column=1)
    led_widgets[pin] = led

def on_close():
    print("Shutting down...")
    GPIO.cleanup()
    server.shutdown()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
update_leds()
root.mainloop()
