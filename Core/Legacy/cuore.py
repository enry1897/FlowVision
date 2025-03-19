import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np

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

# Parametri per il rilevamento delle mani sul cuore
HEART_REGION_TOLERANCE = 0.10  # Tolleranza per la sovrapposizione con il cuore (percentuale della larghezza dell'immagine)

# Funzione per calcolare la distanza tra due punti (in pixel)
def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

# Funzione per rilevare se le mani sono sovrapposte sul cuore
def check_hands_on_heart(pose_landmarks, w, h):
    try:
        # Coordinate chiave: spalle, polsi
        right_shoulder = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_shoulder = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_wrist = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_wrist = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        left_hip = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]

        # Converti in pixel
        right_shoulder_px = (int(right_shoulder.x * w), int(right_shoulder.y * h))
        left_shoulder_px = (int(left_shoulder.x * w), int(left_shoulder.y * h))
        right_wrist_px = (int(right_wrist.x * w), int(right_wrist.y * h))
        left_wrist_px = (int(left_wrist.x * w), int(left_wrist.y * h))
        left_hip_px = (int(left_hip.x * w), int(left_hip.y * h))

        if right_wrist.y > right_shoulder.y and right_wrist.y < left_hip.y:
            # Definiamo la zona del cuore come il centro tra le spalle
            print("calcolo cuore")
            heart_x = (right_shoulder.x + left_shoulder.x) / 2
            heart_y = (right_shoulder.y) - ((right_shoulder.y - left_hip.y) / 4 )  # Posizione tra le spalle, nella zona del petto

            # Zona del cuore in pixel
            heart_region = (int(heart_x * w), int(heart_y * h))

            # Calcola la distanza tra le mani e la zona del cuore
            right_wrist_distance = calculate_distance((right_wrist.x * w, right_wrist.y * h), heart_region)
            left_wrist_distance = calculate_distance((left_wrist.x * w, left_wrist.y * h), heart_region)

            # Se entrambe le mani sono abbastanza vicine alla zona del cuore, attiviamo una funzione
            if right_wrist_distance < HEART_REGION_TOLERANCE * w and left_wrist_distance < HEART_REGION_TOLERANCE * w:
                return True  # Le mani sono sovrapposte al cuore
            else:
                return False

    except IndexError:
        pass
    return False

try:
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

            # Controlla se le mani sono sovrapposte al cuore
            if check_hands_on_heart(pose_results.pose_landmarks.landmark, w, h):
                # Mostra il messaggio se le mani sono sovrapposte al cuore
                cv2.putText(color_image, "Hands on Heart Detected!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Mostra l'immagine risultante
        cv2.imshow("Hand and Body Tracking with Heart Detection", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except RuntimeError as e:
    print(f"Errore durante l'acquisizione dei frame: {e}")

pose.close()
pipeline.stop()
cv2.destroyAllWindows()
