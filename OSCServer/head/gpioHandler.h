#ifndef GPIOHANDLER_H
#define GPIOHANDLER_H

#include <gpiod.h>
#include <QString>
#include <QMap>

const int LED_PIN = 17;
const int BLINDER_PIN = 27;
const int FIRE_PIN_1 = 22;
const int FIRE_PIN_2 = 23;
const int FIRE_PIN_3 = 24;


enum gpio_status
{
    s_OFF = 0,
    s_ON = 1,
    s_Count
};

class GpioHandler
{
public:
    GpioHandler();
    ~GpioHandler();

    bool setOutput(int pin, bool value);
    bool readInput(int pin);

    void cleanup();

private:
    struct gpiod_chip *chip;
    QMap<int, struct gpiod_line *> lines;
    QMap<int, bool> lineIsOutput;

    struct gpiod_line *ensureLine(int pin, bool output);
};

#endif // GPIOHANDLER_H
