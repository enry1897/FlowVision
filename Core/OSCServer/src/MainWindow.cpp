#include "../head/MainWindow.h"
#include <QVBoxLayout>
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setupUi();

    // Connect OSC signals to slots
    connect(&oscServer, &OSCServer::toggleLed, this, &MainWindow::onToggleLed);
    connect(&oscServer, &OSCServer::fireMachine, this, &MainWindow::onFireMachine);
    connect(&oscServer, &OSCServer::toggleBlinders, this, &MainWindow::onToggleBlinders);

    if (!oscServer.start())
    {
        qWarning() << "OSC Server failed to start.";
    }

    updateGpioStatus();
}

MainWindow::~MainWindow()
{
    myGpioHandler.cleanup();
}

void MainWindow::setupUi()
{
    QWidget *central = new QWidget(this);
    QVBoxLayout *layout = new QVBoxLayout(central);

    setWindowTitle("OSC Server GUI");
    resize(350, 300);

    ledStatus = new QLabel("LED OFF", this);
    ledStatus->setStyleSheet("background-color: red; font-size: 16px;");
    ledStatus->setAlignment(Qt::AlignCenter);
    layout->addWidget(ledStatus);

    gpioStatus = new QLabel("GPIO Status", this);
    gpioStatus->setAlignment(Qt::AlignCenter);
    layout->addWidget(gpioStatus);

    for (int i = 0; i < 3; ++i)
    {
        QLabel *led = new QLabel("OFF", this);
        led->setStyleSheet("background-color: gray; font-size: 12px;");
        led->setAlignment(Qt::AlignCenter);
        led->setMinimumWidth(100);
        layout->addWidget(led);
        fireLeds.append(led);
    }

    blinderLed = new QLabel("BLINDER OFF", this);
    blinderLed->setStyleSheet("background-color: gray; font-size: 12px;");
    blinderLed->setAlignment(Qt::AlignCenter);
    blinderLed->setMinimumWidth(120);
    layout->addWidget(blinderLed);

    setCentralWidget(central);
}

void MainWindow::updateGpioStatus()
{
    QString status = QString("GPIO led_pin: %1, GPIO fire_pin: %2, GPIO blinders_pin: %3")
            .arg(myGpioHandler.input(LED_PIN) ? "HIGH" : "LOW")
            .arg(myGpioHandler.input(FIRE_PIN) ? "HIGH" : "LOW")
            .arg(myGpioHandler.input(BLINDERS_PIN) ? "HIGH" : "LOW");

    gpioStatus->setText(status);
}

void MainWindow::onToggleLed(int value)
{
    qDebug() << "OSC: Toggle LED to" << value;
    myGpioHandler.output(LED_PIN, value);
    ledStatus->setText(value ? "LED ON" : "LED OFF");
    ledStatus->setStyleSheet(QString("background-color: %1; font-size: 16px;").arg(value ? "green" : "red"));
    updateGpioStatus();
}

void MainWindow::onFireMachine(int value)
{
    qDebug() << "OSC: Fire machine level" << value;
    myGpioHandler.output(FIRE_PIN, value > 0 ? 1 : 0);

    for (int i = 0; i < fireLeds.size(); ++i)
    {
        if (i < value)
        {
            fireLeds[i]->setText("ON");
            fireLeds[i]->setStyleSheet("background-color: orange; font-size: 12px;");
        }
        else
        {
            fireLeds[i]->setText("OFF");
            fireLeds[i]->setStyleSheet("background-color: gray; font-size: 12px;");
        }
    }

    updateGpioStatus();
}

void MainWindow::onToggleBlinders(int value)
{
    qDebug() << "OSC: Toggle Blinders to" << value;
    myGpioHandler.output(BLINDERS_PIN, value);
    blinderLed->setText(value ? "BLINDER ON" : "BLINDER OFF");
    blinderLed->setStyleSheet(QString("background-color: %1; font-size: 12px;")
                              .arg(value ? "yellow" : "gray"));
    updateGpioStatus();
}
