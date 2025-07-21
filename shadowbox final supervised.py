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
target = None
dodge_start_time = None
dodge_duration = 2  # seconds to survive dodge

# Define actions with label, type, and color
actions = [
    ("Right Hook", "punch", (0, 255, 0)),
    ("Left Hook", "punch", (255, 255, 0)),
    ("Straight", "punch", (0, 255, 255)),
    ("Low Kick", "kick", (255, 0, 255)),
    ("High Kick", "kick", (255, 165, 0)),
    ("Dodge!", "dodge", (0, 0, 255))
]

# Function to generate a new target with spacing
def generate_target(prev_target=None, min_dist=100):
    while True:
        x = random.randint(target_size, 640 - target_size)
        y = random.randint(target_size, 480 - target_size)
        label, t_type, color = random.choice(actions)

        if prev_target:
            prev_x, prev_y = prev_target[:2]
            dist = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
            if dist < min_dist:
                continue  # retry if too close

        return (x, y, label, t_type, color)

# Function to check collision
def is_touch(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    distance = ((x1 - x2)**2 + (y1 - y2)**2)**0.5
    return distance < target_size

# Initialize first target
target = generate_target()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result_pose = pose.process(rgb)
    result_hands = hands.process(rgb)

    landmarks = {}

    # Pose landmarks
    if result_pose.pose_landmarks:
        for idx, lm in enumerate(result_pose.pose_landmarks.landmark):
            h, w, _ = frame.shape
            landmarks[f"pose_{idx}"] = (int(lm.x * w), int(lm.y * h))
        mp_drawing.draw_landmarks(frame, result_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # Hand landmarks
    if result_hands.multi_hand_landmarks:
        for hand_landmarks in result_hands.multi_hand_landmarks:
            for idx, lm in enumerate(hand_landmarks.landmark):
                h, w, _ = frame.shape
                landmarks[f"hand_{idx}"] = (int(lm.x * w), int(lm.y * h))
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Check interaction
    if target:
        x, y, label, t_type, color = target
        touched = False

        if t_type == "punch":
            for key in ["hand_8", "hand_12"]:
                if key in landmarks and is_touch(landmarks[key], (x, y)):
                    touched = True
                    break
        elif t_type == "kick":
            for key in ["pose_27", "pose_28"]:
                if key in landmarks and is_touch(landmarks[key], (x, y)):
                    touched = True
                    break
        elif t_type == "dodge":
            if dodge_start_time is None:
                dodge_start_time = time.time()

            # Flashing effect
            blink = int((time.time() * 4) % 2) == 0  # 4Hz blink rate

            if blink:
                cv2.circle(frame, (x, y), target_size, color, -1)
                cv2.putText(frame, label, (x - 30, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            for key in ["pose_0", "pose_11", "pose_12"]:
                if key in landmarks and is_touch(landmarks[key], (x, y)):
                    touched = True
                    break

            # If time passed and no touch → survived
            if time.time() - dodge_start_time > dodge_duration:
                print("✅ Dodged Successfully:", label)
                dodge_start_time = None
                target = generate_target(prev_target=target)
                last_hit_time = time.time()
                continue

        if touched and time.time() - last_hit_time > hit_cooldown:
            if t_type != "dodge":
                score += 1
                print("✅ Hit:", label)
            else:
                score -= 1
                print("❌ Failed to Dodge:", label)

            target = generate_target(prev_target=target)
            last_hit_time = time.time()
            dodge_start_time = None if t_type != "dodge" else time.time()

        # Draw non-dodge targets
        if t_type != "dodge":
            cv2.circle(frame, (x, y), target_size, color, -1)
            cv2.putText(frame, label, (x - 30, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw score
    cv2.putText(frame, f"Score: {score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Display the frame
    cv2.imshow("SlowMo Close Range Shadow Box (Fitness App)", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
