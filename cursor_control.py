
import cv2
import mediapipe as mp
import pyautogui

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Open webcam
cap = cv2.VideoCapture(0)

# Smooth cursor movement
smoothening = 5
prev_x, prev_y = 0, 0

while True:

    success, frame = cap.read()

    if not success:
        print("Camera not available")
        break

    frame = cv2.flip(frame, 1)

    frame_height, frame_width, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            # Get index finger tip
            index_finger = hand_landmarks.landmark[8]

            x = int(index_finger.x * frame_width)
            y = int(index_finger.y * frame_height)

            # Convert camera coordinates to screen coordinates
            screen_x = int(index_finger.x * screen_width)
            screen_y = int(index_finger.y * screen_height)

            # Smooth movement
            curr_x = prev_x + (screen_x - prev_x) / smoothening
            curr_y = prev_y + (screen_y - prev_y) / smoothening

            # Move mouse cursor
            pyautogui.moveTo(int(curr_x), int(curr_y))

            prev_x = curr_x
            prev_y = curr_y

            # Draw circle on index fingertip
            cv2.circle(
                frame,
                (x, y),
                12,
                (0, 255, 0),
                cv2.FILLED
            )

            # Draw hand landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.imshow("VisionMouse - Cursor Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
