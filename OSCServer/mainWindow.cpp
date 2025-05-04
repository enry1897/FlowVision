#include "mainWindow.h"
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), oscServer(new OscServer(&gpio, this))
{
    ui.setupUi(this);  // <-- inizializzazione della UI da .ui

    // Connect dei pulsanti definiti nel file .ui
    if(!connect(this->ui.pb_led_17, &QPushButton::clicked, this, &MainWindow::onManualLedToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_fire_27, &QPushButton::clicked, this, &MainWindow::onManualFireToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_blinders_22, &QPushButton::clicked, this, &MainWindow::onManualBlinderToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_enable_all, &QPushButton::clicked, this, &MainWindow::onPbEnableAllClicked)) Q_ASSERT(false);
    if(!connect(this->ui.pb_disable_all, &QPushButton::clicked, this, &MainWindow::onPbDisableAllClicked)) Q_ASSERT(false);


    this->oscServer->start("192.168.1.19", 8100);

    this->checkTimer = new QTimer(this);
    this->checkTimer->setInterval(20);

    if (!connect(checkTimer, &QTimer::timeout, this, &MainWindow::checkRoutine)) Q_ASSERT(false);
    this->checkTimer->start();


    //init port status

    this->ledStatus = false;
    this->fireStatus = false;
    this->blinderStatus = false;


    gpio.setOutput(LED_PIN, this->ledStatus);
    gpio.setOutput(FIRE_PIN, this->fireStatus);
    gpio.setOutput(BLINDER_PIN, this->blinderStatus);


}


MainWindow::~MainWindow()
{
    delete oscServer;
}


void MainWindow::checkRoutine()
{
    this->ui.lbl_GPIO17_status->setText(this->ledStatus ? "ON" : "OFF");
    this->ui.lbl_GPIO27_status->setText(this->fireStatus ? "ON" : "OFF");
    this->ui.lbl_GPIO22_status->setText(this->blinderStatus ? "ON" : "OFF");
}



void MainWindow::onPbEnableAllClicked()
{
    this->ledStatus = gpio.setOutput(LED_PIN,s_ON);
    this->blinderStatus = gpio.setOutput(BLINDER_PIN,s_ON);
    this->fireStatus = gpio.setOutput(FIRE_PIN,s_ON);

}

void MainWindow::onPbDisableAllClicked()
{
    this->ledStatus = gpio.setOutput(LED_PIN,s_OFF);
    this->blinderStatus = gpio.setOutput(BLINDER_PIN,s_OFF);
    this->fireStatus = gpio.setOutput(FIRE_PIN,s_OFF);
}

void MainWindow::onManualLedToggle()
{
    //bool currentState = gpio.readInput(LED_PIN);
    //printf("[LED] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->ledStatus;
    printf("[LED] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->ledStatus = gpio.setOutput(LED_PIN, newState);

    //bool updatedState = gpio.readInput(LED_PIN);
    //printf("[LED] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

void MainWindow::onManualFireToggle()
{
    //bool currentState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->fireStatus;
    printf("[FIRE] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->fireStatus = gpio.setOutput(FIRE_PIN, newState);

    //bool updatedState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

void MainWindow::onManualBlinderToggle()
{
    //bool currentState = gpio.readInput(BLINDER_PIN);
    //printf("[BLINDER] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->blinderStatus;
    printf("[BLINDER] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->blinderStatus = gpio.setOutput(BLINDER_PIN, newState);

    //ool updatedState = gpio.readInput(BLINDER_PIN);
    //rintf("[BLINDER] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

