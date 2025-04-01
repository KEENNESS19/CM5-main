from uiutils import dog, display, Button
from PIL import Image
import cv2, collections
import mediapipe as mp
from picamera2 import Picamera2

button = Button()

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (320, 240)}))
picam2.start()

# Initialize MediaPipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.4, min_tracking_confidence=0.4)

# History to store length of hand distance
length_history = collections.deque(maxlen=10)

def hand_detector(img):
    length = 0
    results = hands.process(img)

    # Check if hand landmarks are detected
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get landmarks for thumb and index finger
            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]
            
            h, w, _ = img.shape
          
            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            
          
            cv2.circle(img, (x1, y1), 5, (255, 0, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 5, (255, 0, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            
            
            length = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            length = int(length) if length > 0 else 0
    
   
    length_history.append(length)
    if length_history:
        length = int(sum(length_history) / len(length_history))

    return img, length


while True:

    img = picam2.capture_array()
    img = cv2.flip(img, 1)
    
   
    img, length = hand_detector(img)
    

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
 
    imgok = Image.fromarray(img)
    display.ShowImage(imgok)


    if length > 0:
        height = min(length / 500 * 40, 40) 
        dog.translation('z', 75 + height)
    else:
        dog.translation('z', 95)
    
    if button.press_b():
        dog.reset()
        break

picam2.stop()
