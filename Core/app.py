from flask import Flask, render_template_string, redirect, url_for, request, session
import main 
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'una_chiave_molto_segreta' 

# Variabili globali per tracciare lo stato dello script e il thread
# Queste devono essere accessibili da diverse richieste.
running_script_thread = None
script_stop_event = threading.Event() # L'evento per segnalare l'interruzione

# Non mostreremo l'output dello script, ma manterremo lo stato del bottone
script_is_active = False # Indica se c'è un processo di script "logicamente" in esecuzione

TEMPLATE = """
<!doctype html>
<title>FlowVision</title>
<style>
    body {
        font-family: sans-serif;
        display: flex;
        flex-direction: column; 
        justify-content: center; 
        align-items: center; 
        min-height: 100vh; 
        margin: 0;
        background-color: #f4f4f4;
        color: #333;
    }
    .container {
        text-align: center; 
        background-color: #fff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        max-width: 600px;
        width: 90%;
    }
    h2 {
        color: #2c3e50;
        margin-bottom: 25px;
    }
    button {
        padding: 15px 30px;
        font-size: 1.2em;
        cursor: pointer;
        border: none;
        border-radius: 5px;
        transition: background-color 0.3s ease, transform 0.2s ease;
        background-color: #007bff; 
        color: white;
    }
    button:hover {
        background-color: #0056b3; 
        transform: translateY(-2px);
    }
    button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }
    p {
        margin-top: 15px;
        font-size: 1.1em;
    }
</style>
<div class="container">
    <h2>Flow Vision</h2>
    <form action="/toggle_script" method="post">
        <button type="submit" id="mainButton">{{ 'Interrompi' if script_is_active else 'Avvia' }}</button>
    </form>
    {% if message %}
        <p style="color: green;">{{ message }}</p>
    {% endif %}
    {% if error %}
        <p style="color: red;">{{ error}}</p>
    {% endif %}
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const mainButton = document.getElementById('mainButton');
        const form = mainButton.closest('form');

        form.addEventListener('submit', function() {
            if (mainButton.textContent.trim() === 'Avvia') {
                mainButton.disabled = true;
                mainButton.textContent = 'Esecuzione in corso...';
            }
            // Se il bottone è "Interrompi", lo lasciamo abilitato perché la richiesta di stop è rapida.
        });
    });
</script>
"""

@app.route("/")
def home():
    global script_is_active, running_script_thread

    message = request.args.get('message')
    error = request.args.get('error')

    # Al caricamento della home, verifica se il thread è ancora vivo ma non dovrebbe esserlo logicamente
    # Oppure se era attivo e si è concluso da solo
    if running_script_thread and not running_script_thread.is_alive() and script_is_active:
        script_is_active = False # Se il thread è morto, aggiorna lo stato logico
        print("Il thread dello script è terminato inaspettatamente o ha completato l'esecuzione.")

    # Logica di reset esplicito dalla sessione (dopo aver cliccato "Interrompi")
    if 'reset_requested' in session:
        session.pop('reset_requested', None)
        script_is_active = False 
        message = "Pagina resettata." 
        error = None 
    
    return render_template_string(
        TEMPLATE, 
        message=message, 
        error=error, 
        script_is_active=script_is_active # Passa lo stato logico al template
    )

@app.route("/toggle_script", methods=["POST"])
def toggle_script():
    global script_is_active, running_script_thread, script_stop_event

    if script_is_active: # Se il bottone dice "Interrompi" e lo script è attivo
        # Segnala al thread di fermarsi
        script_stop_event.set() 
        
        print("Segnale di interruzione inviato al thread.")
        # Attendi che il thread termini (opzionale, ma buona pratica per la pulizia)
        if running_script_thread and running_script_thread.is_alive():
            # Aumentato il timeout in caso il rilascio della risorsa RealSense richieda più tempo
            running_script_thread.join(timeout=20) 
            if running_script_thread.is_alive():
                print("Attenzione: Il thread non si è fermato entro il timeout.")
            else:
                print("Il thread dello script è stato terminato.")

        session['reset_requested'] = True # Richiedi il reset della pagina
        script_is_active = False # Aggiorna lo stato logico
        
        return redirect(url_for("home", message="Script interrotto e pagina resettata."))
    else: # Se il bottone dice "Avvia"
        # Reset dell'evento di stop per un nuovo avvio
        script_stop_event.clear() 

        # Avvia il thread dello script
        # Modifica qui: passa script_stop_event come argomento alla funzione run
        running_script_thread = threading.Thread(target=main.run, args=(script_stop_event,))
        running_script_thread.daemon = True # Il thread si chiude quando l'app Flask si chiude
        running_script_thread.start()
        
        script_is_active = True # Imposta lo stato logico a attivo

        print("Script avviato in un thread separato.")
        # Reindirizza immediatamente alla home.
        # L'output dello script non viene più passato tramite URL perché non lo mostriamo.
        return redirect(url_for("home", message="Script avviato. Puoi interromperlo cliccando di nuovo."))

if __name__== "__main__":
    app.run(host="0.0.0.0", port=7700, debug=True, use_reloader=False)
