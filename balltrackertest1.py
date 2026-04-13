import argparse
import time
from collections import deque

import cv2
import imutils
import numpy as np
from picamera2 import Picamera2

def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--buffer", type=int, default=64,
        help="max buffer size")
    args = vars(ap.parse_args())

    # --- NEW: Color Selection Menu ---
    color_options = {
        "1": {"name": "Yellow", "lower": (20, 100, 100), "upper": (30, 255, 255)},
        "2": {"name": "Green",  "lower": (35, 100, 100),  "upper": (85, 255, 255)},
        "3": {"name": "Blue",   "lower": (100, 150, 0),   "upper": (140, 255, 255)},
        "4": {"name": "Orange", "lower": (10, 100, 20),   "upper": (25, 255, 255)},
        "5": {"name": "Black",  "lower": (0, 0, 0),       "upper": (179, 255, 50)},
        "6": {"name": "Neon", "lower": (24, 100, 100), "upper": (44, 255, 255)}
    }

    print("Select the color of the ball you want to track:")
    for key, value in color_options.items():
        print(f"[{key}] {value['name']}")

    choice = input("Enter the number corresponding to your color: ")
    
    # Validate user input
    while choice not in color_options:
        print("Invalid selection.")
        choice = input("Please enter a valid number from the list above: ")

    selected_color = color_options[choice]
    colorLower = selected_color["lower"]
    colorUpper = selected_color["upper"]
    print(f"\nConfiguration set! Tracking the {selected_color['name']} ball.\n")
    # ---------------------------------

    pts = deque(maxlen=args["buffer"])

    # Initialize Picamera2
    picam2 = Picamera2()
    
    # Configure the camera for video/array capture
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    
    # Allow camera to warm up
    time.sleep(2.0)

    print("Tracking is running. Press 'q' in the OpenCV window or Ctrl+C to stop.")

    try:
        while True:
            # Capture frame-by-frame as a numpy array
            frame = picam2.capture_array()
            
            # capture_array() typically returns RGB, so convert to BGR for OpenCV
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # resize the frame, and perform a vertical flip as requested by original picamera script
            frame = imutils.resize(frame, width=600)
            frame = cv2.flip(frame, 0) # vertical flip
            
            h, w = frame.shape[:2]
                
            # blur it, and convert it to the HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # construct a mask for the color, then perform
            # a series of dilations and erosions
            mask = cv2.inRange(hsv, colorLower, colorUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            
            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)[-2]
            center = None
            
            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                if M["m00"] > 0:
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                
                # only proceed if the radius meets a minimum size
                if radius > 10:
                    # Draw the circle and centroid on the frame in RED (BGR: 0, 0, 255)
                    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 0, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
            
            # update the points queue
            pts.appendleft(center)
            
            # loop over the set of tracked points to draw trail
            for i in range(1, len(pts)):
                if pts[i - 1] is None or pts[i] is None:
                    continue
                thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
                
            # --- SHOW CURRENT COORDINATES (TOP RIGHT & TERMINAL) ---
            if center is not None:
                coord_text = f"X:{center[0]:03d} Y:{center[1]:03d}"
                
                # Print to terminal to see calculation speed
                print(f"Calculated: {coord_text}") 
                
                # Calculate text size to align it properly to the right
                text_size = cv2.getTextSize(coord_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = w - text_size[0] - 10
                cv2.putText(frame, coord_text, (text_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0, 0, 255), 2)
            else:
                # Print to terminal when no ball is found
                print("Calculated: No Ball")
                
                text_size = cv2.getTextSize("No Ball", cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = w - text_size[0] - 10
                cv2.putText(frame, "No Ball", (text_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0, 0, 255), 2)
                            
            # show the frame to our screen
            cv2.imshow("Tracking", frame)
            key = cv2.waitKey(1) & 0xFF
            
            # if the 'q' key is pressed, stop the loop
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        # cleanup the camera and close any open windows
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
