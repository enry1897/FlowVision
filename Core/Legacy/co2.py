import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time

# Inizializza MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Inizializza RealSense Pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Avvia la pipeline
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

# Parametri per il livello
max_level = 10  # Livello massimo
level = 0  # Livello iniziale
prev_level = 0  # Memorizza il livello precedente per l'isteresi

# Soglie per validare braccia distese
ARM_MIN_LENGTH = 0.45  # Lunghezza minima per considerare un braccio disteso (in metri)

# Tolleranza per la differenza di altezza tra i polsi
HAND_HEIGHT_TOLERANCE = 0.10  # Tolleranza maggiore, adesso è 10 cm

# Tempo di attesa iniziale per stabilizzare
STABILITY_WAIT_TIME = 1.0  # Tempo di attesa in secondi

# Isteresi per il livello
LEVEL_CHANGE_THRESHOLD = 1  # La quantità minima di cambiamento per modificare il livello

# Funzione per calcolare la distanza in 3D
def calculate_distance_3d(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)

# Funzione per calcolare il livello proporzionale
def calculate_level(pose_landmarks, w, h, depth_image):
    global level, prev_level
    try:
        # Coordinate chiave: spalle, anche, polsi
        right_shoulder = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_shoulder = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_hip = pose_landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_hip = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_wrist = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_wrist = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        # Converti in pixel
        right_shoulder_px = (int(right_shoulder.x * w), int(right_shoulder.y * h))
        left_shoulder_px = (int(left_shoulder.x * w), int(left_shoulder.y * h))
        right_wrist_px = (int(right_wrist.x * w), int(right_wrist.y * h))
        left_wrist_px = (int(left_wrist.x * w), int(left_wrist.y * h))

        # Ottieni profondità dai frame di profondità
        right_shoulder_depth = depth_image[right_shoulder_px[1], right_shoulder_px[0]] * depth_scale
        left_shoulder_depth = depth_image[left_shoulder_px[1], left_shoulder_px[0]] * depth_scale
        right_wrist_depth = depth_image[right_wrist_px[1], right_wrist_px[0]] * depth_scale
        left_wrist_depth = depth_image[left_wrist_px[1], left_wrist_px[0]] * depth_scale

        # Coordinate 3D
        right_shoulder_3d = (right_shoulder.x, right_shoulder.y, right_shoulder_depth)
        left_shoulder_3d = (left_shoulder.x, left_shoulder.y, left_shoulder_depth)
        right_wrist_3d = (right_wrist.x, right_wrist.y, right_wrist_depth)
        left_wrist_3d = (left_wrist.x, left_wrist.y, left_wrist_depth)

        # Calcola la distanza 3D tra spalla e polso
        right_arm_length = calculate_distance_3d(right_shoulder_3d, right_wrist_3d)
        left_arm_length = calculate_distance_3d(left_shoulder_3d, left_wrist_3d)

        # Verifica che entrambe le braccia siano distese
        if right_arm_length < ARM_MIN_LENGTH or left_arm_length < ARM_MIN_LENGTH:
            level = 0
            return

        # Altezza media delle mani
        avg_hand_height = (right_wrist.y + left_wrist.y) / 2

        # Altezza media delle spalle e delle anche
        avg_shoulder_height = (right_shoulder.y + left_shoulder.y) / 2
        avg_hip_height = (right_hip.y + left_hip.y) / 2

        # Calcolo della differenza di altezza tra i polsi
        wrist_height_diff = abs(right_wrist.y - left_wrist.y)

        # Se non rileva entrambe le mani, il livello non può essere incrementato
        if not (right_arm_length >= ARM_MIN_LENGTH and left_arm_length >= ARM_MIN_LENGTH):
            level = 0
            prev_level = level
            return

        # Condizioni per aumentare il livello: entrambe le braccia devono essere sollevate sopra le anche,
        # distese, e le mani devono essere a livello simile
        if right_wrist.y < avg_hip_height and left_wrist.y < avg_hip_height:  # Le mani sono sopra le anche
            if wrist_height_diff < HAND_HEIGHT_TOLERANCE:  # Le mani sono a livelli simili
                # Calcola il livello in base all'altezza delle mani rispetto alle anche
                normalized_height = (avg_hip_height - avg_hand_height) / (avg_hip_height - avg_shoulder_height * 0.5)
                new_level = int(normalized_height * max_level)  # Mappa a un livello tra 0 e max_level
            else:
                # Se le mani sono a livelli diversi ma non troppo, facciamo comunque incrementare il livello
                normalized_height = (avg_hip_height - avg_hand_height) / (avg_hip_height - avg_shoulder_height * 0.5)
                new_level = int(normalized_height * (max_level * 0.75))  # Meno del massimo
        else:
            new_level = 0  # Se le mani sono sotto le anche, livello 0

        # Applicare l'isteresi: il livello cambierà solo se la differenza con il livello precedente è significativa
        if abs(new_level - prev_level) >= LEVEL_CHANGE_THRESHOLD:
            level = min(new_level, max_level)  # Tronca il livello a max_level (10)
            prev_level = level


    except IndexError:
        pass

try:
    initial_time = time.time()  # Tempo di inizio
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        h, w, _ = color_image.shape

        pose_results = pose.process(rgb_image)

        if pose_results.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                color_image, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Verifica che siano passati abbastanza secondi prima di calcolare il livello
            if time.time() - initial_time > STABILITY_WAIT_TIME:
                # Calcola il livello
                calculate_level(pose_results.pose_landmarks.landmark, w, h, depth_image)

        # Mostra livello e stato
        cv2.putText(color_image, f"Level: {level}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if level == max_level else (0, 0, 255), 2)

        if level == max_level:
            cv2.putText(color_image, "Max Level Reached!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Hand and Body Tracking with Level", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except RuntimeError as e:
    print(f"Errore durante l'acquisizione dei frame: {e}")

pose.close()
pipeline.stop()
cv2.destroyAllWindows()




