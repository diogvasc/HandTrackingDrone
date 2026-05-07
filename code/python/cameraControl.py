# PII — Drone Feed + Hand Gesture Control # 7/05

import socket
import time
import threading
import queue
import cv2
import numpy as np
import mediapipe as mp
import serial

# ---------------------------
# DRONE CAMERA CONFIG
# ---------------------------
CAMERA_IP = "192.168.4.153"
PORT = 8080
SOI = b"\xff\xd8"
EOI = b"\xff\xd9"

# ===========================================================
# TUNABLE VALUES — adjust these for trial and error
# ===========================================================
MAX_BUFFER_SIZE = 600_000
MIN_FRAME_SIZE  = 15_000
OS_RECV_BUFFER  = 2 * 1024 * 1024
KEEPALIVE_INTERVAL = 0.02
QUEUE_MAXSIZE   = 1
CONFIRM_FRAMES  = 5

# ---------------------------
# BLUETOOTH CONFIG
# ---------------------------
BT_PORT = "COM7"   # porta de saída do DroneBT2
BT_BAUD = 9600
# ===========================================================

# ---------------------------
# SOCKET SETUP
# ---------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, OS_RECV_BUFFER)
sock.settimeout(0.2)

running = True
frame_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)

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
#   1 = só direita fechada
#   2 = só esquerda fechada
#   3 = só direita aberta
#   4 = só esquerda aberta
#   5 = ambos abertos         (OPEN + OPEN)
#   6 = esquerda aberta + direita fechada
#   7 = esquerda fechada + direita aberta
#   8 = ambos fechados        (FIST + FIST)
def resolve_flag(left, right):
    if left is None        and right == "FIST":        return 1
    if left == "FIST"      and right is None:          return 2
    if left is None        and right == "OPEN PALM":   return 3
    if left == "OPEN PALM" and right is None:          return 4
    if left == "OPEN PALM" and right == "OPEN PALM":   return 5
    if left == "OPEN PALM" and right == "FIST":        return 6
    if left == "FIST"      and right == "OPEN PALM":   return 7
    if left == "FIST"      and right == "FIST":        return 8
    return None

# ---------------------------
# KEEP STREAM ALIVE
# ---------------------------
def keepalive():
    while running:
        sock.sendto(b"Bv", (CAMERA_IP, PORT))
        time.sleep(KEEPALIVE_INTERVAL)

threading.Thread(target=keepalive, daemon=True).start()
print("Receiving video...")

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

# ---------------------------
# HAND STATE DETECTION
# ---------------------------
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
# STREAM RECEIVER THREAD
# ---------------------------
def receive_stream():
    buffer = bytearray()
    collecting = False

    while running:
        try:
            data, _ = sock.recvfrom(65535)
        except socket.timeout:
            continue

        tzh = data.find(b"TZH")
        if tzh == -1:
            continue
        payload = data[tzh + 4:]

        if not collecting:
            s = payload.find(SOI)
            if s != -1:
                buffer.clear()
                buffer += payload[s:]
                collecting = True
            continue

        new_soi = payload.find(SOI)
        if new_soi != -1:
            buffer.clear()
            buffer += payload[new_soi:]
        else:
            buffer += payload

        if len(buffer) > MAX_BUFFER_SIZE:
            buffer.clear()
            collecting = False
            continue

        e = buffer.rfind(EOI)
        if e == -1:
            continue

        jpg = bytes(buffer[:e + 2])
        collecting = False

        if len(jpg) < MIN_FRAME_SIZE:
            continue

        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        frame_queue.put(jpg)

threading.Thread(target=receive_stream, daemon=True).start()

# ---------------------------
# MAIN / DISPLAY LOOP
# ---------------------------
hand_states    = {"Left": None, "Right": None}
prev_states    = {"Left": None, "Right": None}  # por mão, evita prints repetidos
candidate_flag = None
flag_counter   = 0
confirmed_flag = None  # última flag estável confirmada

while True:
    try:
        jpg = frame_queue.get(timeout=1.0)
    except queue.Empty:
        if cv2.waitKey(1) == ord('q'):
            break
        continue

    arr   = np.frombuffer(jpg, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        continue

    # Uncomment to calibrate MIN_FRAME_SIZE:
    # print(f"Frame size: {len(jpg):,} bytes")

    frame = cv2.rotate(frame, cv2.ROTATE_180)

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = hands_model.process(image_rgb)
    image_rgb.flags.writeable = True

    # Reset cada frame para que mãos que saíram do ecrã não persistam
    hand_states = {"Left": None, "Right": None}

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label  # "Left" ou "Right"
            raw_label = "Left" if label == "Right" else "Right"  # corrige o flip da webcam
            label = raw_label
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

    # Debounce: acumula frames consecutivos com a mesma flag
    if flag == candidate_flag:
        flag_counter += 1
    else:
        candidate_flag = flag
        flag_counter = 1

    # Só confirma nova flag depois de CONFIRM_FRAMES consecutivos (anti-glitch)
    if flag_counter >= CONFIRM_FRAMES and flag is not None:
        confirmed_flag = flag

    # Envio contínuo da flag confirmada (todos os frames)
    if confirmed_flag is not None:
        send_flag(confirmed_flag)

    cv2.imshow("PII — Drone Feed", frame)
    if cv2.waitKey(1) == ord('q'):
        break

# ---------------------------
# CLEANUP
# ---------------------------
running = False
if bt and bt.is_open:
    bt.close()
sock.close()
cv2.destroyAllWindows()