#include "gpioHandler.h"
#include <QDebug>

#define GPIO_CHIP_PATH "/dev/gpiochip0"

/**
 * @brief GpioHandler::GpioHandler
 */
GpioHandler::GpioHandler()
{
    chip = gpiod_chip_open(GPIO_CHIP_PATH);
    if (!chip)
    {
        qCritical() << "Failed to open GPIO chip";
    }
}

/**
 * @brief GpioHandler::~GpioHandler
 */
GpioHandler::~GpioHandler()
{
    cleanup();
}

/**
 * @brief GpioHandler::ensureLine
 * @param pin
 * @param output
 * @return
 */
struct gpiod_line *GpioHandler::ensureLine(int pin, bool output)
{
    if (!chip)
        return nullptr;

    if (lines.contains(pin))
    {
        if (lineIsOutput[pin] == output)
        {
            return lines[pin];  // Already configured correctly
        }
        else
        {
            // Release and reconfigure
            //gpiod_line_release(lines[pin]);
            lines.remove(pin);
            lineIsOutput.remove(pin);
        }
    }

    struct gpiod_line *line = gpiod_chip_get_line(chip, pin);
    if (!line)
    {
        qCritical() << "Failed to get GPIO line" << pin;
        return nullptr;
    }

    int ret = output
        ? gpiod_line_request_output(line, "OSCGpioServer", 0)
        : gpiod_line_request_input(line, "OSCGpioServer");

    if (ret < 0)
    {
        qCritical() << "Failed to request line" << pin << (output ? "as output" : "as input");
        return nullptr;
    }

    lines[pin] = line;
    lineIsOutput[pin] = output;
    return line;
}

/**
 * @brief GpioHandler::setOutput
 * @param pin
 * @param value
 * @return
 */
bool GpioHandler::setOutput(int pin, bool value)
{
    if (!chip)
        return false;

    struct gpiod_line *line = gpiod_chip_get_line(chip, pin);
    if (!line)
    {
        qCritical() << "Failed to get GPIO line" << pin;
        return false;
    }

    // Richiede il controllo del pin come uscita
    if (gpiod_line_request_output(line, "OSCGpioServer", 0) < 0)
    {
        qCritical() << "Failed to request line as output:" << pin;
        gpiod_line_release(line);
        return false;
    }

    // Imposta il valore
    if (gpiod_line_set_value(line, value) < 0)
    {
        qCritical() << "Failed to set line value:" << pin;
        return false;
    }


    // Rilascia la linea
    gpiod_line_release(line);
    return value;
}


/*bool GpioHandler::readInput(int pin)
{
    if (!chip)
        return false;

    struct gpiod_line *line = gpiod_chip_get_line(chip, pin);
    if (!line)
    {
        qCritical() << "Failed to get GPIO line" << pin;
        return false;
    }

    // Richiede il controllo del pin come ingresso
    if (gpiod_line_request_input(line, "OSCGpioServer") < 0)
    {
        qCritical() << "Failed to request line as input:" << pin;
        gpiod_line_release(line);
        return false;
    }

    // Legge il valore
    int value = gpiod_line_get_value(line);
    if (value < 0)
    {
        qCritical() << "Failed to read line value:" << pin;
        gpiod_line_release(line);
        return false;
    }

    gpiod_line_release(line);
    return value == 1;
}*/

/**
 * @brief GpioHandler::readInput
 * @param pin
 * @return
 */
bool GpioHandler::readInput(int pin)
{
    if (!chip)
        return false;

    if (!lines.contains(pin))
    {
        qWarning() << "Line" << pin << "has not been configured yet, skipping read to avoid reconfiguration";
        return false;
    }

    struct gpiod_line *line = lines[pin];

    // Legge il valore attuale (vale anche per linee in output)
    int value = gpiod_line_get_value(line);
    if (value < 0)
    {
        qCritical() << "Failed to read line value:" << pin << "errno:" << strerror(errno);
        return false;
    }

    return value == 1;
}


/**
 * @brief GpioHandler::cleanup
 */
void GpioHandler::cleanup()
{
    for (auto line : lines.values())
    {
        gpiod_line_release(line);
    }
    lines.clear();
    lineIsOutput.clear();

    if (chip)
    {
        gpiod_chip_close(chip);
        chip = nullptr;
    }
}
