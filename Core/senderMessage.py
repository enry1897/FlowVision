from pythonosc.udp_client import SimpleUDPClient
import time

# Configure the adress of the client (Processing)
ip = "0.0.0.0" # Localhost
port = 8000 # Port where we send the messages

# Create the client OSC
client = SimpleUDPClient(ip, port)

def send_number_bilnders():
    client.send_message("/blinders", number_to_send_blinders)
    print(f"Sending a number: {number_to_send_blinders}")

def send_number_lights():
    client.send_message("/lights", number_to_send_light)
    print(f"Sending a number: {number_to_send_light}")

def send_number_fire_machine():
    client.send_message("/fireMachine", number_to_send_fire_machine)
    print(f"Sending a number: {number_to_send_fire_machine}")

# Send an integer
#number_to_send_blinders = 1
#send_number_bilnders()

number_to_send_light = 0
while True:
    send_number_lights()
    time.sleep(3)
    number_to_send_light = 1 - number_to_send_light

#number_to_send_fire_machine = 2
#send_number_fire_machine()
