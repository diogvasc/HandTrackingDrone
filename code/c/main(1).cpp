#include <Arduino.h>
#include "FlightC.h"

int pwmPin = 2;  

FlightC::Controller flight;
FlightC::SepValues sepValues;

void setup() {
    Serial.begin(115200);
    pinMode(pwmPin, OUTPUT);

    FlightC::SerialBT.begin("DroneBT");
    Serial.println("Bluetooth iniciado!");
}

void loop() {

    sepValues = flight.btReceiver();

    Serial.print("Valor 1: ");
    Serial.print(sepValues.val1);
    Serial.print(" | Valor 2: ");
    Serial.println(sepValues.val2);

    delay(500);

}