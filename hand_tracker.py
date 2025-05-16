import cv2
import mediapipe as mp
import numpy as np
import configurations as config

class HandTracker:
    """Class for tracking hand landmarks using MediaPipe."""
    
    def __init__(self, 
                 static_image_mode=False, 
                 max_num_hands=None, 
                 min_detection_confidence=None, 
                 min_tracking_confidence=None):
        """Initialize the hand tracking module."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands or config.MAX_HANDS,
            min_detection_confidence=min_detection_confidence or config.HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=min_tracking_confidence or config.HAND_TRACKING_CONFIDENCE
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
    
    def find_hands(self, img, draw=None):
        """Find hands in an image and optionally draw the landmarks."""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        
        if self.results.multi_hand_landmarks and (draw if draw is not None else config.SHOW_HAND_LANDMARKS):
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    img, 
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        
        return img
    
    def find_position(self, img):
        """Find the position of hand landmarks and return them."""
        hand_landmarks = []
        
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[0]  # Only using the first hand
            h, w, c = img.shape
            for id, lm in enumerate(my_hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                hand_landmarks.append([id, cx, cy])
                
        return hand_landmarks