"""
bt.py — Teste simples de Bluetooth para ESP32
----------------------------------------------
Envia valores para o ESP32 via Bluetooth Classic (SPP).

PRÉ-REQUISITOS:
    pip install pyserial

CONFIGURAÇÃO:
    1. Liga o ESP32 e faz o par no Bluetooth do PC (nome: "DroneBT2")
    2. Windows: vai a Definições → Bluetooth → Mais opções Bluetooth
               → separador "Portas COM" → anota a porta "de saída" (ex: COM6)
       Linux:   sudo rfcomm bind 0 <MAC_DO_ESP32>   → porta: /dev/rfcomm0
       Mac:     ls /dev/tty.* → procura "DroneBT2"
    3. Muda BT_PORT abaixo para a tua porta
"""

import serial
import time

# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────
BT_PORT = "COM11" #com 11 ou 7        # Muda para a tua porta (ex: "COM6", "/dev/rfcomm0")
BT_BAUD = 9600          # Baud rate — para BT SPP geralmente não importa,
                        # mas mantém consistente com o pyserial
# ─────────────────────────────────────────────────────────────────────────────


def send_value(bt: serial.Serial, val1: float, val2: float = 0.0):
    """
    Envia dois valores no formato que o btReceiver() do ESP32 espera:
        "val1,val2\n"
    """
    message = f"{val1},{val2}\n"
    bt.write(message.encode("utf-8"))
    print(f"  → Enviado: {message.strip()}")


def main():
    print("=" * 45)
    print("  Teste Bluetooth ESP32 — DroneBT2")
    print("=" * 45)
    print(f"  A tentar ligar em {BT_PORT}...\n")

    try:
        bt = serial.Serial(BT_PORT, BT_BAUD, timeout=1)
    except serial.SerialException as e:
        print(f"[ERRO] Não foi possível abrir {BT_PORT}: {e}")
        print("\nVerifica:")
        print("  - O ESP32 está ligado e o Bluetooth emparelhado?")
        print("  - A porta COM está correta? (ver Gestor de Dispositivos)")
        return

    time.sleep(1.5)  # Dá tempo à ligação BT para estabilizar
    print(f"[OK] Ligado em {BT_PORT}\n")
    print("Escreve um número e pressiona Enter para enviar.")
    print("Podes enviar dois valores separados por vírgula: ex.  3,7")
    print("Escreve 'q' para sair.\n")

    try:
        while True:
            user_input = input("Valor: ").strip()

            if user_input.lower() == "q":
                print("A encerrar...")
                break

            if not user_input:
                continue

            # Suporta "1" ou "1,2"
            parts = user_input.split(",")
            try:
                val1 = float(parts[0])
                val2 = float(parts[1]) if len(parts) > 1 else 0.0
                send_value(bt, val1, val2)
            except ValueError:
                print("  [!] Valor inválido — escreve um número (ex: 1 ou 1,2)")

    except KeyboardInterrupt:
        print("\nInterrompido pelo utilizador.")

    finally:
        if bt.is_open:
            bt.close()
            print("Porta fechada.")


if __name__ == "__main__":
    main()