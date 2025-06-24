import threading
import time
import signal
import sys

from main import run  # Assicurati che il modulo main.py sia nella stessa directory o nel PYTHONPATH

# Se il tuo codice è tutto nello stesso file, puoi ignorare la riga sopra.

def main():
    stop_event = threading.Event()
    tracking_thread = threading.Thread(target=run, args=(stop_event,))
    tracking_thread.start()

    def signal_handler(sig, frame):
        print("Ricevuto segnale di interruzione, arresto in corso...")
        stop_event.set()
        tracking_thread.join()
        print("Terminato.")
        sys.exit(0)

    # Registra Ctrl+C per stop
    signal.signal(signal.SIGINT, signal_handler)

    # Mantieni il processo attivo finché il thread è vivo
    try:
        while tracking_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
