#include <Arduino.h>
#include "FlightC.h"

int pwmPin = 2;  

FlightC::Controller flight;

void setup() {
    Serial.begin(115200);
    pinMode(pwmPin, OUTPUT);

    FlightC::SerialBT.begin("DroneBT");
    Serial.println("Bluetooth iniciado! Conecta do PC ou celular.");
}



void loop() {
 

}
