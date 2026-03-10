#ifndef FLIGHTC_H
#define FLIGHTC_H

#include <Arduino.h>
#include "BluetoothSerial.h"

namespace FlightC {

    // Bluetooth global
    extern BluetoothSerial SerialBT;

    class Controller {
    public:
        Controller();
        ~Controller();

        // Funções para aumentar/diminuir PWM gradualmente
        int progUp(int PWM_pin);
        int progDown(int PWM_pin);

        // Define valor direto no PWM ou DAC
        void setVal(int pin, int val);

        // Recebe dados via Bluetooth
        void btReceiver();

    private:
        static const int MAX_PWM = 181;
        static const int MIN_PWM = 1;

        // Valores para controle do drone (PID ou inputs)
        int U;  
        int D;
        int L;  
        int R;
    };

    // Função de recebimento global via Bluetooth (opcional)
    void btReceiver();

} // namespace FlightC

#endif

