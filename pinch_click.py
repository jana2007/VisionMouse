
import cv2
import mediapipe as mp
import pyautogui
import math

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

# Cursor smoothing
smoothening = 5
prev_x, prev_y = 0, 0

# Pinch detection
pinching = False

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

            landmarks = hand_landmarks.landmark

            # Get thumb and index finger tips
            thumb = landmarks[4]
            index = landmarks[8]

            # Convert coordinates to pixels
            thumb_x = int(thumb.x * frame_width)
            thumb_y = int(thumb.y * frame_height)

            index_x = int(index.x * frame_width)
            index_y = int(index.y * frame_height)

            # Calculate distance between fingertips
            distance = math.hypot(
                index_x - thumb_x,
                index_y - thumb_y
            )

            # Move cursor using index finger
            screen_x = int(index.x * screen_width)
            screen_y = int(index.y * screen_height)

            curr_x = prev_x + (screen_x - prev_x) / smoothening
            curr_y = prev_y + (screen_y - prev_y) / smoothening

            pyautogui.moveTo(int(curr_x), int(curr_y))

            prev_x = curr_x
            prev_y = curr_y

            # Pinch thresholds
            pinch_threshold = frame_width * 0.045
            release_threshold = frame_width * 0.065

            # Detect pinch and click only once
            if distance < pinch_threshold and not pinching:

                pyautogui.click()
                pinching = True

            elif distance > release_threshold:

                pinching = False

            # Display pinch status
            if pinching:
                status = "CLICK!"
                color = (0, 0, 255)
            else:
                status = "READY"
                color = (0, 255, 0)

            cv2.putText(
                frame,
                status,
                (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                color,
                3
            )

            # Draw fingertip circles
            cv2.circle(
                frame,
                (thumb_x, thumb_y),
                10,
                (255, 0, 0),
                cv2.FILLED
            )

            cv2.circle(
                frame,
                (index_x, index_y),
                10,
                (0, 255, 0),
                cv2.FILLED
            )

            # Draw line between fingertips
            cv2.line(
                frame,
                (thumb_x, thumb_y),
                (index_x, index_y),
                color,
                3
            )

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    else:
        pinching = False

    cv2.imshow("VisionMouse - Pinch to Click", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
