# 25/03
#venv\Scripts\activate


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
# If frames are still corrupted: raise (e.g. 600_000, 800_000)
# If you see stale/delayed frames: lower (e.g. 300_000)

MIN_FRAME_SIZE = 15_000
# If you still see corrupt/rough frames: raise (e.g. 20_000, 30_000)
# If valid frames are being silently dropped (frozen feed): lower (e.g. 8_000, 5_000)
# Tip: uncomment the print() line in the display loop to measure your real frame sizes

OS_RECV_BUFFER = 2 * 1024 * 1024
# OS-level UDP socket buffer. Safe range: 1MB to 4MB

KEEPALIVE_INTERVAL = 0.02
# If stream cuts out intermittently: lower (e.g. 0.015)
# If the drone seems overloaded/stuttering: raise (e.g. 0.03)

QUEUE_MAXSIZE = 1
# 1 = lowest latency | 2-3 = smoother but adds latency

# ---------------------------
# BLUETOOTH CONFIG
# ---------------------------
BT_PORT = "COM3"    # Change to your Bluetooth COM port
BT_BAUD = 9600      # Change if your device uses a different baud rate
# ===========================================================

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
    print(f"Bluetooth connected on {BT_PORT}")
except Exception as e:
    print(f"Bluetooth not available ({e}) — running without it")

def send_flag(flag: int):
    """Send a single flag byte over Bluetooth. Silently skips if not connected."""
    if bt and bt.is_open:
        try:
            bt.write(bytes([flag]))
        except Exception as e:
            print(f"Bluetooth send error: {e}")

# Flag mapping:
#   0 = Both fist
#   1 = Left fist only
#   2 = Right fist only
#   3 = Left open only
#   4 = Right open only
#   5 = Both open
def resolve_flag(left, right):
    if left == "FIST"      and right == "FIST":       return 0
    if left == "FIST"      and right is None:          return 1
    if left is None        and right == "FIST":        return 2
    if left == "OPEN PALM" and right is None:          return 3
    if left is None        and right == "OPEN PALM":   return 4
    if left == "OPEN PALM" and right == "OPEN PALM":   return 5
    return None  # mixed/undefined state — don't send

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

        # Always restart buffer from new SOI if one appears mid-collection
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
prev_state = None
hand_states = {"Left": None, "Right": None}
prev_flag = None

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

    # Uncomment to calibrate MIN_FRAME_SIZE — shows size of every decoded frame:
    # print(f"Frame size: {len(jpg):,} bytes")

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = hands_model.process(image_rgb)
    image_rgb.flags.writeable = True

    # Reset each frame so vanished hands don't linger
    hand_states = {"Left": None, "Right": None}

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label  # "Left" or "Right"
            state = detect_hand_state(hand_landmarks)
            hand_states[label] = state
            if state != prev_state and state is not None:
                print("Detected:", state)
                prev_state = state
            # draw landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # Resolve and send flag only when it changes
    flag = resolve_flag(hand_states["Left"], hand_states["Right"])
    if flag is not None and flag != prev_flag:
        print(f"Sending flag: {flag}")
        send_flag(flag)
        prev_flag = flag

    frame = cv2.rotate(frame, cv2.ROTATE_180)
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