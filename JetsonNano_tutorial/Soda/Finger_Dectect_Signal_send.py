import cv2
import mediapipe as mp
import requests
import time

# === Setup ===
vid = cv2.VideoCapture(0)
vid.set(3, 640)  # Width
vid.set(4, 480)  # Height

mphands = mp.solutions.hands
Hands = mphands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)
mpdraw = mp.solutions.drawing_utils

# Finger tip and dip landmark IDs
finger_tips = [4, 8, 12, 16, 20]
finger_dips = [3, 6, 10, 14, 18]

last_command = None  # To avoid repeating same command
prev_time = 0        # For FPS calculation

while True:
    success, frame = vid.read()
    if not success:
        print("❌ Failed to read from camera.")
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (480, 480))
    RGBframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = Hands.process(RGBframe)
    fingers_up = []

    if result.multi_hand_landmarks:
        print("👋 Hand detected!")
        for handLm in result.multi_hand_landmarks:
            mpdraw.draw_landmarks(frame, handLm, mphands.HAND_CONNECTIONS,
                                  mpdraw.DrawingSpec(color=(0, 0, 255), circle_radius=7, thickness=cv2.FILLED),
                                  mpdraw.DrawingSpec(color=(0, 255, 0), thickness=2))

            h, w, _ = frame.shape
            landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in handLm.landmark]

            # Thumb (X axis)
            fingers_up.append(1 if landmarks[finger_tips[0]][0] > landmarks[finger_dips[0]][0] else 0)

            # Other 4 fingers (Y axis)
            for i in range(1, 5):
                fingers_up.append(1 if landmarks[finger_tips[i]][1] < landmarks[finger_dips[i]][1] else 0)

            total_up = sum(fingers_up)
            cv2.putText(frame, f'Fingers Up: {total_up}', (10, 460), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2)

            # === Map gesture to command ===
            if total_up == 0:
                command = "stop"
            elif total_up == 1:
                command = "forward"
            elif total_up == 2:
                command = "backward"
            elif total_up == 3:
                command = "left"
            elif total_up == 4:
                command = "right"
            else:
                command = "stop"

            # === Send command if it changed ===
            if command != last_command:
                try:
                    print(f"📤 Sending command: {command}")
                    requests.post("http://192.168.25.109:5000/control", json={"cmd": command})
                    last_command = command
                except Exception as e:
                    print(f"⚠️ Failed to send command: {e}")

    else:
        print("🚫 No hand detected")

    # === FPS display ===
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time else 0
    prev_time = curr_time
    cv2.putText(frame, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2)

    # === Display window ===
    cv2.imshow("Hand Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

vid.release()
cv2.destroyAllWindows()
