import cv2
import mediapipe as mp
import numpy as np
import time
import os
import configurations as config
from sound_manager import play_click, play_writing


class Button:
    """Interactive button that responds to finger touch."""
    
    def __init__(self, x, y, width, height, color, text, action):
        """Create button with position (x,y), size (width,height), appearance (color), label (text), and callback (action)."""
        self.x, self.y, self.width, self.height = x, y, width, height
        self.color, self.text, self.action = color, text, action
        self.is_pressed = False
    
    def is_clicked(self, point):
        """Check if point (x,y) is inside button area."""
        return (self.x <= point[0] <= self.x + self.width and self.y <= point[1] <= self.y + self.height)
    
    def draw(self, img):
        """Draw button on image with pressed state visual feedback."""
        # Button background (darker when pressed)
        btn_color = (self.color[0] - 40, self.color[1] - 40, self.color[2] - 40) if self.is_pressed else self.color
        cv2.rectangle(img, (self.x, self.y), (self.x + self.width, self.y + self.height), btn_color, cv2.FILLED)
        cv2.rectangle(img, (self.x, self.y), (self.x + self.width, self.y + self.height), (50, 50, 50), 2)
        
        # Center text on button
        text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2
        cv2.putText(img, self.text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return img


class DrawingCanvas:
    """Manages drawing functionality with finger tracking, face following, and UI controls."""
    
    def __init__(self, width, height):
        """Initialize drawing canvas with specified dimensions and setup all UI elements."""
        # Canvas setup
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.width, self.height = width, height
        self.current_camera_img = None
        
        # Drawing state
        self.drawing_segments = []  # [{points: [(x,y)...], color: (b,g,r), thickness: int, follows_face: bool}]
        self.is_drawing = False
        self.drawing_color = config.DEFAULT_DRAWING_COLOR
        self.line_thickness = config.DEFAULT_LINE_THICKNESS
        
        # Face tracking
        self.current_face_mode = "still"  # "still" or "following" - affects new lines
        self.face_following_segments = set()  # Indices of segments that follow face
        self.last_face_center = None
        self._current_faces = []
        
        # UI elements
        self.buttons = []
        self.show_ui = config.SHOW_UI_BY_DEFAULT
        self.button_cooldown = 0
        self.colors = config.DRAWING_COLORS
        
        # Setup all buttons inline
        self._setup_all_buttons()
        
        # Create output directory
        self.output_dir = config.SAVE_DIRECTORY
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _setup_all_buttons(self):
        """Setup all UI buttons in one place - colors, thickness, reset, save."""
        # Reset button (always visible)
        self.buttons.append(Button(self.width - 110, 10, 100, 40, config.BUTTON_COLORS["reset"], "Reset", self.clear_canvas))
        
        if config.SHOW_UI_BY_DEFAULT:
            # Color buttons (left side)
            y_pos = 10
            for color_name, color_value in self.colors.items():
                self.buttons.append(Button(10, y_pos, 80, 30, color_value, color_name, 
                                         lambda col=color_value, name=color_name: self._set_color(col, name)))
                y_pos += 40
            
            # Thickness buttons (middle)
            y_pos = 10
            for thickness_name, thickness_value in config.LINE_THICKNESS_OPTIONS.items():
                self.buttons.append(Button(100, y_pos, 80, 30, config.BUTTON_COLORS["thickness"], thickness_name,
                                         lambda t=thickness_value, name=thickness_name: self._set_thickness(t, name)))
                y_pos += 40
            
            # Save button
            self.buttons.append(Button(self.width - 110, 60, 100, 40, config.BUTTON_COLORS["save"], "Save", self.save_drawing))
    
    def _set_color(self, color, name):
        """Set drawing color for new lines."""
        self.drawing_color = color
        print(f"Color: {name}")
    
    def _set_thickness(self, thickness, name):
        """Set line thickness for new lines."""
        self.line_thickness = thickness
        print(f"Thickness: {name}")
    
    def process_finger_input(self, point, finger_id):
        """Process finger input for drawing (index finger) or UI interaction (pinky finger)."""
        # Update cooldown
        if self.button_cooldown > 0:
            self.button_cooldown -= 1
        
        # Pinky finger (20) for UI buttons
        if finger_id == 20 and self.show_ui and self.button_cooldown == 0:
            for button in self.buttons:
                if button.is_clicked(point):
                    button.is_pressed = True
                    self.button_cooldown = config.BUTTON_COOLDOWN_FRAMES
                    play_click()
                    button.action()
                    return True
                button.is_pressed = False
        
        # Index finger (8) for drawing
        elif finger_id == 8:
            if not self.is_drawing:
                self.start_drawing(point)
            else:
                self.continue_drawing(point)
            return True
        
        return False
    
    def start_drawing(self, point):
        """Start new drawing segment with current settings and face mode."""
        self.is_drawing = True
        
        # Create new segment with current properties
        new_segment = {
            'points': [point],
            'color': self.drawing_color,
            'thickness': self.line_thickness,
            'follows_face': (self.current_face_mode == "following")
        }
        self.drawing_segments.append(new_segment)
        
        # Track face-following segments
        if self.current_face_mode == "following":
            self.face_following_segments.add(len(self.drawing_segments) - 1)
    
    def continue_drawing(self, point):
        """Add point to current drawing segment."""
        if self.is_drawing and self.drawing_segments:
            play_writing()
            self.drawing_segments[-1]['points'].append(point)
    
    def stop_drawing(self, end_point=None):
        """Stop drawing and determine face mode for future lines based on end position."""
        if not self.is_drawing or not self.drawing_segments:
            self.is_drawing = False
            return
        
        # Get last point to check face proximity
        current_segment = self.drawing_segments[-1]
        last_point = end_point if end_point else (current_segment['points'][-1] if current_segment['points'] else None)
        
        if last_point:
            # Check if line ended near any face to set future line mode
            face_detected = any(
                face['bbox'][0] <= last_point[0] <= face['bbox'][0] + face['bbox'][2] and
                face['bbox'][1] <= last_point[1] <= face['bbox'][1] + face['bbox'][3]
                for face in self._current_faces
            )
            
            # Update face mode for future lines
            new_mode = "following" if face_detected else "still"
            if new_mode != self.current_face_mode:
                self.current_face_mode = new_mode
                print(f"Face mode: {new_mode}")
            
            # Update current segment's face following status
            segment_index = len(self.drawing_segments) - 1
            if new_mode == "following" and not current_segment['follows_face']:
                current_segment['follows_face'] = True
                self.face_following_segments.add(segment_index)
            elif new_mode == "still" and current_segment['follows_face']:
                current_segment['follows_face'] = False
                self.face_following_segments.discard(segment_index)
        
        self.is_drawing = False
    
    def update_with_face_movement(self, face_center):
        """Update face-following drawings when face moves."""
        if not self.last_face_center or not face_center or not self.face_following_segments:
            self.last_face_center = face_center
            return
        
        # Calculate face movement offset
        dx = face_center[0] - self.last_face_center[0]
        dy = face_center[1] - self.last_face_center[1]
        
        # Move all face-following segments
        for segment_index in self.face_following_segments:
            if segment_index < len(self.drawing_segments):
                segment = self.drawing_segments[segment_index]
                segment['points'] = [(x + dx, y + dy) for x, y in segment['points']]
        
        self.last_face_center = face_center
        self.draw_on_canvas()
    
    def draw_on_canvas(self):
        """Render all drawing segments to canvas with their individual properties."""
        self.canvas.fill(0)  # Clear canvas
        
        # Draw each segment with its color and thickness
        for segment in self.drawing_segments:
            points = segment['points']
            if len(points) > 1:
                for i in range(1, len(points)):
                    cv2.line(self.canvas, points[i-1], points[i], segment['color'], segment['thickness'])
    
    def draw_ui(self, img):
        """Draw all UI buttons on image."""
        if self.show_ui:
            for button in self.buttons:
                img = button.draw(img)
        return img
    
    def clear_canvas(self):
        """Clear all drawings and reset state."""
        self.canvas.fill(0)
        self.drawing_segments.clear()
        self.face_following_segments.clear()
        self.is_drawing = False
        self.current_face_mode = "still"
        print("Canvas cleared")
    
    def save_drawing(self):
        """Save current drawing with camera background to file."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"drawing_{timestamp}.png")
        
        if self.current_camera_img is not None:
            # Combine camera image with drawing
            canvas_resized = cv2.resize(self.canvas, (self.current_camera_img.shape[1], self.current_camera_img.shape[0])) \
                           if self.current_camera_img.shape[:2] != self.canvas.shape[:2] else self.canvas
            combined_img = cv2.addWeighted(self.current_camera_img, 0.8, canvas_resized, config.CANVAS_OPACITY, 0)
            cv2.imwrite(filename, combined_img)
        else:
            cv2.imwrite(filename, self.canvas)
        
        print(f"Saved: {filename}")
    
    def update_faces(self, faces):
        """Update current faces for proximity detection."""
        self._current_faces = faces
    
    def toggle_ui(self):
        """Toggle UI visibility."""
        self.show_ui = not self.show_ui
        print(f"UI: {'shown' if self.show_ui else 'hidden'}")
