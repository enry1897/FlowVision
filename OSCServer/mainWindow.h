#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTimer>
#include "gpioHandler.h"
#include "oscServer.h"
#include "ui_mainWindow.h"  // <-- include dell'interfaccia grafica

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onManualLedToggle();
    void onManualFire1Toggle();
    void onManualFire2Toggle();
    void onManualFire3Toggle();
    void onManualBlinderToggle();
    void onPbEnableAllClicked();
    void onPbDisableAllClicked();

private:
    Ui::MainWindow ui;              // <-- istanza della UI
    GpioHandler gpio;
    OscServer *oscServer;

    bool ledStatus;
    bool fire1Status;
    bool fire2Status;
    bool fire3Status;
    bool blinderStatus;

    void checkRoutine();

    QTimer* checkTimer;
};

#endif // MAINWINDOW_H
