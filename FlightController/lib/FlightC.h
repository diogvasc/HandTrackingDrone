#ifndef FLIGHTC_H
#define FLIGHTC_H

#include <Arduino.h>
#include "BluetoothSerial.h"

namespace FlightC {

extern BluetoothSerial SerialBT;

    struct SepValues {  // depois serão 4
        float val1;
        float val2;
    };

    class Controller {
        public:
            Controller();
            ~Controller();
            void prog(int PWM_pin);           // sem SepValues
            void setTarget(SepValues sv);     // define o target
            void setVal(int pin, int val);
            SepValues btReceiver();
        
        private:
            static const int MAX_PWM = 255;
            static const int MIN_PWM = 0;
            int val = 0;
            int target = 0;   // <-- novo
            int U, D, L, R;
            SepValues sepValues;
        };
} // namespace FlightC

#endif
