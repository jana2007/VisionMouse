
import cv2
import mediapipe as mp
import pyautogui
import math
import time

pyautogui.PAUSE = 0

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Screen dimensions
screen_width, screen_height = pyautogui.size()

# Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Cursor smoothing
smoothening = 5
prev_x, prev_y = 0, 0

# Click states
left_pinching = False
right_pinching = False

# Scroll settings
middle_pinch_active = False
scroll_mode = False
scroll_start_time = None
previous_wrist_y = None
scroll_accumulator = 0

scroll_hold_time = 0.2
scroll_threshold = 6
scroll_speed = 2

# Main loop
while True:

    success, frame = cap.read()

    if not success:
        print("Camera not available")
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    status = "SHOW YOUR HAND"
    color = (0, 255, 255)

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            lm = hand_landmarks.landmark

            # Finger coordinates
            thumb = lm[4]
            index = lm[8]
            middle = lm[12]
            ring = lm[16]
            wrist = lm[0]

            tx, ty = int(thumb.x * width), int(thumb.y * height)
            ix, iy = int(index.x * width), int(index.y * height)
            mx, my = int(middle.x * width), int(middle.y * height)
            rx, ry = int(ring.x * width), int(ring.y * height)

            # Calculate pinch distances
            left_dist = math.hypot(ix - tx, iy - ty)
            scroll_dist = math.hypot(mx - tx, my - ty)
            right_dist = math.hypot(rx - tx, ry - ty)

            # Detect middle finger pinch with release tolerance
            if not middle_pinch_active and scroll_dist < 35:
                middle_pinch_active = True
                scroll_start_time = time.time()
                scroll_mode = False
                previous_wrist_y = None
                scroll_accumulator = 0

            elif middle_pinch_active and scroll_dist > 50:
                middle_pinch_active = False
                scroll_mode = False
                scroll_start_time = None
                previous_wrist_y = None
                scroll_accumulator = 0

            # Activate scrolling after holding the pinch
            if middle_pinch_active:

                status = "HOLD TO SCROLL"
                color = (255, 255, 0)

                if time.time() - scroll_start_time >= scroll_hold_time:
                    scroll_mode = True

                if scroll_mode:

                    status = "SCROLL MODE"
                    color = (0, 255, 0)

                    wrist_y = int(wrist.y * height)

                    if previous_wrist_y is not None:

                        movement = previous_wrist_y - wrist_y
                        scroll_accumulator += movement

                        while scroll_accumulator >= scroll_threshold:
                            pyautogui.scroll(scroll_speed)
                            scroll_accumulator -= scroll_threshold

                        while scroll_accumulator <= -scroll_threshold:
                            pyautogui.scroll(-scroll_speed)
                            scroll_accumulator += scroll_threshold

                    previous_wrist_y = wrist_y

            else:

                # Cursor movement
                index_up = lm[8].y < lm[6].y

                if index_up:

                    sx = int(index.x * screen_width)
                    sy = int(index.y * screen_height)

                    curr_x = prev_x + (sx - prev_x) / smoothening
                    curr_y = prev_y + (sy - prev_y) / smoothening

                    pyautogui.moveTo(int(curr_x), int(curr_y))

                    prev_x, prev_y = curr_x, curr_y

                    status = "MOVE CURSOR"
                    color = (0, 255, 0)

                # Left-click: thumb + index
                if left_dist < 35 and not left_pinching:
                    pyautogui.click()
                    left_pinching = True
                    status = "LEFT CLICK"
                    color = (0, 0, 255)

                elif left_dist > 50:
                    left_pinching = False

                # Right-click: thumb + ring
                if right_dist < 35 and not right_pinching:
                    pyautogui.rightClick()
                    right_pinching = True
                    status = "RIGHT CLICK"
                    color = (255, 0, 255)

                elif right_dist > 50:
                    right_pinching = False

            # Draw hand landmarks
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Draw fingertip markers
            cv2.circle(frame, (tx, ty), 8, (255, 0, 0), -1)
            cv2.circle(frame, (ix, iy), 8, (0, 255, 0), -1)
            cv2.circle(frame, (mx, my), 8, (0, 0, 255), -1)
            cv2.circle(frame, (rx, ry), 8, (255, 0, 255), -1)

    else:
        left_pinching = False
        right_pinching = False
        middle_pinch_active = False
        scroll_mode = False
        scroll_start_time = None
        previous_wrist_y = None
        scroll_accumulator = 0

    # Display status
    cv2.putText(
        frame,
        status,
        (30, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        3
    )

    cv2.imshow("VisionMouse - Advanced Controls", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
