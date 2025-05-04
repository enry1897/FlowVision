#include "oscServer.h"
#include <QDebug>



OscServer::OscServer(GpioHandler *gpioHandler, QObject *parent)
    : QObject(parent), gpio(gpioHandler), serverThread(nullptr)
{
}

OscServer::~OscServer()
{
    if (serverThread)
    {
        lo_server_thread_free(serverThread);
    }
}

void OscServer::start(const QString &ip, int port)
{
    serverThread = lo_server_thread_new_with_proto(nullptr, LO_UDP, nullptr);

    Q_ASSERT(serverThread != nullptr);

    lo_server_thread_add_method(serverThread, "/lights", "i", lightsHandler, gpio);
    lo_server_thread_add_method(serverThread, "/fireMachine", "i", fireMachineHandler, gpio);
    lo_server_thread_add_method(serverThread, "/blinders", "i", blindersHandler, gpio);

    lo_server_thread_start(serverThread);

    qDebug() << "OSC Server started on port" << port;
}

int OscServer::lightsHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);
    gpio->setOutput(LED_PIN, argv[0]->i);

    return 0;
}

int OscServer::fireMachineHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);
    gpio->setOutput(FIRE_PIN, argv[0]->i);

    return 0;
}

int OscServer::blindersHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data)
{
    Q_UNUSED(path);
    Q_UNUSED(types);
    Q_UNUSED(argc);
    Q_UNUSED(msg);

    GpioHandler *gpio = static_cast<GpioHandler *>(user_data);
    gpio->setOutput(BLINDER_PIN, argv[0]->i);

    return 0;
}
