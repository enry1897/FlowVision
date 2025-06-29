#include "oscServer.h"
#include <QDebug>

/**
 * @brief OscServer::OscServer Main OSC server class, manages interactions between
 * @author Davide Lorenzi
 * @param gpioHandler
 * @param parent
 */
OscServer::OscServer(GpioHandler *gpioHandler, QObject *parent)
    : QObject(parent),
      gpio(gpioHandler),
      serverThread(nullptr)
{
}

/**
 * @brief OscServer::~OscServer
 */
OscServer::~OscServer()
{
    if (this->serverThread)
    {
        lo_server_thread_free(this->serverThread);
    }
}

/**
 * @brief OscServer::start OSC Server that starts thre server thread and begin listening
 * @param ip
 * @param port
 */
void OscServer::start(const QString &ip, int port)
{
    Q_UNUSED(ip); // Liblo does not accepts directly IP
    QString portStr = QString::number(port);

    qDebug() << "Starting OSC server on port" << portStr;

    this->serverThread = lo_server_thread_new_with_proto(portStr.toStdString().c_str(), LO_UDP, nullptr);
    if (!this->serverThread)
    {
        qCritical() << "Failed to create OSC server thread.";
        return;
    }

    lo_method m1 = lo_server_thread_add_method(this->serverThread, "/lights", "i", lightsHandler, this);
    lo_method m2 = lo_server_thread_add_method(this->serverThread, "/fireMachine", "i", fireMachineHandler, this);
    lo_method m3 = lo_server_thread_add_method(this->serverThread, "/blinders", "i", blindersHandler, this);

    if (!m1 || !m2 || !m3)
    {
        qCritical() << "Failed to add one or more OSC methods.";
        return;
    }

    lo_server_thread_start(this->serverThread);

    qDebug() << "OSC server started.";
}

/**
 * @brief OscServer::lightsHandler gets values from lights hand command and emits signal for start actions
 * @param path
 * @param types
 * @param argv
 * @param argc
 * @param msg
 * @param user_data
 * @return
 */
int OscServer::lightsHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    OscServer *self = static_cast<OscServer *>(user_data);
    int value = argv[0]->i;

    qDebug() << "Received /lights:" << (value ? "ON" : "OFF");

    self->gpio->setOutput(LED_PIN, value);
    emit self->sendGPIOStatus(value, s_OFF, s_OFF, s_OFF, s_OFF);

    return 0;
}

/**
 * @brief OscServer::fireMachineHandler  gets values from fire machine hand command and emits signal for start actions
 * @param path
 * @param types
 * @param argv
 * @param argc
 * @param msg
 * @param user_data
 * @return
 */
int OscServer::fireMachineHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    OscServer *self = static_cast<OscServer *>(user_data);
    int value = std::round((argv[0]->i)/3);

    int fire1 = s_OFF;
    int fire2 = s_OFF;
    int fire3 = s_OFF;

    switch (value)
    {
    case 0:
        break;
    case 1:
        fire1 = s_ON;
        break;
    case 2:
        fire1 = s_ON;
        fire2 = s_ON;
        break;
    case 3:
        fire1 = s_ON;
        fire2 = s_ON;
        fire3 = s_ON;
        break;
    default:
        qWarning() << "Invalid /fireMachine value:" << value;
        return 0;
    }

    self->gpio->setOutput(FIRE_PIN_1, fire1);
    self->gpio->setOutput(FIRE_PIN_2, fire2);
    self->gpio->setOutput(FIRE_PIN_3, fire3);

    emit self->sendGPIOStatus(s_OFF, s_OFF, fire1, fire2, fire3);

    return 0;
}

/**
 * @brief OscServer::blindersHandler gets values from blinders hand command and emits signal for start actions
 * @param path
 * @param types
 * @param argv
 * @param argc
 * @param msg
 * @param user_data
 * @return
 */
int OscServer::blindersHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    OscServer *self = static_cast<OscServer *>(user_data);
    int value = argv[0]->i;

    qDebug() << "Received /blinders:" << (value ? "ON" : "OFF");

    self->gpio->setOutput(BLINDER_PIN, value);
    emit self->sendGPIOStatus(s_OFF, value, s_OFF, s_OFF, s_OFF);

    return 0;
}
