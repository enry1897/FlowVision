import tkinter as tk
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)
    GPIO.setup(22, GPIO.OUT)
except ImportError:
    class MockGPIO:
        BCM = OUT = HIGH = LOW = None
        def setmode(self, mode): pass
        def setup(self, pin, mode): pass
        def output(self, pin, state): pass
        def cleanup(self): pass
    GPIO = MockGPIO()

# Server Configuration
SERVER_IP = "192.168.1.19"
SERVER_PORT = 8000

# GUI Configuration
root = tk.Tk()
root.title("OSC Server GUI")
root.geometry("300x250")

# LED status labels
led_status = tk.Label(root, text="LED OFF", bg="red", font=("Arial", 16))
led_status.pack(pady=10)

fire_leds = []
for _ in range(3):
    led = tk.Label(root, text="OFF", bg="gray", font=("Arial", 12), width=10)
    led.pack()
    fire_leds.append(led)

blinder_led = tk.Label(root, text="BLINDER OFF", bg="gray", font=("Arial", 12), width=12)
blinder_led.pack(pady=10)

def toggle_led(address, value):
    """Toggle the main LED and GPIO 17."""
    GPIO.output(17, GPIO.HIGH if value == 1 else GPIO.LOW)
    led_status.config(text="LED ON" if value == 1 else "LED OFF", bg="green" if value == 1 else "red")

def fire_machine(address, value):
    """Control fire machine LEDs and GPIO 27."""
    GPIO.output(27, GPIO.HIGH if value > 0 else GPIO.LOW)
    for i in range(3):
        fire_leds[i].config(text="ON", bg="orange") if i < value else fire_leds[i].config(text="OFF", bg="gray")

def toggle_blinders(address, value):
    """Control the blinder LED and GPIO 22."""
    GPIO.output(22, GPIO.HIGH if value == 1 else GPIO.LOW)
    blinder_led.config(text="BLINDER ON" if value == 1 else "BLINDER OFF", bg="yellow" if value == 1 else "gray")

dispatcher = Dispatcher()
dispatcher.map("/lights", toggle_led)
dispatcher.map("/fireMachine", fire_machine)
dispatcher.map("/blinders", toggle_blinders)

server = ThreadingOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher)

def start_osc_server():
    print(f"Listening on {SERVER_IP}:{SERVER_PORT}...")
    server.serve_forever()

server_thread = threading.Thread(target=start_osc_server, daemon=True)
server_thread.start()

# Run the GUI
tk.mainloop()

# Cleanup GPIO on exit
GPIO.cleanup()
