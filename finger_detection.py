
import cv2
import mediapipe as mp

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Open webcam
cap = cv2.VideoCapture(0)

# Finger tip and lower joint positions
finger_tips = [8, 12, 16, 20]
finger_pips = [6, 10, 14, 18]

while True:

    success, frame = cap.read()

    if not success:
        print("Camera not available")
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            landmarks = hand_landmarks.landmark

            # Check which fingers are raised
            fingers = []

            for tip, pip in zip(finger_tips, finger_pips):

                if landmarks[tip].y < landmarks[pip].y:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # Check thumb separately
            if landmarks[4].x < landmarks[3].x:
                fingers.insert(0, 1)
            else:
                fingers.insert(0, 0)

            # Count raised fingers
            count = fingers.count(1)

            # Display finger count
            cv2.putText(
                frame,
                f"Fingers: {count}",
                (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 255, 0),
                3
            )

            # Draw landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("VisionMouse - Finger Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
