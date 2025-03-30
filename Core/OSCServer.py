import tkinter as tk
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

# Configurazione IP e porta del server
SERVER_IP = "192.168.255.102"
SERVER_PORT = 8000
CLIENT_IP = "192.168.255.108"

# Creazione della finestra GUI
root = tk.Tk()
root.title("OSC Server GUI")
root.geometry("300x200")

# LED di stato (ON/OFF)
led_status = tk.Label(root, text="LED OFF", bg="red", font=("Arial", 16))
led_status.pack(pady=20)

# LED per Fire Machine
fire_leds = []
for _ in range(3):
    led = tk.Label(root, text="OFF", bg="gray", font=("Arial", 12), width=10)
    led.pack()
    fire_leds.append(led)

def toggle_led(address, value):
    """Accende o spegne il LED principale in base al valore ricevuto"""
    if value == 1:
        led_status.config(text="LED ON", bg="green")
    else:
        led_status.config(text="LED OFF", bg="red")

def fire_machine(address, value):
    """Accende n LED in base al valore ricevuto (0-2)"""
    for i in range(3):
        if i < value:
            fire_leds[i].config(text="ON", bg="orange")
        else:
            fire_leds[i].config(text="OFF", bg="gray")

dispatcher = Dispatcher()
dispatcher.map("/lights", toggle_led)  # Gestisce il LED principale
dispatcher.map("/fireMachine", fire_machine)  # Gestisce i LED multipli

# Configurazione del server OSC
server = ThreadingOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher)

# Avvio del server in un thread separato
def start_osc_server():
    print(f"In ascolto su {SERVER_IP}:{SERVER_PORT} per {CLIENT_IP}...")
    server.serve_forever()

import threading
server_thread = threading.Thread(target=start_osc_server, daemon=True)
server_thread.start()

# Avvio della GUI
tk.mainloop()
