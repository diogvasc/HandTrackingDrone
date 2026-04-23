#include <Arduino.h>
#include "FlightC.h"
#include <BluetoothSerial.h>

int dacPin = 25;  

BluetoothSerial FlightC::SerialBT;

FlightC::Controller flight;
FlightC::SepValues sepValues;

int iteration = 0; // Variável para contar as iterações

void setup() {
    Serial.begin(115200);
    pinMode(dacPin, OUTPUT);

    FlightC::SerialBT.begin("DroneBT");
    Serial.println("Bluetooth iniciado!");

}

void loop() {
    FlightC::SepValues received = flight.btReceiver();

    if (received.val1 != 0 || received.val2 != 0) {
        flight.setTarget(received);
        Serial.print("Target: ");
        Serial.println(received.val1);
    }

    flight.prog(dacPin);  // sobe/desce 1 passo por iteração
    delay(10);            // loop rápido, sem delay grande
}
