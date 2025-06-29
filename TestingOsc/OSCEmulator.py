import time
import random
from pythonosc import udp_client

# Configurazione client OSC
ip = "127.0.0.1"  # Cambia con l'IP del Raspberry Pi se necessario
port = 8000
client = udp_client.SimpleUDPClient(ip, port)

commands = [
    ("/on CUORE", "/off CUORE"),
    ("/on MANO", "/off MANO"),
    ("/mani", "/mani")  # Manderà un valore casuale tra 1 e 3
]

while True:
    cmd_on, cmd_off = random.choice(commands)

    if cmd_on == "/mani":
        level = random.randint(1, 3)
        print(f"Sending: {cmd_on} {level}")
        client.send_message(cmd_on, level)
    else:
        print(f"Sending: {cmd_on}")
        client.send_message(cmd_on, [])

    time.sleep(5)  # Attendi 5 secondi

    if cmd_off == "/mani":
        print(f"Sending: {cmd_off} 0")
        client.send_message(cmd_off, 0)  # Spegne tutto impostando livello 0
    else:
        print(f"Sending: {cmd_off}")
        client.send_message(cmd_off, [])

    time.sleep(5)  # Attendi altri 5 secondi prima di scegliere il prossimo