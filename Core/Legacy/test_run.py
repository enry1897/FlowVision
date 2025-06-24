import threading
import time
from FlowVision_run_function import run  # importa la funzione run

stop_event = threading.Event()

def start():
    print("Starting tracking...")
    run(stop_event)

try:
    t = threading.Thread(target=start)
    t.start()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")
    stop_event.set()
    t.join()