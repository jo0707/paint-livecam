import cv2
import mediapipe as mp
import numpy as np
import time
import os
import configurations as config


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
        self.drawing_points = []
        self.is_drawing = False
        self.last_face_center = None
        self.width = width
        self.height = height
        
        # Drawing settings
        self.drawing_color = config.DEFAULT_DRAWING_COLOR
        self.line_thickness = config.DEFAULT_LINE_THICKNESS
        
        # Available colors
        self.colors = config.DRAWING_COLORS
        
        # Initialize buttons
        self.buttons = []
        self.show_ui = config.SHOW_UI_BY_DEFAULT
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
        self.drawing_points = []
        self.is_drawing = False
        print("Canvas cleared")
    
    def change_color(self, color, name):
        """Change the drawing color."""
        self.drawing_color = color
        print(f"Color changed to {name}")
    
    def change_thickness(self, thickness, name=None):
        """Change the line thickness."""
        self.line_thickness = thickness
        name_str = f" ({name})" if name else ""
        print(f"Line thickness changed to {thickness}{name_str}")
    
    def save_drawing(self):
        """Save the current drawing to a file."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"drawing_{timestamp}.png")
        cv2.imwrite(filename, self.canvas)
        print(f"Drawing saved to {filename}")
    
    def start_drawing(self, point):
        """Start a new drawing segment."""
        self.is_drawing = True
        self.drawing_points.append([point])
    
    def continue_drawing(self, point):
        """Continue drawing the current segment."""
        if self.is_drawing and self.drawing_points:
            self.drawing_points[-1].append(point)
    
    def stop_drawing(self):
        """Stop the current drawing segment."""
        self.is_drawing = False
    
    def draw_on_canvas(self, color=None, thickness=None):
        """Draw all points on the canvas."""
        # Use provided color and thickness or default to instance variables
        color = color or self.drawing_color
        thickness = thickness or self.line_thickness
        
        for points in self.drawing_points:
            if len(points) > 1:
                for i in range(1, len(points)):
                    cv2.line(self.canvas, points[i-1], points[i], color, thickness)
    
    def adjust_drawings_to_face(self, face_center):
        """Adjust drawings to follow face movement."""
        if not self.last_face_center or not face_center or not self.drawing_points:
            self.last_face_center = face_center
            return
        
        if self.last_face_center != face_center:
            # Calculate the offset between the current and last face position
            dx = face_center[0] - self.last_face_center[0]
            dy = face_center[1] - self.last_face_center[1]
            
            # Update all drawing points
            for segment in self.drawing_points:
                for i in range(len(segment)):
                    segment[i] = (segment[i][0] + dx, segment[i][1] + dy)
            
            # Update the last face center
            self.last_face_center = face_center
            
            # Clear the canvas and redraw
            self.canvas = np.zeros_like(self.canvas)
            self.draw_on_canvas()
    
    def check_drawing_near_face(self, face, point_radius=10):
        """Check if any drawing point is near a face."""
        if not face or not self.drawing_points:
            return False
        
        x, y, w, h = face['bbox']
        face_area = (x-point_radius, y-point_radius, x+w+point_radius, y+h+point_radius)
        
        for segment in self.drawing_points:
            for point in segment:
                if (face_area[0] <= point[0] <= face_area[2] and 
                    face_area[1] <= point[1] <= face_area[3]):
                    return True
        
        return False
