# venv\Scripts\activate
import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_drawing_styles = mp.solutions.drawing_styles

holistic_model = mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# -------- detects state of hand --------
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

prev_right_state = None
prev_left_state = None


cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (800, 600))
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    image.flags.writeable = False
    results = holistic_model.process(image)
    image.flags.writeable = True

    # -------- detects hand state --------
    right_state = detect_hand_state(results.right_hand_landmarks)
    left_state = detect_hand_state(results.left_hand_landmarks)

    # RIGHT HAND
    if right_state != prev_right_state and right_state is not None:
        print("Right hand:", right_state)
        prev_right_state = right_state

    # LEFT HAND
    if left_state != prev_left_state and left_state is not None:
        print("Left hand:", left_state)
        prev_left_state = left_state

    # -------- draws landmarks (guidelines of hand) --------
    mp_drawing.draw_landmarks(
        image,
        results.right_hand_landmarks,
        mp_holistic.HAND_CONNECTIONS
    )

    mp_drawing.draw_landmarks(
        image,
        results.left_hand_landmarks,
        mp_holistic.HAND_CONNECTIONS
    )

    cv2.imshow('main', image)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
