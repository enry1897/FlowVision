import time
import threading

current_counter_value = 0

def run(stop_event: threading.Event):
    """
    Simula un'operazione che incrementa un valore nel tempo e lo restituisce.
    Accetta un threading.Event per segnalare l'interruzione.
    """
    
    global current_counter_value
    current_counter_value = 0

    print("-------------------------------------------------------")
    print("Avvio dello script di incremento (simple_main.py)...")
    print("-------------------------------------------------------")
    
    counter = 0
    max_increments = 10

    for i in range(max_increments):
        if stop_event.is_set():
            print("Script interrotto da segnale esterno.")
            break

        current_counter_value += 10
        print(f"Contatore attuale: {current_counter_value} (dopo {5 * (i + 1)} secondi)")

        for _ in range(10):
            if stop_event.is_set():
                print("Script interrotto durante il time.sleep().")
                break
            time.sleep(0.5)

        if stop_event.is_set():
            break

    final_value_message = ""
    if stop_event.is_set():
        final_message = f"Script interrotto. Valore al momento dell'interruzione: {current_counter_value}"
    else:
        final_message = f"Script completato. Valore finale: {current_counter_value}"

    print("-------------------------------------------------------")
    print(final_message)
    print("-------------------------------------------------------")

    return final_message
    
if __name__ == "__main__":
    test_stop_event = threading.Event()
    run(test_stop_event)
    print(f"Valore finale nel main: {current_counter_value}")
