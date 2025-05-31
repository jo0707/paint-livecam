import cv2
import mediapipe as mp
import numpy as np
import time
import os
import configurations as config
from sound_manager import play_click, play_writing


class Button:
    """Class for interactive buttons that can be activated by finger touch."""
    
    def __init__(self, x, y, width, height, color, text, action):
        """Initialize a button with position, size, appearance, and functionality."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.text = text
        self.action = action
        self.is_pressed = False
    
    def is_clicked(self, point):
        """Check if a point (finger tip) is inside the button area."""
        return (self.x <= point[0] <= self.x + self.width and 
                self.y <= point[1] <= self.y + self.height)
    
    def draw(self, img):
        """Draw the button on the image."""
        # Draw button background
        button_color = (self.color[0] - 40, self.color[1] - 40, self.color[2] - 40) if self.is_pressed else self.color
        cv2.rectangle(img, (self.x, self.y), (self.x + self.width, self.y + self.height), button_color, cv2.FILLED)
        cv2.rectangle(img, (self.x, self.y), (self.x + self.width, self.y + self.height), (50, 50, 50), 2)
        
        # Draw button text
        text_size = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + (self.height + text_size[1]) // 2
        cv2.putText(img, self.text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return img


class DrawingCanvas:
    """Class for managing the drawing functionality."""
    
    def __init__(self, width, height):
        """Initialize the drawing canvas."""
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.drawing_segments = []  # List of drawing segments with their properties
        self.is_drawing = False
        self.last_face_center = None
        self.width = width
        self.height = height
        
        # Drawing settings for new lines
        self.drawing_color = config.DEFAULT_DRAWING_COLOR
        self.line_thickness = config.DEFAULT_LINE_THICKNESS
        
        # Face tracking state
        self.current_face_mode = "still"  # "still" or "following" - affects all new lines
        self.face_following_segments = set()  # Indices of segments that should follow face
        
        # Available colors
        self.colors = config.DRAWING_COLORS
        
        # Initialize buttons
        self.buttons = []
        self.show_ui = config.SHOW_UI_BY_DEFAULT
        
        # Store current camera image for saving with background
        self.current_camera_img = None
        
        self.setup_default_buttons()
        
        # Button cooldown to prevent multiple activations
        self.button_cooldown = 0
        self.cooldown_duration = config.BUTTON_COOLDOWN_FRAMES
        
        # Create output directory for saved images
        self.output_dir = config.SAVE_DIRECTORY
        os.makedirs(self.output_dir, exist_ok=True)
    
    def setup_default_buttons(self):
        """Set up the default buttons."""
        # Add reset button in the top right corner
        reset_btn = Button(
            self.width - 110, 10, 100, 40, 
            config.BUTTON_COLORS["reset"], "Reset", 
            self.clear_canvas
        )
        self.buttons.append(reset_btn)
        
        # Add all other buttons by default
        if config.SHOW_UI_BY_DEFAULT:
            self.add_color_buttons()
            self.add_thickness_buttons()
            self.add_save_button()
    
    def add_button(self, x, y, width, height, color, text, action):
        """Add a new button to the canvas."""
        new_button = Button(x, y, width, height, color, text, action)
        self.buttons.append(new_button)
        return new_button
    
    def add_color_buttons(self):
        """Add color selection buttons."""
        y_offset = 10
        x_pos = 10
        height = 30
        width = 80
        for color_name, color_value in self.colors.items():
            # Create a button for each color
            self.add_button(
                x_pos, y_offset, width, height,
                color_value, color_name,
                lambda col=color_value, name=color_name: self.change_color(col, name)
            )
            y_offset += height + 10
    
    def add_thickness_buttons(self):
        """Add line thickness adjustment buttons."""
        y_offset = 10
        x_pos = 100
        for thickness_name, thickness_value in config.LINE_THICKNESS_OPTIONS.items():
            self.add_button(
                x_pos, y_offset, 80, 30,
                config.BUTTON_COLORS["thickness"], thickness_name,
                lambda t=thickness_value, name=thickness_name: self.change_thickness(t, name)
            )
            y_offset += 40
    
    def add_save_button(self):
        """Add a button to save the current drawing."""
        self.add_button(
            self.width - 110, 60, 100, 40,
            config.BUTTON_COLORS["save"], "Save",
            self.save_drawing
        )
    
    def toggle_ui_visibility(self):
        """Toggle visibility of UI elements."""
        self.show_ui = not self.show_ui
        print(f"UI visibility: {'shown' if self.show_ui else 'hidden'}")
    
    def check_button_press(self, point, finger_id):
        """Check if a finger tip is pressing any button."""
        # Only process pinky finger (finger_id 20) for button interaction
        if finger_id != 20 or self.button_cooldown > 0 or not self.show_ui:
            return False
        
        for button in self.buttons:
            if button.is_clicked(point):
                button.is_pressed = True
                self.button_cooldown = self.cooldown_duration
                # Play click sound when button is pressed
                play_click()
                button.action()
                return True
            else:
                button.is_pressed = False
        
        return False
    
    def update_cooldown(self):
        """Update button cooldown timer."""
        if self.button_cooldown > 0:
            self.button_cooldown -= 1
    
    def draw_buttons(self, img):
        """Draw all buttons on the image if UI is visible."""
        if self.show_ui:
            for button in self.buttons:
                img = button.draw(img)
        return img
    
    def clear_canvas(self):
        """Clear all drawings from the canvas."""
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.drawing_segments = []
        self.is_drawing = False
        self.current_face_mode = "still"
        self.face_following_segments.clear()
        print("Canvas cleared")
    
    def change_color(self, color, name):
        """Change the drawing color for new lines."""
        self.drawing_color = color
        print(f"Color changed to {name} (affects next line)")
    
    def change_thickness(self, thickness, name=None):
        """Change the line thickness for new lines."""
        self.line_thickness = thickness
        name_str = f" ({name})" if name else ""
        print(f"Line thickness changed to {thickness}{name_str} (affects next line)")
    
    def save_drawing(self):
        """Save the current drawing with camera background to a file."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"drawing_{timestamp}.png")
        
        if self.current_camera_img is not None:
            # Resize canvas to match camera image size if needed
            if self.current_camera_img.shape[:2] != self.canvas.shape[:2]:
                canvas_resized = cv2.resize(self.canvas, (self.current_camera_img.shape[1], self.current_camera_img.shape[0]))
            else:
                canvas_resized = self.canvas
            
            # Combine camera image with drawing canvas
            combined_img = cv2.addWeighted(self.current_camera_img, 0.8, canvas_resized, config.CANVAS_OPACITY, 0)
            cv2.imwrite(filename, combined_img)
            print(f"Drawing with camera background saved to {filename}")
        else:
            # Fallback: save just the canvas if no camera image available
            cv2.imwrite(filename, self.canvas)
            print(f"Drawing saved to {filename}")
    
    def start_drawing(self, point):
        """Start a new drawing segment with current color, thickness, and face mode."""
        self.is_drawing = True
        
        # Create new segment with current properties and face mode
        new_segment = {
            'points': [point],
            'color': self.drawing_color,
            'thickness': self.line_thickness,
            'follows_face': (self.current_face_mode == "following")
        }
        self.drawing_segments.append(new_segment)
        
        # If this line should follow face, add it to the following set
        if self.current_face_mode == "following":
            current_segment_index = len(self.drawing_segments) - 1
            self.face_following_segments.add(current_segment_index)
    
    def continue_drawing(self, point):
        """Continue drawing the current segment."""
        if self.is_drawing and self.drawing_segments:
            # Play writing sound while drawing (with cooldown to prevent spam)
            play_writing()
            self.drawing_segments[-1]['points'].append(point)
    
    def stop_drawing(self, end_point=None):
        """Stop the current drawing segment and check where it ended."""
        if not self.is_drawing or not self.drawing_segments:
            self.is_drawing = False
            return
        
        # Get the last point of the current segment
        current_segment = self.drawing_segments[-1]
        if end_point:
            last_point = end_point
        elif current_segment['points']:
            last_point = current_segment['points'][-1]
        else:
            self.is_drawing = False
            return
        
        # Check if the line ended near a face to set mode for future lines
        face_detected = self._check_point_near_any_face(last_point)
        
        if face_detected:
            if self.current_face_mode != "following":
                self.current_face_mode = "following"
                print("Line ended near face - future lines will follow face movement")
        else:
            if self.current_face_mode != "still":
                self.current_face_mode = "still"
                print("Line ended away from face - future lines will be still")
        
        # Update the current segment's face following status if it changed
        current_segment_index = len(self.drawing_segments) - 1
        if self.current_face_mode == "following" and not current_segment['follows_face']:
            current_segment['follows_face'] = True
            self.face_following_segments.add(current_segment_index)
        elif self.current_face_mode == "still" and current_segment['follows_face']:
            current_segment['follows_face'] = False
            self.face_following_segments.discard(current_segment_index)
        
        self.is_drawing = False
    
    def _check_point_near_any_face(self, point):
        """Check if a point is near any detected face."""
        if hasattr(self, '_current_faces'):
            for face in self._current_faces:
                x, y, w, h = face['bbox']
                if (x <= point[0] <= x + w and 
                    y <= point[1] <= y + h):
                    return True
        return False
    
    def update_faces(self, faces):
        """Update the current faces information for face proximity checking."""
        self._current_faces = faces
    
    def draw_on_canvas(self):
        """Draw all segments on the canvas with their individual properties."""
        # Clear canvas
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw each segment with its own color and thickness
        for segment in self.drawing_segments:
            points = segment['points']
            color = segment['color']
            thickness = segment['thickness']
            
            if len(points) > 1:
                for i in range(1, len(points)):
                    cv2.line(self.canvas, points[i-1], points[i], color, thickness)
    
    def adjust_drawings_to_face(self, face_center):
        """Adjust only face-following drawings to follow face movement."""
        if not self.last_face_center or not face_center:
            self.last_face_center = face_center
            return
        
        if self.last_face_center != face_center and self.face_following_segments:
            # Calculate the offset between the current and last face position
            dx = face_center[0] - self.last_face_center[0]
            dy = face_center[1] - self.last_face_center[1]
            
            # Update only the segments that follow the face
            for segment_index in self.face_following_segments:
                if segment_index < len(self.drawing_segments):
                    segment = self.drawing_segments[segment_index]
                    for i in range(len(segment['points'])):
                        x, y = segment['points'][i]
                        segment['points'][i] = (x + dx, y + dy)
            
            # Update the last face center
            self.last_face_center = face_center
            
            # Redraw canvas with updated positions
            self.draw_on_canvas()
    
    def check_drawing_near_face(self, face):
        """Legacy method - now just returns True if face exists for compatibility."""
        return face is not None
