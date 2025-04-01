from pythonosc.udp_client import SimpleUDPClient
import time
import random

# Indirizzo del server OSC
ip = "192.168.1.19"
port = 8100

client = SimpleUDPClient(ip, port)

def send_number_blinders():
    """Send ON/OFF signal to /blinders"""
    client.send_message("/blinders", 1)
    print("Sending blinders ON")
    time.sleep(1)
    client.send_message("/blinders", 0)
    print("Sending blinders OFF")

def send_number_lights():
    """Send ON/OFF signal to /lights"""
    global number_to_send_light
    client.send_message("/lights", number_to_send_light)
    print(f"Sending lights: {number_to_send_light}")

def send_number_fire_machine():
    """Send random number to /fireMachine (0-3)"""
    global number_to_send_fire_machine
    client.send_message("/fireMachine", number_to_send_fire_machine)
    print(f"Sending fireMachine: {number_to_send_fire_machine}")

number_to_send_light = 0
number_to_send_fire_machine = 0

while True:
    send_number_lights()
    send_number_fire_machine()
    send_number_blinders()  # Added blinders control
    time.sleep(3 + random.randint(0, 3))  # Random delay between 3 and 7 seconds

    number_to_send_light = 1 - number_to_send_light
    number_to_send_fire_machine = random.randint(0, 3)
