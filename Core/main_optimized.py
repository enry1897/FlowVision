import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time

# Initialize MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Initialize RealSense Pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Global Variables
data = {
    "right_shoulder": None,
    "left_shoulder": None,
    "right_wrist": None,
    "left_wrist": None,
    "right_hip": None,
    "left_hip": None,
    "right_shoulder_px": None,
    "left_shoulder_px": None,
    "right_wrist_px": None,
    "left_wrist_px": None,
    "right_hip_px": None,
    "left_hip_px": None,
}

w, h = 640, 480  # Global width and height
level = 0
prev_level = 0
SHOULDER_DISTANCE = 0.45  # Approximate real-world shoulder width in meters
ARM_MIN_LENGTH = 0.2  # Minimum arm length to consider it extended
HAND_HEIGHT_TOLERANCE = 0.1  # Height tolerance for hands to be at the same level
HEART_REGION_TOLERANCE = 0.10  # Tolerance for hands near the heart
LEVEL_CHANGE_THRESHOLD = 1  # Threshold to avoid frequent level changes
max_level = 10
ARM_LENGTH = 0.60  # Lunghezza del braccio in metri

def start_pipeline():
    try:
        pipeline.start(config)
        print("Pipeline started successfully.")
    except Exception as e:
        print(f"Error starting pipeline: {e}")
        return False
    return True

if not start_pipeline():
    print("Unable to start pipeline. Exiting...")
    exit(1)

depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
print(f"Depth Scale: {depth_scale} meters per unit")

### Functions to update global dictionary
def update_landmarks(pose_landmarks):
    """
    Update the coordinates of shoulders, wrists, and hips in the global dictionary.
    """
    global data
    data["right_shoulder"] = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    data["left_shoulder"] = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    data["right_wrist"] = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    data["left_wrist"] = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    data["right_hip"] = pose_landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    data["left_hip"] = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]

def update_pixel_coordinates(w, h):
    """
    Update the pixel coordinates of shoulders, wrists, and hips in the global dictionary.
    """
    global data
    data["right_shoulder_px"] = [data["right_shoulder"].x * w, data["right_shoulder"].y * h, data["right_shoulder"].z]
    data["left_shoulder_px"] = [data["left_shoulder"].x * w, data["left_shoulder"].y * h, data["left_shoulder"].z]
    data["right_wrist_px"] = [data["right_wrist"].x * w, data["right_wrist"].y * h, data["right_wrist"].z]
    data["left_wrist_px"] = [data["left_wrist"].x * w, data["left_wrist"].y * h, data["left_wrist"].z]
    data["right_hip_px"] = [data["right_hip"].x * w, data["right_hip"].y * h, data["right_hip"].z]
    data["left_hip_px"] = [data["left_hip"].x * w, data["left_hip"].y * h, data["left_hip"].z]

### Utility Functions
def calculate_distance(p1, p2):
    """Calculate the Euclidean distance between two points in 2D."""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def calculate_conversion_distances(p1, p2):
    """Calculate normalized distance between two points based on shoulder width."""
    shoulder_distance_px = round(calculate_distance(data["right_shoulder_px"], data["left_shoulder_px"]),3)
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    distance_px = round(calculate_distance(p1, p2),3)
    return distance_px * conversion_factor

def is_right_arm_raised(right_shoulder_px, right_wrist_px):
    global ARM_LENGTH
    """Check if the right arm is raised based on wrist position relative to shoulder."""
    #return right_wrist_px[1] < right_shoulder_px[1]
    if (calculate_conversion_distances(right_wrist_px, right_shoulder_px) > ARM_LENGTH) and (right_wrist_px[1] + 50 < right_shoulder_px[1]):  # Range di tolleranza (150 pixel)
        return right_wrist_px[1] > right_shoulder_px[1]

def is_left_arm_raised(left_shoulder_px, left_wrist_px):
    """Check if the left arm is raised based on wrist position relative to shoulder."""
    return left_wrist_px[1] < left_shoulder_px[1]

def calculate_hip_distance():
    """Calculate the real-world distance between hips using the conversion factor."""
    hip_distance_px = calculate_distance(data["right_hip_px"], data["left_hip_px"])
    shoulder_distance_px = calculate_distance(data["right_shoulder_px"], data["left_shoulder_px"])
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    return hip_distance_px * conversion_factor

def check_hands_on_heart():
    try:
        right_wrist_px = data["right_wrist_px"]
        left_wrist_px = data["left_wrist_px"]
        right_shoulder_px = data["right_shoulder_px"]
        left_shoulder_px = data["left_shoulder_px"]
        left_hip_px = data["left_hip_px"]
        right_shoulder = data["right_shoulder"]
        right_wrist = data["right_wrist"]
        left_hip = data["left_hip"]

        if right_shoulder.y < right_wrist.y < left_hip.y:
            # Calculate heart region based on shoulder and hip position
            heart_x = (right_shoulder_px[0] + left_shoulder_px[0]) / 2
            heart_y = right_shoulder_px[1] - ((right_shoulder_px[1] - left_hip_px[1]) / 4)
            heart_region = (heart_x * w, heart_y * h)

            # Calculate distances from wrists to the heart region
            right_wrist_distance = calculate_distance((right_wrist_px[0], right_wrist_px[1]), heart_region)
            left_wrist_distance = calculate_distance((left_wrist_px[0], left_wrist_px[1]), heart_region)

            # Check if both hands are close to the heart region
            if right_wrist_distance < HEART_REGION_TOLERANCE * w and left_wrist_distance < HEART_REGION_TOLERANCE * w:
                return True
    except IndexError:
        pass
    return False

def calculate_level(pose_landmarks, my_w, my_h, my_depth_image):
    global level, prev_level
    try:
        update_landmarks(pose_landmarks)
        update_pixel_coordinates(my_w, my_h)

        right_arm_length = calculate_conversion_distances(data["right_shoulder_px"], data["right_wrist_px"])
        left_arm_length = calculate_conversion_distances(data["left_shoulder_px"], data["left_wrist_px"])

        #vedere come implementare la distanza 3D

        # Ottieni profondità dai frame di profondità
        #right_shoulder_depth = my_depth_image[right_shoulder_px[1], right_shoulder_px[0]] * depth_scale
        #left_shoulder_depth = my_depth_image[left_shoulder_px[1], left_shoulder_px[0]] * depth_scale
        #right_wrist_depth = my_depth_image[right_wrist_px[1], right_wrist_px[0]] * depth_scale
        #left_wrist_depth = my_depth_image[left_wrist_px[1], left_wrist_px[0]] * depth_scale

        # Coordinate 3D
        #right_shoulder_3d = (right_shoulder.x, right_shoulder.y, right_shoulder_depth)
        #left_shoulder_3d = (left_shoulder.x, left_shoulder.y, left_shoulder_depth)
        #right_wrist_3d = (right_wrist.x, right_wrist.y, right_wrist_depth)
        #left_wrist_3d = (left_wrist.x, left_wrist.y, left_wrist_depth)

        # Calcola la distanza 3D tra spalla e polso
        #right_arm_length = calculate_distance_3d(right_shoulder_3d, right_wrist_3d)
        #left_arm_length = calculate_distance_3d(left_shoulder_3d, left_wrist_3d)

        if right_arm_length < ARM_MIN_LENGTH or left_arm_length < ARM_MIN_LENGTH:
            level = max(0, level - 1)
        elif is_right_arm_raised(data["right_shoulder_px"], data["right_wrist_px"]) and is_left_arm_raised(data["left_shoulder_px"], data["left_wrist_px"]):
            level = min(max_level, level + 1)

        if abs(level - prev_level) > LEVEL_CHANGE_THRESHOLD:
            prev_level = level
            print(f"Level updated to: {level}")
    except IndexError:
        pass

# Main loop
try:
    initial_time = time.time()  # Tempo di inizio
    STABILITY_WAIT_TIME = 5  # Tempo di attesa prima di calcolare il livello
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        # Convert color image to RGB
        rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        # Process the image and find pose landmarks
        results = pose.process(rgb_image)

        if results.pose_landmarks:
            calculate_level(results.pose_landmarks.landmark, w, h, depth_image)

        heart = 0
        # Controlla se le mani sono sovrapposte al cuore
        if check_hands_on_heart():
            # Mostra il messaggio se le mani sono sovrapposte al cuore
            heart = 1

            cv2.putText(color_image, "Hands on Heart Detected!", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        print(f"heart: {heart}")


        # Controlla se il braccio destro è alzato e braccio sx abbassato
        landmarks = results.pose_landmarks.landmark

        right_arm_high = 0

        if is_right_arm_raised(landmarks, w, h):
            cv2.putText(color_image, "Right arm raised!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print("Funzione attivata: braccio destro alzato!")
            right_arm_high = 1

        print(f"right_arm_high: {right_arm_high}")

        # Verifica che siano passati abbastanza secondi prima di calcolare il livello --- TRACKING 3 -- CO2
        if time.time() - initial_time > STABILITY_WAIT_TIME:
            # Calcola il livello
            calculate_level(results.pose_landmarks.landmark, w, h, depth_image)


        # Mostra livello e stato --- TRACKING 3 -- CO2

        cv2.putText(color_image, f"Level: {level}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if level == max_level else (0, 0, 255), 2)

        if level == max_level:
            cv2.putText(color_image, "Max Level Reached!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display the image
        cv2.imshow('Pose Tracking', color_image)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
