## working as 03/03 - detects hands and corresponding state. connects to drone

import socket
import time
import threading
import cv2
import numpy as np
import mediapipe as mp

# ---------------------------
# DRONE CAMERA CONFIG
# ---------------------------
CAMERA_IP = "192.168.4.153"
PORT = 8080

SOI = b"\xff\xd8"
EOI = b"\xff\xd9"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(0.2)

running = True

# ---------------------------
# KEEP STREAM ALIVE
# ---------------------------
def keepalive():
    while running:
        sock.sendto(b"Bv", (CAMERA_IP, PORT))
        time.sleep(0.025)

threading.Thread(target=keepalive, daemon=True).start()

print("receiving video")

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
    pip_ids = [6, 10, 14, 18]

    fingers_closed = 0
    fingers_open = 0

    for tip, pip in zip(tips_ids, pip_ids):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            fingers_closed += 1
        else:
            fingers_open += 1

    if fingers_closed >= 3:
        return "FIST"
    elif fingers_open >= 3:
        return "OPEN PALM"
    else:
        return None


prev_state = None
buffer = bytearray()
collecting = False

# ---------------------------
# MAIN LOOP
# ---------------------------
while True:
    try:
        data, _ = sock.recvfrom(65535)
    except socket.timeout:
        continue

    tzh = data.find(b"TZH")
    if tzh == -1:
        continue

    payload = data[tzh + 4:]

    # ---- detect frame start ----
    if not collecting:
        s = payload.find(SOI)
        if s != -1:
            buffer.clear()
            buffer += payload[s:]
            collecting = True
        continue

    buffer += payload

    # ---- detect frame end ----
    e = buffer.find(EOI)
    if e == -1:
        continue

    jpg = buffer[:e+2]
    collecting = False

    # ---- decode frame ----
    arr = np.frombuffer(jpg, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if frame is None:
        continue

    # ---------------------------
    # HAND DETECTION ON DRONE FRAME
    # ---------------------------
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = hands_model.process(image_rgb)
    image_rgb.flags.writeable = True

    # detect gesture
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            state = detect_hand_state(hand_landmarks)

            if state != prev_state and state is not None:
                print("Detected:", state)
                prev_state = state

            # draw landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("PII", frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

running = False
sock.close()
cv2.destroyAllWindows()
