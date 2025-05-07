#ifndef OSCSERVER_H
#define OSCSERVER_H

#include <QObject>
#include "gpioHandler.h"
#include <lo/lo.h>

class OscServer : public QObject
{
    Q_OBJECT

public:
    explicit OscServer(GpioHandler *gpioHandler, QObject *parent = nullptr);
    ~OscServer();

    void start(const QString &ip, int port);

private:
    static int lightsHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data);
    static int fireMachineHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data);
    static int blindersHandler(const char *path, const char *types, lo_arg **argv, int argc, lo_message msg, void *user_data);

    GpioHandler *gpio;
    lo_server_thread serverThread;

signals:
    void sendGPIOStatus(int led, int blinders, int firePin1, int firePin2, int firePin3);
};

#endif // OSCSERVER_H
