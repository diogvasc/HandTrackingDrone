#ifndef FLIGHTC_H
#define FLIGHTC_H

#include <Arduino.h>
#include "BluetoothSerial.h"

namespace FlightC {

   //extern BluetoothSerial SerialBT;

    struct SepValues {  // depois serão 4
        float val1;
        float val2;
    };

    class Controller {
    public:
        Controller();
        ~Controller();

        int progUp(int PWM_pin);
        int progDown(int PWM_pin);

        void setVal(int pin, int val);

        SepValues btReceiver();

    private:
        static const int MAX_PWM = 181;
        static const int MIN_PWM = 1;

        int U;  
        int D;
        int L;  
        int R;
        SepValues sepValues; // set[0] para esquerda, set[1] para direita
    };
} // namespace FlightC

#endif
