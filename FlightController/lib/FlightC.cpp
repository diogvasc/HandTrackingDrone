#include "FlightC.h"
#include <Arduino.h>
#include "BluetoothSerial.h"

namespace FlightC {

    BluetoothSerial SerialBT;

    Controller::Controller() : U(0), D(0), L(0), R(0) {}
    Controller::~Controller() {}

    int Controller::progUp(int PWM_pin) {
        int val = 0;
        while (val < MAX_PWM) {
            val++;
            analogWrite(PWM_pin, val);
            delay(20);
        }
        return 0;
    }

    int Controller::progDown(int PWM_pin) {
        int val = MAX_PWM;
        while (val > MIN_PWM) {
            val--;
            analogWrite(PWM_pin, val);
            delay(20);
        }
        return 0;
    }

    void Controller::setVal(int pin, int val) {
        analogWrite(pin, val);
    }

    SepValues Controller::btReceiver() {
        SepValues sepValues = {0, 0};
        if (SerialBT.available()) {
            String data = SerialBT.readStringUntil('\n');
            int sep = data.indexOf(',');

            if (sep > 0) {
                sepValues.val1 = data.substring(0, sep).toFloat();
                sepValues.val2 = data.substring(sep + 1).toFloat();
            }
        }
        return sepValues;
    }

} 
