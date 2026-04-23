# Offline Bluetooth test — uses webcam instead of drone

import cv2
import numpy as np
import mediapipe as mp
import serial
import time

# ---------------------------
# BLUETOOTH CONFIG
# ---------------------------
BT_PORT = "COM11"   # porta de saída do DroneBT2
BT_BAUD = 9600

# ---------------------------
# BLUETOOTH SETUP
# ---------------------------
bt = None
try:
    bt = serial.Serial(BT_PORT, BT_BAUD, timeout=1)
    time.sleep(1.5)
    print(f"Bluetooth connected on {BT_PORT}")
except serial.SerialException as e:
    print(f"Bluetooth not available ({e}) — running without it")

def send_flag(flag: int):
    """Envia flag no formato que o btReceiver() do ESP32 espera: 'val1,val2\n'"""
    if bt and bt.is_open:
        try:
            message = f"{flag},0\n"
            bt.write(message.encode("utf-8"))
            print(f"  → Enviado: {message.strip()}")
        except Exception as e:
            print(f"Bluetooth send error: {e}")

# Flag mapping:
#   0 = ambos fechados        (FIST + FIST)
#   1 = só esquerda fechada
#   2 = só direita fechada
#   3 = só esquerda aberta
#   4 = só direita aberta
#   5 = ambos abertos         (OPEN + OPEN)
#   6 = esquerda fechada + direita aberta
#   7 = esquerda aberta  + direita fechada
def resolve_flag(left, right):
    if left == "FIST"      and right == "FIST":       return 0
    if left == "FIST"      and right is None:          return 1
    if left is None        and right == "FIST":        return 2
    if left == "OPEN PALM" and right is None:          return 3
    if left is None        and right == "OPEN PALM":   return 4
    if left == "OPEN PALM" and right == "OPEN PALM":   return 5
    if left == "FIST"      and right == "OPEN PALM":   return 6
    if left == "OPEN PALM" and right == "FIST":        return 7
    return None

# ---------------------------
# MEDIAPIPE SETUP
# ---------------------------
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands_model = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def detect_hand_state(hand_landmarks):
    if hand_landmarks is None:
        return None
    tips_ids = [8, 12, 16, 20]
    pip_ids  = [6, 10, 14, 18]
    fingers_closed = 0
    fingers_open   = 0
    for tip, pip in zip(tips_ids, pip_ids):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            fingers_closed += 1
        else:
            fingers_open += 1
    if fingers_closed >= 3:
        return "FIST"
    elif fingers_open >= 3:
        return "OPEN PALM"
    return None

# ---------------------------
# WEBCAM LOOP
# ---------------------------
cap = cv2.VideoCapture(0)

hand_states = {"Left": None, "Right": None}
prev_states = {"Left": None, "Right": None}  # por mão, evita prints repetidos
prev_flag = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Webcam read failed")
        break

    # Espelha o frame — o que aparece à esquerda no ecrã é a mão esquerda
    frame = cv2.flip(frame, 1)

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = hands_model.process(image_rgb)
    image_rgb.flags.writeable = True

    hand_states = {"Left": None, "Right": None}

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Após flip, os labels do MediaPipe ficam invertidos — corrigimos aqui
            raw_label = handedness.classification[0].label
            label = "Right" if raw_label == "Left" else "Left"

            state = detect_hand_state(hand_landmarks)
            hand_states[label] = state

            # Só imprime se o estado desta mão mudou
            if state != prev_states[label] and state is not None:
                print(f"Detected: {label} {state}")
                prev_states[label] = state

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # Limpa prev_state de mãos que saíram do ecrã
    for hand in ["Left", "Right"]:
        if hand_states[hand] is None:
            prev_states[hand] = None

    flag = resolve_flag(hand_states["Left"], hand_states["Right"])
    if flag is not None and flag != prev_flag:
        print(f"Sending flag: {flag}")
        send_flag(flag)
        prev_flag = flag

    cv2.imshow("BT Test — Webcam", frame)
    if cv2.waitKey(1) == ord('q'):
        break

# ---------------------------
# CLEANUP
# ---------------------------
cap.release()
if bt and bt.is_open:
    bt.close()
cv2.destroyAllWindows()