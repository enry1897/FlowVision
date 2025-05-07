#include "oscServer.h"
#include <QDebug>
#include <lo/lo.h>  // Assicurati di includere la libreria liblo per l'OSC

OscServer::OscServer(GpioHandler *gpioHandler, QObject *parent)
    : QObject(parent), gpio(gpioHandler), serverThread(nullptr)
{
}

OscServer::~OscServer()
{
    if (this->serverThread)
    {
        lo_server_thread_free(this->serverThread);
    }
}

void OscServer::start(const QString &ip, int port)
{
    qDebug() << "Starting OSC server...";

    // Inizializza il server OSC con il protocollo UDP
    // Qui abbiamo esplicitamente specificato IP e porta
    this->serverThread = lo_server_thread_new_with_proto(/*ip.toStdString().c_str()*/"8100", LO_UDP, nullptr);

    if (this->serverThread == nullptr)
    {
        qCritical() << "Failed to create OSC server thread.";
        return;
    }

    qDebug() << "OSC Server thread created.";

    // Aggiungi i metodi per ciascun percorso
    lo_method methodLights = lo_server_thread_add_method(this->serverThread, "/lights", "i", lightsHandler, gpio);
    lo_method methodFireMachine = lo_server_thread_add_method(this->serverThread, "/fireMachine", "i", fireMachineHandler, gpio);
    lo_method methodBlinders = lo_server_thread_add_method(this->serverThread, "/blinders", "i", blindersHandler, gpio);

    // Verifica che i metodi siano stati aggiunti correttamente
    if (methodLights == nullptr || methodFireMachine == nullptr || methodBlinders == nullptr) {
        qCritical() << "Error adding methods to the server!";
        return;
    }
    qDebug() << "Methods successfully added to OSC server.";

    // Aggiungi un log per monitorare il comportamento prima di avviare il server
    qDebug() << "Starting the server thread...";

    // Avvia il server
    lo_server_thread_start(this->serverThread);

    qDebug() << "Server thread started.";

    // Log di conferma
    qDebug() << "OSC Server started on IP:" << ip << "Port:" << port;
}


int OscServer::lightsHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    // Log del messaggio ricevuto
    qDebug() << "Received /lights message with value:" << (argv[0]->i == 1 ? "ON" :"OFF");

    // Gestione GPIO per il controllo delle luci
    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);

    gpio->setOutput(LED_PIN, argv[0]->i);
    OscServer::setGPIOStatus(argv[0]->i,s_OFF,s_OFF,s_OFF,s_OFF);

    //reset other pins


    return 0;
}

int OscServer::fireMachineHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    // Log del messaggio ricevuto
    qDebug() << "Received /fireMachine message with value:" << (argv[0]->i == 1 ? "ON" :"OFF");

    // Gestione GPIO per la macchina del fuoco
    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);

    // Ottieni il valore dell'argomento
    int value = (argv[0]->i)/3;

    // Aggiungi uno switch per gestire i valori da 0 a 3
    switch (value)
    {
    case 0:
        qDebug() << "Received /lights with value 0: Turn OFF lights.";
        // Logica per spegnere le luci
        gpio->setOutput(FIRE_PIN_1, s_OFF);
        gpio->setOutput(FIRE_PIN_2, s_OFF);
        gpio->setOutput(FIRE_PIN_3, s_OFF);
        OscServer::setGPIOStatus(s_OFF,s_OFF,s_OFF,s_OFF,s_OFF);
        break;

    case 1:
        qDebug() << "Received /lights with value 1: Turn ON lights.";
        // Logica per accendere le luci
        gpio->setOutput(FIRE_PIN_1, s_ON);
        gpio->setOutput(FIRE_PIN_2, s_OFF);
        gpio->setOutput(FIRE_PIN_3, s_OFF);
        OscServer::setGPIOStatus(s_OFF,s_OFF,s_ON,s_OFF,s_OFF);
        break;

    case 2:
        qDebug() << "Received /lights with value 2: Dim lights.";
        // Logica per diminuire la luminosit� delle luci
        gpio->setOutput(FIRE_PIN_1, s_ON);
        gpio->setOutput(FIRE_PIN_2, s_ON);
        gpio->setOutput(FIRE_PIN_3, s_OFF);
        OscServer::setGPIOStatus(s_OFF,s_OFF,s_ON,s_ON,s_OFF);
        break;

    case 3:
        qDebug() << "Received /lights with value 3: Set lights to a special mode.";
        // Logica per modalit� speciale delle luci
        gpio->setOutput(FIRE_PIN_1, s_ON);
        gpio->setOutput(FIRE_PIN_2, s_ON);
        gpio->setOutput(FIRE_PIN_3, s_ON);
        OscServer::setGPIOStatus(s_OFF,s_OFF,s_ON,s_ON,s_ON);
        break;

    default:
        qWarning() << "Received invalid value for /lights: " << value;
        break;
    }

    return 0;
}

int OscServer::blindersHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    // Log del messaggio ricevuto
    qDebug() << "Received /blinders message with value:" << argv[0]->i;

    // Gestione GPIO per il controllo dei blinders
    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);

    gpio->setOutput(BLINDER_PIN, argv[0]->i);
    OscServer::setGPIOStatus(s_OFF,argv[0]->i,s_OFF,s_OFF,s_OFF);
    return 0;
}

void OscServer::setGPIOStatus(int led, int blinders, int firePin1, int firePin2,int firePin3)
{
    emit sendGPIOStatus(led,blinders,firePin1,firePin2,firePin3);
}
