#include <Arduino.h>

void executeVoiceCommand(uint8_t id);

// Definição de pinos para o ESP32 (UART2)
#define RXD2 18
#define TXD2 19

void setup() {
  // Monitor Série para veres no PC
  Serial.begin(115200); 
  while(Serial.available()) Serial.read(); // Limpa qualquer lixo que tenha entrado no buffer
  
  // Porta Serial 1 para o Microfone (Pinos 18 e 19 no Mega)
  //Serial1.begin(115200); 
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
  
  Serial.println("--- Teste de Voz (Arduino Mega) ---");
  Serial.println("Diz 'Hicell' para comecar.");
}

void loop() {
  // Verifica se o microfone enviou algum dado pela Serial 1
  if (Serial2.available()) {
    uint8_t commandID = Serial2.read();
    
    Serial.print("Comando Detetado - ID: ");
    Serial.println(commandID);
    executeVoiceCommand(commandID);
  }
}

void executeVoiceCommand(uint8_t id) {
  switch (id) {

    case 7:  Serial.println("Comando: Up (Subir)"); break;
    case 8:  Serial.println("Comando: Down (Descer)"); break;   
    case 16: Serial.println("Comando: Left (Rodar Esquerda)"); break;
    case 17: Serial.println("Comando: Right (Rodar Direita)"); break;
    case 18: Serial.println("Comando: STOP (Parar)"); break;
    case 19: Serial.println("Comando: Start (Comecar)"); break;
    case 20: Serial.println("Comando: One (Um)"); break;
    case 21: Serial.println("Comando: Two (Dois)"); break;
    case 22: Serial.println("Comando: Go (Ir)"); break;
    
    default: 
      Serial.print("ID desconhecido recebido: "); 
      Serial.println(id); 
      break;
  }
}
