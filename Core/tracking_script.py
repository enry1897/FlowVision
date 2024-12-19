import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np

# Inizializza MediaPipe
mp_hands = mp.solutions.hands
mp_pose = mp.solutions.pose
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
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

# Tentiamo di avviare la pipeline
if not start_pipeline():
    print("Unable to start pipeline. Exiting...")
    exit(1)

# Ottieni il profilo di profondità
depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
print(f"Depth Scale: {depth_scale} meters per unit")

# Funzione per calcolare la distanza euclidea tra due punti 3D
def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

# Funzione principale per controllare se il braccio destro è alzato
def is_right_arm_raised(landmarks, w, h):
    try:
        # Ottieni coordinate di spalla e polso destro
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

        # Converti in pixel
        shoulder_y = right_shoulder.y * h
        wrist_y = right_wrist.y * h

        # Controlla se il polso è significativamente sopra la spalla
        if wrist_y < shoulder_y - 150:  # Range di tolleranza (50 pixel)
            return True
    except IndexError:
        pass
    return False

try:
    while True:
        # Cattura i frame di colore e profondità
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        # Converti i frame in formati utilizzabili
        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        h, w, _ = color_image.shape

        # Passa il frame di colore a MediaPipe
        rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(rgb_image)

        # Disegna lo skeleton tracking e controlla il braccio destro
        if pose_results.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                color_image, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Controlla se il braccio destro è alzato
            landmarks = pose_results.pose_landmarks.landmark
            if is_right_arm_raised(landmarks, w, h):
                cv2.putText(color_image, "Right arm raised!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                print("Funzione attivata: braccio destro alzato!")

        # Mostra il frame con i risultati
        cv2.imshow("Hand and Body Tracking with Depth", color_image)

        # Esci premendo 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except RuntimeError as e:
    print(f"Errore durante l'acquisizione dei frame: {e}")

# Rilascia le risorse
hands.close()
pose.close()
pipeline.stop()
cv2.destroyAllWindows()
