import cv2
import numpy as np
import time
from picamera2 import Picamera2
from uiutils import Button,dog,display
from PIL import Image

button = Button()
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)

# Color range for the mode
color_lower = np.array([0, 43, 46])
color_upper = np.array([10, 255, 255])
mode = 1

font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(main={"format": "RGB888", "size": (320, 240)})
)
picam2.start()



def change_color():
    global color_lower, color_upper, mode
    
    color_ranges = [
        (np.array([0, 150, 100]), np.array([8, 255, 255])),   # red
        (np.array([35, 43, 46]), np.array([77, 255, 255])),  # green
        (np.array([100, 150, 100]), np.array([120, 255, 255])),  # blue
        (np.array([26, 43, 46]), np.array([34, 255, 255]))  # yellow
    ]
    
    mode = (mode % 4) + 1
    
    color_lower, color_upper = color_ranges[mode - 1]


# FPS counter
t_start = time.time()
fps = 0
color_x = 0
color_y = 0
color_radius = 0

while True:
    frame = picam2.capture_array() 
    frame_ = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_lower, color_upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    
    if len(cnts) > 0:
        cnt = max(cnts, key=cv2.contourArea)
        (color_x, color_y), color_radius = cv2.minEnclosingCircle(cnt)
        if color_radius > 10:
            cv2.circle(frame, (int(color_x), int(color_y)), int(color_radius), (255, 0, 255), 2)
            value_x = color_x - 160
            value_y = color_y - 120
            rider_x = value_x
            value_x = np.clip(value_x, -55, 55)
            value_y = np.clip(value_y, -75, 75)
            
           
            dog.attitude(['y', 'p'], [-value_x / 15, value_y / 15])

   
    cv2.putText(frame, "X:%d, Y:%d" % (int(color_x), int(color_y)), (40, 40), font, 0.8, (0, 255, 255), 3)
    
   
    fps += 1
    mfps = fps / (time.time() - t_start)
    cv2.putText(frame, "FPS " + str(int(mfps)), (40, 80), font, 0.8, (0, 255, 255), 3)

   
    b, g, r = cv2.split(frame)
    img = cv2.merge((r, g, b))
    
    colors = [red, green, blue, yellow]
    cv2.rectangle(img, (290, 10), (320, 40), colors[mode - 1], -1)
    
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)  
    
    if (cv2.waitKey(1) & 0xFF) == ord('q'):
        break
    if button.press_b():
        break
    if button.press_d():
        change_color()

picam2.stop()
