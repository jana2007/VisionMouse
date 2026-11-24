# VisionMouse – AI-Based Hand Gesture Control System

VisionMouse is a computer vision-based desktop application that allows users to control their computer mouse using hand gestures captured through a webcam.

The application uses **MediaPipe Hands** to detect and track hand landmarks in real time, **OpenCV** to process webcam frames, and **PyAutoGUI** to perform mouse actions.

## Features

- **Cursor Movement:** Move the index finger to control the mouse cursor.
- **Left Click:** Pinch the thumb and index finger together.
- **Right Click:** Pinch the thumb and ring finger together.
- **Scrolling:** Pinch all the fingers together, then move the hand up or down.
- **Real-Time Hand Tracking:** Detects and displays hand landmarks through the webcam.
- **Interactive Dashboard:** Provides a desktop interface with camera controls and gesture status indicators.

## Technologies Used

- Python
- OpenCV
- MediaPipe
- PyAutoGUI
- CustomTkinter
- Pillow (PIL)
- NumPy

## Project Structure

```text
VisionMouse/
│
├── app.py
├── main.py
├── finger_detection.py
├── cursor_control.py
├── pinch_click.py
├── advanced_controls.py
│
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the project folder

```bash
cd VisionMouse
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install the dependencies

```bash
python -m pip install numpy==1.26.4
python -m pip install mediapipe==0.10.21
python -m pip install opencv-contrib-python==4.11.0.86
python -m pip install pyautogui customtkinter Pillow
```

### 6. Run the application

```bash
python app.py
```

Make sure your webcam is connected and allow camera access when prompted.

## How It Works

1. The webcam captures live video of the user's hand.
2. OpenCV processes the video frames.
3. MediaPipe Hands detects and tracks hand landmarks.
4. The application identifies specific finger positions and pinch gestures.
5. PyAutoGUI translates the detected gestures into mouse actions.
6. The dashboard displays the live camera feed and gesture status.

## Requirements

- Python 3.12
- A working webcam
- Windows desktop environment
- Good lighting for reliable hand detection

## Future Improvements

- Customizable gesture controls.
- Improved gesture recognition and accuracy.
- Support for additional hand gestures.
- Enhanced user settings and accessibility options.

## Author

Developed as a computer vision project to explore real-time hand tracking and touch-free desktop interaction.