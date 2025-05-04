#include "mainWindow.h"
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), oscServer(new OscServer(&gpio, this))
{
    ui.setupUi(this);  // <-- inizializzazione della UI da .ui

    // Connect dei pulsanti definiti nel file .ui
    if(!connect(this->ui.pb_led_17, &QPushButton::clicked, this, &MainWindow::onManualLedToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_fire_22, &QPushButton::clicked, this, &MainWindow::onManualFireToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_blinders_27, &QPushButton::clicked, this, &MainWindow::onManualBlinderToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_enable_all, &QPushButton::clicked, this, &MainWindow::onPbEnableAllClicked)) Q_ASSERT(false);
    if(!connect(this->ui.pb_disable_all, &QPushButton::clicked, this, &MainWindow::onPbDisableAllClicked)) Q_ASSERT(false);


    this->oscServer->start("192.168.1.19", 8100);

    this->checkTimer = new QTimer(this);
    this->checkTimer->setInterval(20);

    if (!connect(checkTimer, &QTimer::timeout, this, &MainWindow::checkRoutine)) Q_ASSERT(false);
    this->checkTimer->start();

}


MainWindow::~MainWindow()
{
    delete oscServer;
}


void MainWindow::checkRoutine()
{
    /*bool stateLed     = gpio.readInput(LED_PIN);
    bool stateFire    = gpio.readInput(FIRE_PIN);
    bool stateBlinder = gpio.readInput(BLINDER_PIN);

    this->ui.lbl_GPIO17_status->setText(stateLed ? "ON" : "OFF");
    this->ui.lbl_GPIO27_status->setText(stateFire ? "ON" : "OFF");
    this->ui.lbl_GPIO22_status->setText(stateBlinder ? "ON" : "OFF");*/
}



void MainWindow::onPbEnableAllClicked()
{
    gpio.setOutput(LED_PIN,s_ON);
    gpio.setOutput(BLINDER_PIN,s_ON);
    gpio.setOutput(FIRE_PIN,s_ON);

}

void MainWindow::onPbDisableAllClicked()
{
    gpio.setOutput(LED_PIN,s_OFF);
    gpio.setOutput(BLINDER_PIN,s_OFF);
    gpio.setOutput(FIRE_PIN,s_OFF);
}

void MainWindow::onManualLedToggle()
{
    bool currentState = gpio.readInput(LED_PIN);
    printf("[LED] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !currentState;
    printf("[LED] Applying new state: %s\n", newState ? "ON" : "OFF");
    gpio.setOutput(LED_PIN, newState);

    bool updatedState = gpio.readInput(LED_PIN);
    printf("[LED] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

void MainWindow::onManualFireToggle()
{
    bool currentState = gpio.readInput(FIRE_PIN);
    printf("[FIRE] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !currentState;
    printf("[FIRE] Applying new state: %s\n", newState ? "ON" : "OFF");
    gpio.setOutput(FIRE_PIN, newState);

    bool updatedState = gpio.readInput(FIRE_PIN);
    printf("[FIRE] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

void MainWindow::onManualBlinderToggle()
{
    bool currentState = gpio.readInput(BLINDER_PIN);
    printf("[BLINDER] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !currentState;
    printf("[BLINDER] Applying new state: %s\n", newState ? "ON" : "OFF");
    gpio.setOutput(BLINDER_PIN, newState);

    bool updatedState = gpio.readInput(BLINDER_PIN);
    printf("[BLINDER] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

