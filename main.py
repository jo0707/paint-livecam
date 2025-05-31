
import cv2
import time
from datetime import datetime

import configurations as config
from drawing_canvas import DrawingCanvas
from face_tracker import FaceTracker
from hand_tracker import HandTracker
from sound_manager import play_background


class PaintLivecam:
    """Main application class that manages the paint livecam functionality."""
    
    def __init__(self):
        """Initialize camera, trackers, and canvas."""
        # Initialize camera
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")
        
        # Get camera dimensions
        _, sample_frame = self.cap.read()
        h, w = sample_frame.shape[:2]
        
        # Initialize components
        self.hand_tracker = HandTracker()
        self.face_tracker = FaceTracker()
        self.canvas = DrawingCanvas(w, h)
        
        # Setup display window
        cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_NAME, *config.WINDOW_SIZE)
        
        # Performance tracking
        self.fps_time = 0
        
        # Start background music
        play_background()
        self._print_instructions()
    
    def _print_instructions(self):
        """Display usage instructions to console."""
        print("\n" + "="*50)
        print("PAINT LIVECAM - Ready to Draw!")
        print("="*50)
        print("🎨 Drawing:")
        print("   • Index finger (tip above base) = Draw")
        print("   • V gesture (index and middle up) = Pause draw")
        print("   • Middle finger tip = Click UI buttons")
        print("\n🎭 Features:")
        print("   • Drawings follow your face movement")
        print("   • Multiple colors and brush sizes")
        print("\n⌨️  Controls:")
        print("   • 'i' = Toggle UI visibility")
        print("   • 'q' = Quit")
        print("="*50 + "\n")
    
    def _extract_finger_positions(self, landmarks):
        """Extract index tip, index base, and middle tip positions from hand landmarks."""
        positions = {'index_tip': None, 'middle_tip': None, 'middle_one': None}
        
        for landmark_id, x, y in landmarks:
            if landmark_id == 8:    # Index finger tip
                positions['index_tip'] = (x, y)
            elif landmark_id == 12:  # middle finger tip
                positions['middle_tip'] = (x, y)
            elif landmark_id == 9: # middle finger book
                positions['middle_one'] = (x, y)
        
        return positions
    
    def _draw_finger_indicators(self, img, positions):
        """Draw visual indicators on detected finger positions."""
        if positions['index_tip']:
            cv2.circle(img, positions['index_tip'], 10, (255, 0, 255), cv2.FILLED)
        if positions['middle_tip']:
            cv2.circle(img, positions['middle_tip'], 8, (0, 255, 255), cv2.FILLED)
    
    def _process_hand_input(self, positions):
        """Process hand gestures for drawing and UI interaction."""
        # Handle middle finger UI interaction
        if positions['middle_tip']:
            self.canvas.process_finger_input(positions['middle_tip'], 20)
        
        # Handle index finger drawing (only when tip is above base)
        if positions['index_tip'] and positions['middle_tip'] and positions['middle_one']:
            # disable drawing when V gesture is detected
            if positions['middle_tip'][1] > positions['middle_one'][1]:
                self.canvas.process_finger_input(positions['index_tip'], 8)
            else:
                self.canvas.stop_drawing(positions['index_tip'])
    
    def _render_ui_info(self, img):
        """Render current color, thickness, and FPS information on image."""
        h = img.shape[0]
        
        # Current drawing settings
        color_name = next(name for name, color in self.canvas.colors.items() 
                         if color == self.canvas.drawing_color)
        cv2.putText(img, f"Color: {color_name}", (10, h - 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Thickness: {self.canvas.line_thickness}", (10, h - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # FPS display
        if config.SHOW_FPS:
            current_time = time.time()
            fps = 1 / (current_time - self.fps_time) if self.fps_time else 0
            self.fps_time = current_time
            cv2.putText(img, f'FPS: {int(fps)}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    def _handle_keyboard_input(self):
        """Process keyboard commands and return True to continue, False to quit."""
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            return False
        elif key == ord('i'):
            self.canvas.toggle_ui()
        
        return True
    
    def run(self):
        """Main application loop."""
        try:
            while True:
                # Capture and prepare frame
                success, img = self.cap.read()
                if not success:
                    print("Camera disconnected!")
                    break
                
                img = cv2.flip(img, 1)  # Mirror for intuitive interaction
                
                # Detect hands and faces
                img = self.hand_tracker.find_hands(img)
                hand_landmarks = self.hand_tracker.find_position(img)
                img, faces = self.face_tracker.find_faces(img)
                
                # Update canvas with face information
                self.canvas.update_faces(faces)
                if faces:
                    self.canvas.update_with_face_movement(faces[0]['center'])
                
                # Process hand input
                if hand_landmarks:
                    self.canvas.current_camera_img = img.copy()  # For saving
                    positions = self._extract_finger_positions(hand_landmarks)
                    self._draw_finger_indicators(img, positions)
                    self._process_hand_input(positions)
                else:
                    self.canvas.stop_drawing()
                
                # Render drawing and UI
                self.canvas.draw_on_canvas()
                img = cv2.addWeighted(img, 0.8, self.canvas.canvas, config.CANVAS_OPACITY, 0)
                img = self.canvas.draw_ui(img)
                
                # Add information overlay
                self._render_ui_info(img)
                
                # Handle keyboard input
                if not self._handle_keyboard_input():
                    break
                
                # Display result
                display_img = cv2.resize(img, config.WINDOW_SIZE)
                cv2.imshow(config.WINDOW_NAME, display_img)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Release resources and close windows."""
        self.cap.release()
        cv2.destroyAllWindows()
        print("Application closed successfully!")


def main():
    """Application entry point."""
    try:
        app = PaintLivecam()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()