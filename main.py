import cv2
import time
import numpy as np
import os
from datetime import datetime

import configurations as config
from drawing_canvas import DrawingCanvas
from face_tracker import FaceTracker
from hand_tracker import HandTracker

def main():
    """Main function to run the application."""
    # Initialize video capture
    cap = cv2.VideoCapture(1)
    
    # Get video dimensions
    success, img = cap.read()
    if not success:
        print("Failed to capture image from camera.")
        return
    
    h, w, c = img.shape
    
    # Initialize modules
    hand_tracker = HandTracker()
    face_detector = FaceTracker()
    drawing_canvas = DrawingCanvas(w, h)
    
    # Set up window with desired size
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_NAME, config.WINDOW_SIZE[0], config.WINDOW_SIZE[1])
    
    # Display instructions
    print("\nFinger Drawing App Instructions:")
    print("--------------------------------")
    print("- Draw with your index finger (tip must be above base)")
    print("- Click buttons with your pinky finger")
    print("- Press 'i' to show/hide UI elements")
    print("- Press '+' to increase window scale")
    print("- Press '-' to decrease window scale")
    print("- Press 'q' to quit")
    print("- Press 's' to save a screenshot")
    print("--------------------------------\n")
    
    # Main loop
    pTime = 0
    scale_factor = config.SCALE_FACTOR
    
    while True:
        # Read frame from camera
        success, img = cap.read()
        if not success:
            print("Failed to capture image from camera.")
            break
        
        # Flip the image horizontally for a more intuitive experience
        img = cv2.flip(img, 1)
        
        # Scale the image if needed
        if scale_factor != 1.0:
            scaled_width = int(img.shape[1] * scale_factor)
            scaled_height = int(img.shape[0] * scale_factor)
            img = cv2.resize(img, (scaled_width, scaled_height))
        
        # Find hands
        img = hand_tracker.find_hands(img)
        hand_landmarks = hand_tracker.find_position(img)
        
        # Find faces
        img, faces = face_detector.find_faces(img)
        face_center = faces[0]['center'] if faces else None
        
        # Update face information for the drawing canvas
        drawing_canvas.update_faces(faces)
        
        # Check if drawings are near face and adjust face-following lines
        if faces and drawing_canvas.check_drawing_near_face(faces[0]):
            drawing_canvas.adjust_drawings_to_face(face_center)
        
        # Process hand landmarks
        if hand_landmarks:
            # Index finger tip and base landmarks
            index_tip = None
            index_base = None
            # Pinky finger tip for button interactions
            pinky_tip = None
            
            for lm in hand_landmarks:
                # Index finger tip is landmark 8
                if lm[0] == 8:
                    index_tip = (lm[1], lm[2])
                    # Draw a circle at the tip
                    cv2.circle(img, index_tip, 10, (255, 0, 255), cv2.FILLED)
                
                # Index finger base (MCP) is landmark 5
                if lm[0] == 5:
                    index_base = (lm[1], lm[2])
                
                # Pinky tip is landmark 20
                if lm[0] == 20:
                    pinky_tip = (lm[1], lm[2])
                    # Draw a circle at the pinky tip
                    cv2.circle(img, pinky_tip, 8, (0, 255, 255), cv2.FILLED)
            
            # Check for button interactions with pinky finger
            if pinky_tip:
                # Store current camera image in drawing canvas for saving
                drawing_canvas.current_camera_img = img.copy()
                drawing_canvas.check_button_press(pinky_tip, 20)
            
            # Update button cooldown
            drawing_canvas.update_cooldown()
            
            # Check if drawing should be enabled
            if index_tip and index_base:
                # Drawing is enabled if tip y is less than base y (tip is above base)
                if index_tip[1] < index_base[1]:
                    if not drawing_canvas.is_drawing:
                        drawing_canvas.start_drawing(index_tip)
                    else:
                        drawing_canvas.continue_drawing(index_tip)
                else:
                    # Pass the last drawing point when stopping
                    drawing_canvas.stop_drawing(index_tip)
        else:
            # Stop drawing if no hands detected
            drawing_canvas.stop_drawing()
        
        # Draw the canvas onto the image
        drawing_canvas.draw_on_canvas()
        
        # Resize canvas to match current image size if needed
        if scale_factor != 1.0:
            canvas_resized = cv2.resize(drawing_canvas.canvas, (img.shape[1], img.shape[0]))
            img = cv2.addWeighted(img, 0.8, canvas_resized, config.CANVAS_OPACITY, 0)
        else:
            img = cv2.addWeighted(img, 0.8, drawing_canvas.canvas, config.CANVAS_OPACITY, 0)
        
        # Draw buttons on the image
        img = drawing_canvas.draw_buttons(img)
        
        # Display info about drawing color and thickness
        color_name = [c for c, v in drawing_canvas.colors.items() if v == drawing_canvas.drawing_color][0]
        cv2.putText(img, f"Color: {color_name}", 
                   (10, img.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Thickness: {drawing_canvas.line_thickness}", 
                   (10, img.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display face following mode
        mode_color = (0, 255, 0) if drawing_canvas.current_face_mode == "following" else (0, 0, 255)
        mode_text = f"Mode: {drawing_canvas.current_face_mode.upper()}"
        cv2.putText(img, mode_text, 
                   (10, img.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        
        # Display FPS
        if config.SHOW_FPS:
            cTime = time.time()
            fps = 1 / (cTime - pTime) if 'pTime' in locals() else 0
            pTime = cTime
            
            cv2.putText(img, f'FPS: {int(fps)}', 
                      config.FPS_POSITION, 
                      cv2.FONT_HERSHEY_SIMPLEX, 
                      config.FPS_FONT_SCALE, 
                      config.FPS_COLOR, 
                      config.FPS_THICKNESS)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        # Toggle UI visibility when 'i' is pressed
        if key == ord('i'):
            drawing_canvas.toggle_ui_visibility()
        
        # Increase scale factor when '+' is pressed
        elif key == ord('+') or key == ord('='):  # = is on the same key as + without shift
            scale_factor += 0.1
            print(f"Scale factor increased to {scale_factor:.1f}")
            
        # Decrease scale factor when '-' is pressed
        elif key == ord('-'):
            scale_factor = max(0.5, scale_factor - 0.1)  # Don't go below 0.5
            print(f"Scale factor decreased to {scale_factor:.1f}")
        
        # Save screenshot when 's' is pressed
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            cv2.imwrite(filename, img)
            print(f"Screenshot saved as {filename}")
        
        # Quit application when 'q' is pressed
        elif key == ord('q'):
            break
        
        # Resize the image to fit the window
        display_img = cv2.resize(img, config.WINDOW_SIZE)
        
        # Display the image
        cv2.imshow(config.WINDOW_NAME, display_img)
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()