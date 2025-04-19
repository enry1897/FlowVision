#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QLabel>
#include <QVector>
#include "GpioController.h"
#include "GpioHandler.h"
#include "OSCServer.h"

const int LED_PIN      = 17;
const int FIRE_PIN     = 27;
const int BLINDERS_PIN = 22;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onToggleLed(int value);
    void onFireMachine(int value);
    void onToggleBlinders(int value);

private:
    void setupUi();
    void updateGpioStatus();

private:
    QLabel *ledStatus;
    QLabel *gpioStatus;
    QVector<QLabel*> fireLeds;
    QLabel *blinderLed;

    GpioHandler myGpioHandler;
    OSCServer oscServer;
};

#endif // MAINWINDOW_H
