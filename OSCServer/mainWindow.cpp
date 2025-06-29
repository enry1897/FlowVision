#include "mainWindow.h"
#include <QDebug>

/**
 * @brief MainWindow::MainWindow manages the GUI application and configures all connets and launches OSCServer Backend
 * @author Davide Lorenzi
 * @param parent
 */
MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), oscServer(new OscServer(&gpio, this))
{
    ui.setupUi(this);  // <-- inizializzazione della UI da .ui

    // Connect dei pulsanti definiti nel file .ui
    if(!connect(this->ui.pb_led_17      , &QPushButton::clicked, this, &MainWindow::onManualLedToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_blinders_27 , &QPushButton::clicked, this, &MainWindow::onManualBlinderToggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_FM_1_22     , &QPushButton::clicked, this, &MainWindow::onManualFire1Toggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_FM_2_23     , &QPushButton::clicked, this, &MainWindow::onManualFire2Toggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_FM_3_24     , &QPushButton::clicked, this, &MainWindow::onManualFire3Toggle)) Q_ASSERT(false);
    if(!connect(this->ui.pb_enable_all  , &QPushButton::clicked, this, &MainWindow::onPbEnableAllClicked)) Q_ASSERT(false);
    if(!connect(this->ui.pb_disable_all , &QPushButton::clicked, this, &MainWindow::onPbDisableAllClicked)) Q_ASSERT(false);
    if(!connect(this->oscServer         , &OscServer::sendGPIOStatus,this, &MainWindow::updateGPIOStatusFromOSC)) Q_ASSERT(false);


    this->oscServer->start("192.168.1.19",8100);

    //init port status

    this->ledStatus = false;
    this->fire1Status = false;
    this->fire2Status = false;
    this->fire3Status = false;
    this->blinderStatus = false;

    //reset stats
    gpio.setOutput(LED_PIN, this->ledStatus);
    gpio.setOutput(FIRE_PIN_1, this->fire1Status);
    gpio.setOutput(FIRE_PIN_2, this->fire2Status);
    gpio.setOutput(FIRE_PIN_3, this->fire3Status);
    gpio.setOutput(BLINDER_PIN, this->blinderStatus);

    this->checkTimer = new QTimer(this);
    this->checkTimer->setInterval(20);

    if (!connect(checkTimer, &QTimer::timeout, this, &MainWindow::checkRoutine)) Q_ASSERT(false);
    this->checkTimer->start();


}


MainWindow::~MainWindow()
{
    delete oscServer;
}

/**
 * @brief MainWindow::checkRoutine gui update routine
 */
void MainWindow::checkRoutine()
{
    this->ui.lbl_GPIO17_LED_status->setText(this->ledStatus ? "ON" : "OFF");
    this->ui.lbl_GPIO27_blinders_status->setText(this->blinderStatus ? "ON" : "OFF");
    this->ui.lbl_GPIO22_FM_1_status->setText(this->fire1Status ? "ON" : "OFF");
    this->ui.lbl_GPIO23_FM_2_status->setText(this->fire2Status ? "ON" : "OFF");
    this->ui.lbl_GPIO24_FM_3_status->setText(this->fire3Status ? "ON" : "OFF");
}


/**
 * @brief MainWindow::onPbEnableAllClicked enables all gpios
 */
void MainWindow::onPbEnableAllClicked()
{
    this->ledStatus = gpio.setOutput(LED_PIN,s_ON);
    this->blinderStatus = gpio.setOutput(BLINDER_PIN,s_ON);
    this->fire1Status = gpio.setOutput(FIRE_PIN_1,s_ON);
    this->fire2Status = gpio.setOutput(FIRE_PIN_2,s_ON);
    this->fire3Status = gpio.setOutput(FIRE_PIN_3,s_ON);

}

/**
 * @brief MainWindow::onPbDisableAllClicked resets all GPIO status
 */
void MainWindow::onPbDisableAllClicked()
{
    this->ledStatus = gpio.setOutput(LED_PIN,s_OFF);
    this->blinderStatus = gpio.setOutput(BLINDER_PIN,s_OFF);
    this->fire1Status = gpio.setOutput(FIRE_PIN_1,s_OFF);
    this->fire2Status = gpio.setOutput(FIRE_PIN_2,s_OFF);
    this->fire3Status = gpio.setOutput(FIRE_PIN_3,s_OFF);
}

/**
 * @brief MainWindow::onManualLedToggle  changes the value of led
 */
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

/**
 * @brief MainWindow::onManualFire1Toggle  changes the value of Fire Machine 1
 */
void MainWindow::onManualFire1Toggle()
{
    //bool currentState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->fire1Status;
    printf("[FIRE] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->fire1Status = gpio.setOutput(FIRE_PIN_1, newState);

    //bool updatedState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

/**
 * @brief MainWindow::onManualFire2Toggle changes the value of Fire Machine 2
 */
void MainWindow::onManualFire2Toggle()
{
    //bool currentState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->fire2Status;
    printf("[FIRE] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->fire2Status = gpio.setOutput(FIRE_PIN_2, newState);

    //bool updatedState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

/**
 * @brief MainWindow::onManualFire3Toggle changes the value of Fire Machine 3
 */
void MainWindow::onManualFire3Toggle()
{
    //bool currentState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Current state: %s\n", currentState ? "ON" : "OFF");

    bool newState = !this->fire3Status;
    printf("[FIRE] Applying new state: %s\n", newState ? "ON" : "OFF");
    this->fire3Status = gpio.setOutput(FIRE_PIN_3, newState);

    //bool updatedState = gpio.readInput(FIRE_PIN);
    //printf("[FIRE] Updated state: %s\n", updatedState ? "ON" : "OFF");

}

/**
 * @brief MainWindow::onManualBlinderToggle changes the value of blinder
 */
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

/**
 * @brief MainWindow::updateGPIOStatusFromOSC gets GPIO status info from OSC
 * @param led status
 * @param blinders status
 * @param firePin1 status
 * @param firePin2 status
 * @param firePin3 status
 */
void MainWindow::updateGPIOStatusFromOSC(int led, int blinders, int firePin1, int firePin2, int firePin3)
{
    this->ledStatus = led;
    this->fire1Status = firePin1;
    this->fire2Status = firePin2;
    this->fire3Status = firePin3;
    this->blinderStatus = blinders;
}

