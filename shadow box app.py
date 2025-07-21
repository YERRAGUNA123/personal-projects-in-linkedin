import cv2
import mediapipe as mp
import random
import time

# Initialize MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Initialize Video Capture
cap = cv2.VideoCapture(0)

# Game variables
target_size = 60
score = 0
last_hit_time = 0
hit_cooldown = 1  # seconds

# Function to generate a new target
def generate_target():
    x = random.randint(target_size, 640 - target_size)
    y = random.randint(target_size, 480 - target_size)
    target_area = random.choice(['head', 'torso', 'body'])  # can be expanded later
    return (x, y, target_area)

# Function to check if finger touched the target
def is_touch_on_body(hand_pos, target_pos):
    x, y = hand_pos
    target_x, target_y, _ = target_pos
    distance = ((x - target_x) ** 2 + (y - target_y) ** 2) ** 0.5
    return distance < target_size

# Initialize first target
target_pos = generate_target()
target_color = (0, 255, 0)  # Green initially (punch target)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Mirror effect
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # MediaPipe detections
    results_pose = pose.process(rgb_frame)
    results_hands = hands.process(rgb_frame)

    index_finger_pos = None

    if results_hands.multi_hand_landmarks:
        for hand_landmarks in results_hands.multi_hand_landmarks:
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x = int(index_tip.x * frame.shape[1])
            y = int(index_tip.y * frame.shape[0])
            index_finger_pos = (x, y)

            # Draw hand landmarks
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Draw finger tip for visual debugging
            cv2.circle(frame, (x, y), 10, (255, 255, 0), -1)

    # Check for punch (only if finger is detected)
    if index_finger_pos and target_color == (0, 255, 0):
        if is_touch_on_body(index_finger_pos, target_pos):
            if time.time() - last_hit_time > hit_cooldown:
                print("Punch hit!")  # Debug
                score += 1
                target_color = (255, 0, 0)  # Switch to red
                target_pos = generate_target()
                last_hit_time = time.time()

    # If red, switch back to green after delay
    if target_color == (255, 0, 0) and time.time() - last_hit_time > 1.5:
        target_color = (0, 255, 0)

    # Draw target
    cv2.circle(frame, target_pos[:2], target_size, target_color, -1)

    # Draw score
    cv2.putText(frame, f'Score: {score}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Show the frame
    cv2.imshow('Shadowboxing Game', frame)

    # Exit on ESC key
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release everything
cap.release()
cv2.destroyAllWindows()
