
import customtkinter as ctk
import cv2
import mediapipe as mp
import pyautogui
import math
import time
from PIL import Image

# ==========================================
# APPEARANCE AND COLORS
# ==========================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG = "#0B0B12"
CARD = "#171722"
PURPLE = "#8B5CF6"
LIGHT_PURPLE = "#A78BFA"
WHITE = "#FFFFFF"
MUTED = "#9292A8"
GREEN = "#22C55E"
RED = "#EF4444"

pyautogui.PAUSE = 0

# ==========================================
# MAIN WINDOW
# ==========================================

app = ctk.CTk()
app.title("VisionMouse | AI Hand Control")
app.geometry("1250x820")
app.minsize(1050, 700)
app.configure(fg_color=BG)

# ==========================================
# CAMERA VARIABLES
# ==========================================

cap = None
hands = None
camera_running = False
camera_image = None

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()

# Cursor settings
smoothening = 5
prev_x, prev_y = 0, 0

# Click states
left_pinching = False
right_pinching = False
left_pinch_frames = 0

# Left-click detection settings
left_click_threshold = 45
left_release_threshold = 60
left_click_confirm_frames = 2

# Scroll settings
middle_pinch_active = False
scroll_mode = False
scroll_start_time = None
previous_wrist_y = None
scroll_accumulator = 0

scroll_hold_time = 0.15
scroll_threshold = 2
scroll_speed = 8

# FPS settings
fps_start_time = time.time()
fps_frame_count = 0
current_fps = 0


# ==========================================
# CAMERA START
# ==========================================

def start_camera():

    global cap, hands, camera_running
    global prev_x, prev_y
    global left_pinching, right_pinching, left_pinch_frames
    global middle_pinch_active, scroll_mode
    global scroll_start_time, previous_wrist_y
    global scroll_accumulator
    global fps_start_time, fps_frame_count, current_fps

    if camera_running:
        return

    try:

        cap = cv2.VideoCapture(0)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():

            cap.release()
            cap = None

            status_label.configure(
                text="● Could not access webcam",
                text_color=RED
            )

            return

        hands = mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        # Reset gesture states
        prev_x, prev_y = 0, 0

        left_pinching = False
        right_pinching = False
        left_pinch_frames = 0

        middle_pinch_active = False
        scroll_mode = False
        scroll_start_time = None
        previous_wrist_y = None
        scroll_accumulator = 0

        # Reset FPS
        fps_start_time = time.time()
        fps_frame_count = 0
        current_fps = 0

        camera_running = True

        status_label.configure(
            text="● CAMERA CONNECTED",
            text_color=GREEN
        )

        gesture_status_label.configure(
            text="SHOW YOUR HAND",
            text_color=LIGHT_PURPLE
        )

        camera_button.configure(
            text="CAMERA RUNNING",
            state="disabled"
        )

        fps_label.configure(
            text="FPS: Calculating..."
        )

        camera_preview.configure(
            text="Starting camera...",
            image=None
        )

        update_camera_frame()

    except Exception as error:

        stop_camera()

        status_label.configure(
            text=f"● Camera error: {error}",
            text_color=RED
        )


# ==========================================
# CAMERA PROCESSING
# ==========================================

def update_camera_frame():

    global camera_image
    global left_pinching, right_pinching, left_pinch_frames
    global middle_pinch_active, scroll_mode
    global scroll_start_time, previous_wrist_y
    global scroll_accumulator
    global prev_x, prev_y
    global fps_start_time, fps_frame_count, current_fps

    if not camera_running:
        return

    success, frame = cap.read()

    if not success:

        stop_camera()

        status_label.configure(
            text="● CAMERA FEED LOST",
            text_color=RED
        )

        return

    # Mirror camera
    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    status = "SHOW YOUR HAND"
    color = (0, 255, 255)

    # ======================================
    # HAND DETECTION
    # ======================================

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            lm = hand_landmarks.landmark

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

            # ======================================
            # SCROLL GESTURE
            # ======================================

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

                # ======================================
                # LEFT CLICK
                # ======================================

                # Require the pinch to be detected for consecutive
                # frames so small landmark movements do not cause flicker.
                if left_dist < left_click_threshold:

                    left_pinch_frames += 1

                else:

                    left_pinch_frames = 0

                if (
                    left_pinch_frames >= left_click_confirm_frames
                    and not left_pinching
                ):

                    # Click at the current cursor position only once.
                    pyautogui.click(button="left")
                    left_pinching = True

                    status = "LEFT CLICK"
                    color = (0, 0, 255)

                elif left_pinching and left_dist > left_release_threshold:

                    left_pinching = False
                    left_pinch_frames = 0

                if left_pinching:

                    status = "LEFT CLICK"
                    color = (0, 0, 255)

                # ======================================
                # CURSOR MOVEMENT
                # ======================================

                index_up = lm[8].y < lm[6].y

                # Keep the cursor steady while the thumb-index pinch
                # is held, so the click lands on the intended target.
                if index_up and not left_pinching:

                    sx = int(index.x * screen_width)
                    sy = int(index.y * screen_height)

                    curr_x = prev_x + (sx - prev_x) / smoothening
                    curr_y = prev_y + (sy - prev_y) / smoothening

                    pyautogui.moveTo(
                        int(curr_x),
                        int(curr_y)
                    )

                    prev_x, prev_y = curr_x, curr_y

                    status = "MOVE CURSOR"
                    color = (0, 255, 0)

                # ======================================
                # RIGHT CLICK
                # ======================================

                if right_dist < 35 and not right_pinching:

                    pyautogui.rightClick()

                    right_pinching = True

                    status = "RIGHT CLICK"
                    color = (255, 0, 255)

                elif right_dist > 50:

                    right_pinching = False

            # ======================================
            # DRAW LANDMARKS - GREEN STYLE
            # ======================================

            green_dots = mp_draw.DrawingSpec(
                color=(0, 255, 0),
                thickness=2,
                circle_radius=4
            )

            green_connections = mp_draw.DrawingSpec(
                color=(0, 255, 0),
                thickness=2
            )

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec=green_dots,
                connection_drawing_spec=green_connections
            )

            # All fingertip dots are green
            cv2.circle(frame, (tx, ty), 8, (0, 255, 0), -1)
            cv2.circle(frame, (ix, iy), 8, (0, 255, 0), -1)
            cv2.circle(frame, (mx, my), 8, (0, 255, 0), -1)
            cv2.circle(frame, (rx, ry), 8, (0, 255, 0), -1)

    else:

        left_pinching = False
        right_pinching = False
        left_pinch_frames = 0

        middle_pinch_active = False
        scroll_mode = False
        scroll_start_time = None
        previous_wrist_y = None
        scroll_accumulator = 0

    # ======================================
    # FPS CALCULATION
    # ======================================

    fps_frame_count += 1

    elapsed = time.time() - fps_start_time

    if elapsed >= 1:

        current_fps = fps_frame_count / elapsed

        fps_frame_count = 0
        fps_start_time = time.time()

        fps_label.configure(
            text=f"FPS: {current_fps:.1f}"
        )

    # ======================================
    # CAMERA STATUS TEXT
    # ======================================

    cv2.putText(
        frame,
        status,
        (30, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2
    )

    # Update dashboard gesture status
    gesture_status_label.configure(
        text=status,
        text_color=(
            GREEN if status in ["MOVE CURSOR", "SCROLL MODE"]
            else LIGHT_PURPLE
        )
    )

    # ======================================
    # DISPLAY CAMERA IN DASHBOARD
    # ======================================

    frame_rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    image = Image.fromarray(frame_rgb)

    display_image = ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=(560, 420)
    )

    camera_image = display_image

    camera_preview.configure(
        image=camera_image,
        text=""
    )

    # Schedule next frame
    app.after(10, update_camera_frame)


# ==========================================
# STOP CAMERA
# ==========================================

def stop_camera():

    global cap, hands, camera_running
    global camera_image

    camera_running = False

    if cap is not None:

        cap.release()
        cap = None

    if hands is not None:

        hands.close()
        hands = None

    camera_image = None

    camera_preview.configure(
        image=None,
        text="CAMERA OFF\n\nClick START CAMERA to begin."
    )

    gesture_status_label.configure(
        text="WAITING FOR CAMERA",
        text_color=MUTED
    )

    status_label.configure(
        text="● CAMERA IS OFF",
        text_color=MUTED
    )

    fps_label.configure(
        text="FPS: --"
    )

    camera_button.configure(
        text="START CAMERA",
        state="normal"
    )


# ==========================================
# CLOSE APPLICATION
# ==========================================

def close_application():

    stop_camera()
    app.destroy()


# ==========================================
# SCREEN SWITCHING
# ==========================================

def show_dashboard():

    welcome_frame.pack_forget()

    dashboard_frame.pack(
        fill="both",
        expand=True
    )


def show_welcome():

    stop_camera()

    dashboard_frame.pack_forget()

    welcome_frame.pack(
        fill="both",
        expand=True
    )


# ==========================================
# WELCOME SCREEN
# ==========================================

welcome_frame = ctk.CTkFrame(
    app,
    fg_color=BG
)

top = ctk.CTkFrame(
    welcome_frame,
    fg_color="transparent"
)

top.pack(
    fill="x",
    padx=35,
    pady=30
)

ctk.CTkLabel(
    top,
    text="◈  VISIONMOUSE",
    font=("Segoe UI", 25, "bold"),
    text_color=LIGHT_PURPLE
).pack(side="left")

ctk.CTkLabel(
    top,
    text="AI HAND CONTROL SYSTEM  •  V1.0",
    font=("Segoe UI", 11),
    text_color=MUTED
).pack(side="right")

ctk.CTkLabel(
    welcome_frame,
    text="Control your world.",
    font=("Segoe UI", 46, "bold"),
    text_color=WHITE
).pack(pady=(100, 12))

ctk.CTkLabel(
    welcome_frame,
    text="A smarter way to interact with your computer using hand gestures.",
    font=("Segoe UI", 16),
    text_color=MUTED
).pack(pady=(0, 35))

welcome_card = ctk.CTkFrame(
    welcome_frame,
    fg_color=CARD,
    corner_radius=20,
    width=600,
    height=170
)

welcome_card.pack(pady=10)
welcome_card.pack_propagate(False)

ctk.CTkLabel(
    welcome_card,
    text="✦  INTELLIGENT GESTURE RECOGNITION",
    font=("Segoe UI", 16, "bold"),
    text_color=LIGHT_PURPLE
).pack(pady=(30, 12))

ctk.CTkLabel(
    welcome_card,
    text="Move your cursor, click and scroll\nwithout touching your mouse.",
    font=("Segoe UI", 15),
    text_color=WHITE,
    justify="center"
).pack()

ctk.CTkButton(
    welcome_frame,
    text="GET STARTED   →",
    font=("Segoe UI", 15, "bold"),
    fg_color=PURPLE,
    hover_color="#7040D0",
    width=230,
    height=52,
    corner_radius=12,
    command=show_dashboard
).pack(pady=35)

ctk.CTkLabel(
    welcome_frame,
    text="POWERED BY PYTHON  •  OPENCV  •  MEDIAPIPE",
    font=("Segoe UI", 10),
    text_color="#626276"
).pack(side="bottom", pady=20)


# ==========================================
# MAIN DASHBOARD
# ==========================================

dashboard_frame = ctk.CTkFrame(
    app,
    fg_color=BG
)

# ==========================================
# SIDEBAR
# ==========================================

sidebar = ctk.CTkFrame(
    dashboard_frame,
    fg_color="#11111B",
    width=210,
    corner_radius=0
)

sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar,
    text="◈  VISIONMOUSE",
    font=("Segoe UI", 20, "bold"),
    text_color=LIGHT_PURPLE
).pack(padx=18, pady=(30, 45))

ctk.CTkLabel(
    sidebar,
    text="WORKSPACE",
    font=("Segoe UI", 10, "bold"),
    text_color=MUTED
).pack(anchor="w", padx=22, pady=(0, 15))

ctk.CTkLabel(
    sidebar,
    text="▣   Dashboard",
    font=("Segoe UI", 14, "bold"),
    text_color=WHITE,
    fg_color="#29213E",
    corner_radius=8,
    anchor="w",
    height=42
).pack(fill="x", padx=12, pady=4)

ctk.CTkLabel(
    sidebar,
    text="GESTURE CONTROLS",
    font=("Segoe UI", 10, "bold"),
    text_color=MUTED
).pack(anchor="w", padx=22, pady=(35, 15))

for item in [
    "✋  Cursor Movement",
    "👆  Left Click",
    "🤏  Right Click",
    "↕   Scrolling"
]:

    ctk.CTkLabel(
        sidebar,
        text=item,
        font=("Segoe UI", 13),
        text_color=MUTED,
        anchor="w",
        height=35
    ).pack(fill="x", padx=20)

ctk.CTkButton(
    sidebar,
    text="ABOUT PROJECT",
    fg_color="transparent",
    hover_color="#29213E",
    text_color=MUTED,
    command=lambda: show_about()
).pack(side="bottom", fill="x", padx=15, pady=(5, 5))

ctk.CTkButton(
    sidebar,
    text="← BACK TO HOME",
    fg_color="transparent",
    hover_color="#29213E",
    text_color=MUTED,
    command=show_welcome
).pack(side="bottom", fill="x", padx=15, pady=(5, 15))


# ==========================================
# DASHBOARD CONTENT
# ==========================================

content = ctk.CTkFrame(
    dashboard_frame,
    fg_color=BG
)

content.pack(
    side="left",
    fill="both",
    expand=True,
    padx=25,
    pady=22
)

ctk.CTkLabel(
    content,
    text="Dashboard",
    font=("Segoe UI", 30, "bold"),
    text_color=WHITE
).pack(anchor="w")

ctk.CTkLabel(
    content,
    text="Manage your AI-powered hand controls.",
    font=("Segoe UI", 14),
    text_color=MUTED
).pack(anchor="w", pady=(4, 15))


# ==========================================
# SYSTEM STATUS
# ==========================================

status_card = ctk.CTkFrame(
    content,
    fg_color=CARD,
    corner_radius=15,
    height=75
)

status_card.pack(fill="x", pady=(0, 15))
status_card.pack_propagate(False)

ctk.CTkLabel(
    status_card,
    text="SYSTEM STATUS",
    font=("Segoe UI", 10, "bold"),
    text_color=MUTED
).pack(anchor="w", padx=20, pady=(10, 2))

status_label = ctk.CTkLabel(
    status_card,
    text="● CAMERA IS OFF",
    font=("Segoe UI", 16, "bold"),
    text_color=MUTED
)

status_label.pack(anchor="w", padx=20)


# ==========================================
# CAMERA CONTROLS
# ==========================================

ctk.CTkLabel(
    content,
    text="CAMERA CONTROLS",
    font=("Segoe UI", 12, "bold"),
    text_color=WHITE
).pack(anchor="w", pady=(0, 8))

button_row = ctk.CTkFrame(
    content,
    fg_color="transparent"
)

button_row.pack(fill="x", pady=(0, 15))

camera_button = ctk.CTkButton(
    button_row,
    text="START CAMERA",
    font=("Segoe UI", 12, "bold"),
    fg_color=PURPLE,
    hover_color="#7040D0",
    height=40,
    command=start_camera
)

camera_button.pack(side="left", padx=(0, 10))

ctk.CTkButton(
    button_row,
    text="STOP CAMERA",
    font=("Segoe UI", 12, "bold"),
    fg_color="#34202B",
    hover_color="#542637",
    text_color="#FF8A9B",
    height=40,
    command=stop_camera
).pack(side="left")


# ==========================================
# CAMERA AND GESTURE DISPLAY
# ==========================================

main_display = ctk.CTkFrame(
    content,
    fg_color="transparent"
)

main_display.pack(
    fill="both",
    expand=True
)

main_display.grid_columnconfigure(0, weight=3)
main_display.grid_columnconfigure(1, weight=2)
main_display.grid_rowconfigure(0, weight=1)


# ==========================================
# CAMERA PREVIEW PANEL
# ==========================================

camera_card = ctk.CTkFrame(
    main_display,
    fg_color=CARD,
    corner_radius=15
)

camera_card.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 12)
)

camera_header = ctk.CTkFrame(
    camera_card,
    fg_color="transparent"
)

camera_header.pack(
    fill="x",
    padx=15,
    pady=(15, 10)
)

ctk.CTkLabel(
    camera_header,
    text="LIVE CAMERA FEED",
    font=("Segoe UI", 12, "bold"),
    text_color=LIGHT_PURPLE
).pack(side="left")

fps_label = ctk.CTkLabel(
    camera_header,
    text="FPS: --",
    font=("Segoe UI", 11, "bold"),
    text_color=GREEN
)

fps_label.pack(side="right")

camera_preview = ctk.CTkLabel(
    camera_card,
    text="CAMERA OFF\n\nClick START CAMERA to begin.",
    font=("Segoe UI", 16, "bold"),
    text_color=MUTED,
    fg_color="#101019",
    corner_radius=10,
    width=560,
    height=420
)

camera_preview.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=(0, 12)
)


# ==========================================
# GESTURE INFORMATION PANEL
# ==========================================

gesture_card = ctk.CTkFrame(
    main_display,
    fg_color=CARD,
    corner_radius=15
)

gesture_card.grid(
    row=0,
    column=1,
    sticky="nsew"
)

ctk.CTkLabel(
    gesture_card,
    text="LIVE GESTURE STATUS",
    font=("Segoe UI", 12, "bold"),
    text_color=LIGHT_PURPLE
).pack(anchor="w", padx=15, pady=(15, 10))

gesture_status_label = ctk.CTkLabel(
    gesture_card,
    text="WAITING FOR CAMERA",
    font=("Segoe UI", 16, "bold"),
    text_color=MUTED,
    wraplength=250
)

gesture_status_label.pack(
    anchor="w",
    padx=15,
    pady=(5, 15)
)

ctk.CTkFrame(
    gesture_card,
    height=1,
    fg_color="#29293A"
).pack(fill="x", padx=15, pady=5)

ctk.CTkLabel(
    gesture_card,
    text="GESTURE GUIDE",
    font=("Segoe UI", 12, "bold"),
    text_color=WHITE
).pack(anchor="w", padx=15, pady=(10, 8))

gesture_data = [
    ("01", "Cursor Movement", "Raise index finger"),
    ("02", "Left Click", "Thumb + index pinch"),
    ("03", "Right Click", "Thumb + ring pinch"),
    ("04", "Scrolling", "Hold thumb + middle pinch")
]

for number, action, instruction in gesture_data:

    item = ctk.CTkFrame(
        gesture_card,
        fg_color="#20202D",
        corner_radius=8
    )

    item.pack(
        fill="x",
        padx=12,
        pady=3
    )

    ctk.CTkLabel(
        item,
        text=number,
        font=("Segoe UI", 10, "bold"),
        text_color=LIGHT_PURPLE
    ).pack(anchor="w", padx=10, pady=(5, 0))

    ctk.CTkLabel(
        item,
        text=action,
        font=("Segoe UI", 11, "bold"),
        text_color=WHITE
    ).pack(anchor="w", padx=10)

    ctk.CTkLabel(
        item,
        text=instruction,
        font=("Segoe UI", 9),
        text_color=MUTED,
        wraplength=240
    ).pack(anchor="w", padx=10, pady=(0, 5))


# ==========================================
# ABOUT PROJECT
# ==========================================

def show_about():

    about_window = ctk.CTkToplevel(app)

    about_window.title("About VisionMouse")
    about_window.geometry("550x480")
    about_window.configure(fg_color=BG)

    about_window.transient(app)

    ctk.CTkLabel(
        about_window,
        text="◈ VISIONMOUSE",
        font=("Segoe UI", 26, "bold"),
        text_color=LIGHT_PURPLE
    ).pack(pady=(30, 10))

    ctk.CTkLabel(
        about_window,
        text="AI-Based Hand Gesture Recognition System",
        font=("Segoe UI", 15, "bold"),
        text_color=WHITE
    ).pack(pady=5)

    description = (
        "VisionMouse is a computer vision application "
        "that allows users to control their computer "
        "using hand gestures detected through a webcam.\n\n"
        "The system uses MediaPipe to detect hand landmarks "
        "and Python automation to perform mouse actions."
    )

    ctk.CTkLabel(
        about_window,
        text=description,
        font=("Segoe UI", 13),
        text_color=MUTED,
        wraplength=450,
        justify="center"
    ).pack(pady=20, padx=25)

    ctk.CTkLabel(
        about_window,
        text="TECHNOLOGIES USED",
        font=("Segoe UI", 13, "bold"),
        text_color=LIGHT_PURPLE
    ).pack(pady=(10, 10))

    ctk.CTkLabel(
        about_window,
        text="Python  •  OpenCV  •  MediaPipe\nPyAutoGUI  •  CustomTkinter",
        font=("Segoe UI", 13),
        text_color=WHITE,
        justify="center"
    ).pack(pady=5)

    ctk.CTkLabel(
        about_window,
        text="VISIONMOUSE  •  VERSION 1.0",
        font=("Segoe UI", 10),
        text_color="#626276"
    ).pack(side="bottom", pady=20)


# ==========================================
# FOOTER
# ==========================================

ctk.CTkLabel(
    content,
    text="VISIONMOUSE  •  AI HAND GESTURE CONTROL",
    font=("Segoe UI", 10),
    text_color="#626276"
).pack(side="bottom", pady=(12, 0))


# ==========================================
# START APPLICATION
# ==========================================

welcome_frame.pack(
    fill="both",
    expand=True
)

app.protocol(
    "WM_DELETE_WINDOW",
    close_application
)

app.mainloop()
