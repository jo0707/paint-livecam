"""
Configuration settings for the finger tracking drawing application.
This module contains various settings that can be adjusted to customize the application behavior.
"""

# Display configuration
WINDOW_NAME = "Paint LiveCam"
WINDOW_SIZE = (860, 640)  # Default window size (width, height)

# FPS display configuration
SHOW_FPS = True

# Hand tracking configuration
SHOW_HAND_LANDMARKS = True  # Show hand skeleton lines
MAX_HANDS = 1  # Maximum number of hands to track
HAND_DETECTION_CONFIDENCE = 0.7  # Minimum confidence for hand detection
HAND_TRACKING_CONFIDENCE = 0.5  # Minimum confidence for hand tracking

# Face tracking configuration
SHOW_FACE_BOUNDING_BOX = True  # Show rectangle around detected faces
FACE_DETECTION_CONFIDENCE = 0.5  # Minimum confidence for face detection

# Drawing settings
DEFAULT_DRAWING_COLOR = (0, 255, 255)  # Default: Yellow
DEFAULT_LINE_THICKNESS = 4
CANVAS_OPACITY = 1  # Canvas overlay opacity (0.0 to 1.0)

# UI configuration
SHOW_UI_BY_DEFAULT = True  # Show buttons and UI elements by default

# Button configuration
BUTTON_COOLDOWN_FRAMES = 20  # Number of frames to wait between button activations
BUTTON_COLORS = {
    "reset": (200, 50, 50),  # Red
    "color": (0, 128, 255),  # Orange
    "thickness": (150, 150, 150),  # Gray
    "save": (0, 200, 0),  # Green
}

# Available drawing colors (name: BGR color)
DRAWING_COLORS = {
    "Yellow": (0, 255, 255),
    "Blue": (255, 0, 0),
    "Green": (0, 255, 0),
    "Red": (0, 0, 255),
    "Purple": (255, 0, 255),
    "Orange": (0, 165, 255),
    "White": (255, 255, 255),
    "Black": (0, 0, 0),
}

# Line thickness options
LINE_THICKNESS_OPTIONS = {
    "Thin": 2,
    "Medium": 4,
    "Thick": 8,
    "Very Thick": 12,
}

# File saving configuration
SAVE_DIRECTORY = "saved_drawings"