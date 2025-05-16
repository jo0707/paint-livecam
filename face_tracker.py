import cv2
import mediapipe as mp
import numpy as np
import configurations as config


class FaceTracker:
    """Class for detecting faces using MediaPipe."""
    
    def __init__(self, min_detection_confidence=None):
        """Initialize the face detection module."""
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=min_detection_confidence or config.FACE_DETECTION_CONFIDENCE
        )
    
    def find_faces(self, img, draw=None):
        """Find faces in an image and optionally draw the detections."""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.face_detection.process(imgRGB)
        
        faces = []
        
        if self.results.detections:
            h, w, c = img.shape
            for detection in self.results.detections:
                bbox = detection.location_data.relative_bounding_box
                x, y, width, height = int(bbox.xmin * w), int(bbox.ymin * h), int(bbox.width * w), int(bbox.height * h)
                
                # Create a face object with bounding box, center, and size
                face = {
                    'bbox': (x, y, width, height),
                    'center': (x + width//2, y + height//2),
                    'size': (width, height)
                }
                faces.append(face)
                
                if draw if draw is not None else config.SHOW_FACE_BOUNDING_BOX:
                    cv2.rectangle(img, (x, y), (x + width, y + height), (0, 255, 0), 2)
        
        return img, faces
