#include <Arduino.h>
#include "FlightC.h"
#include <BluetoothSerial.h>

int pwmPin = 2;  

BluetoothSerial SerialBT;

FlightC::Controller flight;
FlightC::SepValues sepValues;
int iteration = 0; // Variável para contar as iterações

void setup() {
    Serial.begin(115200);
    pinMode(pwmPin, OUTPUT);

    SerialBT.begin("DroneBT2");
    Serial.println("Bluetooth iniciado!");

}

void loop() {
    iteration++; // Incrementa a iteração

    sepValues = flight.btReceiver();

    // Imprime o número da iteração e os valores recebidos
    Serial.print("Iteração ");
    Serial.print(iteration);
    Serial.print(" - Valor 1: ");
    Serial.print(sepValues.val1);
    Serial.print(" | Valor 2: ");
    Serial.println(sepValues.val2);

    delay(500);
}