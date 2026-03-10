
#include "FlightC.h"
#include <Arduino.h>

namespace FlightC {

    // Definição do objeto global BluetoothSerial
    BluetoothSerial SerialBT;

    // ----------------- Controller -----------------
    Controller::Controller() : U(0), D(0), L(0), R(0) {}
    Controller::~Controller() {}

    int Controller::progUp(int PWM_pin) {
        int val = 0;
        while (val < MAX_PWM) {
            val++;
            analogWrite(PWM_pin, val);
            delay(20); // ajuste a velocidade do ramp
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
        // Para PWM:
        analogWrite(pin, val); 
        // Se usar DAC no ESP32, use dacWrite(pin, val);
    }

    void Controller::btReceiver() {
        if (SerialBT.available()) {
            String data = SerialBT.readStringUntil('\n');
            Serial.print("Recebido via BT: ");
            Serial.println(data);
            // Aqui podes processar comandos, atualizar PID, etc.
        }
    }

    // ----------------- Função global -----------------
    void btReceiver() {
        if (SerialBT.available()) {
            String data = SerialBT.readStringUntil('\n');
            int sep = data.indexOf(',');
    
            if (sep > 0) {
                float setL = data.substring(0, sep).toFloat();
                float setR = data.substring(sep + 1).toFloat();
    
                // exemplo: medida simulada
                float medL = 0.5;
                float medR = 0.5;
    
               // updatePID(setL, setR, medL, medR, 0.01);
            }
        }
    }

} // namespace FlightC
