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

SHOULDER_DISTANCE = 0.45  # Distanza tra le spalle in metri
ARM_LENGTH = 0.60  # Lunghezza del braccio in metri

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

# Funzione per calcolare la distanza euclidea tra due punti 3D in metri date come riferimento le spalle
def calculate_conversion_distances(p1, p2, right_shoulder, left_shoulder):
    shoulder_distance_px = round(np.sqrt((right_shoulder[0] - left_shoulder[0])**2 + (right_shoulder[1] - left_shoulder[1])**2),3) #distanza spalle in pixel 2D
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    #print(f"posizione polso destro x px: {p1[0]}") #Le coordinate sono a posto
    #print(f"posizione spalla destra x px: {p2[0]}")
    #print(f"posizione polso destro y px: {p1[1]}")
    #print(f"posizione spalla destra y px: {p2[1]}")
    distance_px = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    print(f"distance_px: {distance_px * conversion_factor}")
    return distance_px * conversion_factor


# Funzione principale per controllare se il braccio destro è alzato
def is_right_arm_raised(landmarks, w, h):
    try:
        # Ottieni coordinate di spalla e polso destro
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        # Converti in pixel
        right_shoulder_px = [right_shoulder.x * w, right_shoulder.y * h, right_shoulder.z]
        left_shoulder_px = [left_shoulder.x * w, left_shoulder.y * h, right_shoulder.z]
        right_wrist_px = [right_wrist.x * w, right_wrist.y * h, right_wrist.z]
        left_wrist_px = [left_wrist.x * w, left_wrist.y * h, left_wrist.z]
        #shoulder_y = right_shoulder_px[1]
        #wrist_y = right_wrist.y * h

        # Controlla se il polso è significativamente sopra la spalla e non è alzato il braccio sx
        if (calculate_conversion_distances(right_wrist_px, right_shoulder_px, right_shoulder_px, left_shoulder_px) > ARM_LENGTH) and (right_wrist_px[1] + 50 < right_shoulder_px[1]):  # Range di tolleranza (150 pixel)
            if(left_wrist_px[1] > left_shoulder_px[1]):
               return True
            else :
                return False
            
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

            # Controlla se il braccio destro è alzato e braccio sx abbassato
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
