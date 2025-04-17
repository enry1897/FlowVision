import tkinter as tk
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

led_pin = 17
fire_pin = 27
blinders_pin = 22


try:
    import gpiod
    from gpiod.line import Direction
    use_mock = False

    chip = gpiod.Chip("gpiochip0")
    lines = {}
    for pin in [led_pin, fire_pin, blinders_pin]:
        line = chip.get_line(pin)
        line.request(consumer="osc-server", type=Direction.OUTPUT, default_val=0)
        lines[pin] = line
        print(f"Line {pin} initial state: {line.get_value()}")

    print("USING gpiod")

except Exception as e:
    print(f"Falling back to MockGPIO due to error: {e}")
    use_mock = True

if use_mock:
    class MockGPIO:
        def __init__(self):
            self.states = {led_pin: 0, fire_pin: 0, blinders_pin: 0}

        def output(self, pin, state):
            print(f"MockGPIO: Setting GPIO {pin} to {'HIGH' if state else 'LOW'}")
            self.states[pin] = state

        def input(self, pin):
            return self.states.get(pin, 0)

        def cleanup(self):
            print("MockGPIO: cleanup")

    GPIO = MockGPIO()
else:
    class RealGPIO:
        def __init__(self, lines):
            self.lines = lines
            self.state = {pin: 0 for pin in lines}

        def output(self, pin, value):
            self.state[pin] = value
            self.lines[pin].set_value(value)

        def input(self, pin):
            return self.state.get(pin, 0)

        def cleanup(self):
            for pin, line in self.lines.items():
                line.set_value(0)
                line.release()

    GPIO = RealGPIO(lines)

# GUI Setup
root = tk.Tk()
root.title("OSC Server GUI")
root.geometry("350x300")

led_status = tk.Label(root, text="LED OFF", bg="red", font=("Arial", 16))
led_status.pack(pady=10)

gpio_status = tk.Label(root, text="GPIO led_pin: LOW, GPIO fire_pin: LOW, GPIO blinders_pin: LOW", font=("Arial", 12))
gpio_status.pack(pady=10)

fire_leds = []
for _ in range(3):
    led = tk.Label(root, text="OFF", bg="gray", font=("Arial", 12), width=10)
    led.pack()
    fire_leds.append(led)

blinder_led = tk.Label(root, text="BLINDER OFF", bg="gray", font=("Arial", 12), width=12)
blinder_led.pack(pady=10)

def update_gpio_status():
    status_text = f"GPIO led_pin: {'HIGH' if GPIO.input(led_pin) else 'LOW'}, " \
                  f"GPIO fire_pin: {'HIGH' if GPIO.input(fire_pin) else 'LOW'}, " \
                  f"GPIO blinders_pin: {'HIGH' if GPIO.input(blinders_pin) else 'LOW'}"
    gpio_status.config(text=status_text)

def toggle_led(address, value):
    print(f"Toggling LED: {'ON' if value == 1 else 'OFF'}")
    GPIO.output(led_pin, 1 if value == 1 else 0)
    led_status.config(text="LED ON" if value == 1 else "LED OFF", bg="green" if value == 1 else "red")
    update_gpio_status()
    print(f"Toggled LED: {'ON' if value == 1 else 'OFF'}")

def fire_machine(address, value):
    print(f"Toggling Firing machine: {'ON' if value > 0 else 'OFF'}")
    GPIO.output(fire_pin, 1 if value > 0 else 0)
    for i in range(3):
        fire_leds[i].config(text="ON", bg="orange") if i < value else fire_leds[i].config(text="OFF", bg="gray")
    update_gpio_status()
    print(f"Toggled Firing machine: {'ON' if value > 0 else 'OFF'}")

def toggle_blinders(address, value):
    print(f"Toggling Blinders: {'ON' if value == 1 else 'OFF'}")
    GPIO.output(blinders_pin, 1 if value == 1 else 0)
    blinder_led.config(text="BLINDER ON" if value == 1 else "BLINDER OFF", bg="yellow" if value == 1 else "gray")
    update_gpio_status()
    print(f"Toggled Blinders: {'ON' if value == 1 else 'OFF'}")

# OSC Setup
dispatcher = Dispatcher()
dispatcher.map("/lights", toggle_led)
dispatcher.map("/fireMachine", fire_machine)
dispatcher.map("/blinders", toggle_blinders)

SERVER_IP = "192.168.1.19"
SERVER_PORT = 8100
server = ThreadingOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher)

def start_osc_server():
    print(f"Listening on {SERVER_IP}:{SERVER_PORT}...")
    server.serve_forever()

server_thread = threading.Thread(target=start_osc_server, daemon=True)
server_thread.start()

# GUI Loop
try:
    tk.mainloop()
finally:
    GPIO.cleanup()
