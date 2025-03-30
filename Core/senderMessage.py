from pythonosc.udp_client import SimpleUDPClient
import time

# Configure the adress of the client (Processing)
ip = "127.0.0.1" # Localhost
port = 12000 # Port where we send the messages

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
number_to_send_blinders = 1
send_number_bilnders()

number_to_send_light = 1
send_number_lights()

number_to_send_fire_machine = 12
send_number_fire_machine()
