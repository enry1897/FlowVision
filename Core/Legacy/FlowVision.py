import cv2
import mediapipe as mp

import pyrealsense2 as rs
import numpy as np
import time
from pythonosc.udp_client import SimpleUDPClient

# Inizializza MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Inizializza RealSense Pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Configure OSC Client Address and Port
ip = "127.0.0.1" #localhost
port1 = 7700  #port for processing


# Create OSC Client
client = SimpleUDPClient(ip, port1)


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

### VARIABLES

## Parametri per il rilevamento delle mani sul cuore TRACKING 2 - CUORE

HEART_REGION_TOLERANCE = 0.10  # Tolleranza per la sovrapposizione con il cuore (percentuale della larghezza dell'immagine)
SHOULDER_DISTANCE = 0.45  # Distanza tra le spalle in metri
ARM_LENGTH = 0.60  # Lunghezza del braccio in metri

## Parametri per il livello TRACKING 3 -- CO2

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


##FUNCTIONS


# Funzione per calcolare la distanza tra due punti (in pixel)
def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# Funzione per calcolare la distanza in 3D
def calculate_distance_3d(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)


# Funzione per calcolare la distanza euclidea tra due punti 3D in metri date come riferimento le spalle
def calculate_conversion_distances(p1, p2, right_shoulder, left_shoulder):
    shoulder_distance_px = round(
        np.sqrt((right_shoulder[0] - left_shoulder[0]) ** 2 + (right_shoulder[1] - left_shoulder[1]) ** 2),
        3)  # distanza spalle in pixel 2D
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    # print(f"posizione polso destro x px: {p1[0]}") #Le coordinate sono a posto
    # print(f"posizione spalla destra x px: {p2[0]}")
    # print(f"posizione polso destro y px: {p1[1]}")
    # print(f"posizione spalla destra y px: {p2[1]}")
    distance_px = np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    # print(f"distance_px: {distance_px * conversion_factor}")
    return distance_px * conversion_factor


# Funzione principale per controllare se il braccio destro è alzato e non è alzato il braccio sx --- TRACKING 1
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

        # Controlla se il polso destro è sopra la spalla destra e il sinistro non è alzato
        if (
            right_wrist_px[1] < right_shoulder_px[1]  # Mano destra sopra la spalla
            and left_wrist_px[1] > left_shoulder_px[1]  # Mano sinistra sotto la spalla
        ):
            return True

    except IndexError:
        pass
    return False



# Funzione per rilevare se le mani sono sovrapposte sul cuore --- TRACKING 2 - CUORE
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
            # print("calcolo cuore")
            heart_x = (right_shoulder.x + left_shoulder.x) / 2
            heart_y = (right_shoulder.y) - (
                        (right_shoulder.y - left_hip.y) / 4)  # Posizione tra le spalle, nella zona del petto

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


# Funzione per calcolare il livello proporzionale --- TRACKING 3 -- CO2
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

        # Calcola la distanza 2D tra spalla e polso
        right_arm_length = calculate_conversion_distances(right_wrist_px, right_shoulder_px, right_shoulder_px, left_shoulder_px)
        left_arm_length = calculate_conversion_distances(left_wrist_px, left_shoulder_px, right_shoulder_px, left_shoulder_px)

        # Verifica che entrambe le braccia siano distese
        if right_arm_length < ARM_LENGTH or left_arm_length < ARM_LENGTH:
            level = 0
            print("Braccia non distese")
            return

        # Altezza media delle mani
        avg_hand_height = (right_wrist.y + left_wrist.y) / 2

        # Altezza media delle spalle e delle anche
        avg_shoulder_height = (right_shoulder.y + left_shoulder.y) / 2
        avg_hip_height = (right_hip.y + left_hip.y) / 2

        # Calcolo della differenza di altezza tra i polsi
        wrist_height_diff = abs(right_wrist.y - left_wrist.y)

        # Condizioni per aumentare il livello
        if (
            right_wrist.y < avg_hip_height and left_wrist.y < avg_hip_height
            and wrist_height_diff < HAND_HEIGHT_TOLERANCE
        ):  # Entrambe le mani sopra le anche
            normalized_height = (avg_hip_height - avg_hand_height) / (avg_hip_height - avg_shoulder_height * 0.5)
            new_level = min(int(normalized_height * max_level), max_level)  # Mappa a livello tra 0 e max_level
        else:
            # Se le mani non soddisfano i criteri, resetta il livello
            new_level = 0

        # Isteresi per il cambio di livello
        if abs(new_level - prev_level) >= LEVEL_CHANGE_THRESHOLD:
            level = new_level
            prev_level = level

    except IndexError:
        pass


# OSC Functions
    
def send_number_bilnders():
    client.send_message("/blinders", number_to_send_blinders)
    print(f"Sending a number blinders: {number_to_send_blinders}")

def send_number_lights():
    client.send_message("/lights", number_to_send_light)
    print(f"Sending a number light: {number_to_send_light}")

def send_number_fire_machine():
    client.send_message("/fireMachine", number_to_send_fire_machine)
    print(f"Sending a number fire machine: {number_to_send_fire_machine}")



# MAIN LOOP


try:
    initial_time = time.time()  # Tempo di inizio
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

            heart = 0
            # Controlla se le mani sono sovrapposte al cuore
            if check_hands_on_heart(pose_results.pose_landmarks.landmark, w, h):
                # Mostra il messaggio se le mani sono sovrapposte al cuore
                heart = 1

                cv2.putText(color_image, "Hands on Heart Detected!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            number_to_send_light = heart
            send_number_lights()
            print(f"heart: {heart}")

            # Controlla se il braccio destro è alzato e braccio sx abbassato
            landmarks = pose_results.pose_landmarks.landmark

            right_arm_high = 0

            # Verifica se il braccio destro è alzato
            right_arm_high = is_right_arm_raised(pose_results.pose_landmarks.landmark, w, h)
            if right_arm_high:
                print("Funzione attivata: braccio destro alzato!")
                cv2.putText(color_image, "Right arm raised!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                right_arm_high = 1
                
            number_to_send_blinders = int(right_arm_high)
            send_number_bilnders()
            print(f"right_arm_high: {right_arm_high}")


            # Calcola il livello solo se il braccio destro non è alzato --- TRACKING 3 -- CO2
            if not right_arm_high and time.time() - initial_time > STABILITY_WAIT_TIME:
                calculate_level(pose_results.pose_landmarks.landmark, w, h, depth_image)
            
            number_to_send_fire_machine = level
            send_number_fire_machine()

           

        # Mostra livello e stato --- TRACKING 3 -- CO2

        cv2.putText(color_image, f"Level: {level}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if level == max_level else (0, 0, 255), 2)

        if level == max_level:
            cv2.putText(color_image, "Max Level Reached!", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Mostra l'immagine risultante
        cv2.imshow("Hand and Body Tracking Detection", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


except RuntimeError as e:
    print(f"Errore durante l'acquisizione dei frame: {e}")

pose.close()
pipeline.stop()
cv2.destroyAllWindows()
