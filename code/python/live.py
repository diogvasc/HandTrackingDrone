#!/usr/bin/env python3

import socket
import time
import threading
import cv2
import numpy as np

CAMERA_IP = "192.168.4.153"
PORT = 8080

SOI = b"\xff\xd8"
EOI = b"\xff\xd9"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(0.2)

running = True


# ---------------------------
# keep stream alive
# ---------------------------
def keepalive():
    while running:
        sock.sendto(b"Bv", (CAMERA_IP, PORT))
        time.sleep(0.025)


threading.Thread(target=keepalive, daemon=True).start()

print("Receiving live video...")

buffer = bytearray()
collecting = False

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
        continue  # corrupted frame

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == 27:
        break


running = False
sock.close()
cv2.destroyAllWindows()
