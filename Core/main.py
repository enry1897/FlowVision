import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time

debug = False

from enum import Enum

# Inizializza MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

w = 640
h = 480

# Inizializza RealSense Pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, w, h, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, w, h, rs.format.z16, 30)

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

#global vars
# Inizializzazione delle variabili globali in un dizionario
body_points = {
    "right_shoulder": (0.0, 0.0, 0.0),
    "left_shoulder": (0.0, 0.0, 0.0),
    "right_hip": (0.0, 0.0, 0.0),
    "left_hip": (0.0, 0.0, 0.0),
    "right_wrist": (0.0, 0.0, 0.0),
    "left_wrist": (0.0, 0.0, 0.0),
    "right_shoulder_depth": 0.0,
    "left_shoulder_depth": 0.0,
    "right_wrist_depth": 0.0,
    "left_wrist_depth": 0.0,
    "right_shoulder_px": (0.0, 0.0, 0.0),
    "left_shoulder_px": (0.0, 0.0, 0.0),
    "right_wrist_px": (0.0, 0.0, 0.0),
    "left_wrist_px": (0.0, 0.0, 0.0),
    "left_hip_px": (0.0, 0.0, 0.0),
}

def update_body_point(body_point, new_value):
    if body_point in body_points:
        body_points[body_point] = new_value  # Aggiorna il valore
    else:
        print(f"Joint {body_point} not found!")

def display_all_joints():
    for joint, value in body_points.items():
        print(f"{joint}: {value}")

# Utilizzo TBR
#update_body_point("right_shoulder", (1.2, 3.4, 5.6))
#display_all_joints()


##FUNCTIONS

def getUpdatedLandmarks(myPoseLandmarks):
    update_body_point(body_points["right_shoulder"], myPoseLandmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER])
    update_body_point(body_points["left_shoulder"], myPoseLandmarks[mp_pose.PoseLandmark.LEFT_SHOULDER])
    update_body_point(body_points["right_hip"], myPoseLandmarks[mp_pose.PoseLandmark.RIGHT_HIP])
    update_body_point(body_points["left_hip"], myPoseLandmarks[mp_pose.PoseLandmark.LEFT_HIP])
    update_body_point(body_points["right_wrist"], myPoseLandmarks[mp_pose.PoseLandmark.RIGHT_WRIST])
    update_body_point(body_points["left_wrist"], myPoseLandmarks[mp_pose.PoseLandmark.LEFT_WRIST])

def getPixelBodyPoints():
    update_body_point(body_points["right_shoulder_px"],[body_points["right_shoulder"][0] * w, body_points["right_shoulder"][1] * h, body_points["right_shoulder"][2]])
    update_body_point(body_points["left_shoulder_px"],[body_points["left_shoulder"][0] * w, body_points["left_hip"][1] * h, body_points["right_shoulder"][2]])
    update_body_point(body_points["right_wrist_px"],[body_points["right_wrist"][0] * w, body_points["right_wrist"][1] * h, body_points["right_wrist"][2]])
    update_body_point(body_points["left_wrist_px"],[body_points["left_wrist"][0] * w, body_points["left_wrist"][1] * h, body_points["left_wrist"][2]])
    update_body_point(body_points["left_hip_px"],(int(body_points["left_hip"][0] * w), int(body_points["left_hip"][1] * h)))

# Funzione per calcolare la distanza tra due punti (in pixel)
def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

# Funzione per calcolare la distanza in 3D
def calculate_distance_3d(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)


# Funzione per calcolare la distanza euclidea tra due punti 3D in metri date come riferimento le spalle
def calculate_conversion_distances(p1, p2):
    global body_points
    shoulder_distance_px = round(np.sqrt((body_points["right_shoulder_px"][0] - body_points["left_shoulder_px"][0])**2 + (body_points["right_shoulder_px"][1] - body_points["left_shoulder_px"][1])**2),3) #distanza spalle in pixel 2D
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    #print(f"posizione polso destro x px: {p1[0]}") #Le coordinate sono a posto
    #print(f"posizione spalla destra x px: {p2[0]}")
    #print(f"posizione polso destro y px: {p1[1]}")
    #print(f"posizione spalla destra y px: {p2[1]}")
    distance_px = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    #print(f"distance_px: {distance_px * conversion_factor}")
    return distance_px * conversion_factor


# Funzione principale per controllare se il braccio destro è alzato e non è alzato il braccio sx --- TRACKING 1
def is_right_arm_raised():
    try:
        global body_points

        #getUpdatedLandmarks(my_landmarks)
        # Ottieni coordinate di spalla e polso destro
        #right_shoulder = my_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        #left_shoulder = my_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        #right_wrist = my_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        #left_wrist = my_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        # Converti in pixel
        #getPixelBodyPoints()
        #right_shoulder_px = [body_points["right_shoulder"][0] * w, body_points["right_shoulder"][1] * h, body_points["right_shoulder"][2]]
        #left_shoulder_px = [body_points["left_shoulder"][0] * w, body_points["left_hip"][1] * h, body_points["right_shoulder"][2]]
        #right_wrist_px = [body_points["right_wrist"][0] * w, body_points["right_wrist"][1] * h, body_points["right_wrist"][2]]
        #left_wrist_px = [body_points["left_wrist"][0] * w, body_points["left_wrist"][1] * h, body_points["left_wrist"][2]]
        #shoulder_y = right_shoulder_px[1]
        #wrist_y = body_points["right_wrist"][1] * h

        # Controlla se il polso è significativamente sopra la spalla e non è alzato il braccio sx
        if (calculate_conversion_distances(body_points["right_wrist_px"], body_points["right_shoulder_px"]) > ARM_LENGTH) and (body_points["right_wrist_px"][1] + 50 < body_points["right_shoulder_px"][1]):  # Range di tolleranza (150 pixel)
            return body_points["left_wrist_px"][1] > ["left_shoulder_px"][1]
            
    except IndexError:
        pass
    return False



# Funzione per rilevare se le mani sono sovrapposte sul cuore --- TRACKING 2 - CUORE
def check_hands_on_heart(pose_landmarks):
    try:
        global body_points

        # Coordinate chiave: spalle, polsi
        #update coordinates:
        #getUpdatedLandmarks(pose_landmarks)

        #right_shoulder = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        #left_shoulder = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        #right_wrist = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        #left_wrist = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        #left_hip = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]

        # Converti in pixel
        #getPixelBodyPoints()
        #right_shoulder_px = (int(body_points["right_shoulder"][0] * my_w), int(body_points["right_shoulder"][1] * my_h))
        #left_shoulder_px = (int(body_points["left_shoulder"][0] * my_w), int(body_points["left_hip"][1] * my_h))
        #right_wrist_px = (int(body_points["right_wrist"][0] * my_w), int(body_points["right_wrist"][1] * my_h))
        #left_wrist_px = (int(body_points["left_wrist"][0] * my_w), int(body_points["left_wrist"][1] * my_h))
        #left_hip_px = (int(body_points["left_hip"][0] * my_w), int(body_points["left_hip"][1] * my_h))

        if body_points["right_shoulder"][1] < body_points["right_wrist"][1] < body_points["left_hip"][1]:
            # Definiamo la zona del cuore come il centro tra le spalle
            #print("calcolo cuore")
            heart_x = (body_points["right_shoulder"][0] + body_points["left_shoulder"][0]) / 2
            heart_y = body_points["right_shoulder"][1] - ((body_points["right_shoulder"][1] - body_points["left_hip"][1]) / 4)  # Posizione tra le spalle, nella zona del petto

            # Zona del cuore in pixel
            heart_region = (int(heart_x * w), int(heart_y * h))

            # Calcola la distanza tra le mani e la zona del cuore
            right_wrist_distance = calculate_distance((body_points["right_wrist"][0] * w, body_points["right_wrist"][1] * h), heart_region)
            left_wrist_distance = calculate_distance((body_points["left_wrist"][0] * w, body_points["left_wrist"][1] * h), heart_region)

            # Se entrambe le mani sono abbastanza vicine alla zona del cuore, attiviamo una funzione
            return right_wrist_distance < HEART_REGION_TOLERANCE * w and left_wrist_distance < HEART_REGION_TOLERANCE * h

    except IndexError:
        pass
    return False



# Funzione per calcolare il livello proporzionale --- TRACKING 3 -- CO2
def calculate_level(my_depth_image):
    global body_points,prev_level
    try:
        #getUpdatedLandmarks(my_pose_landmarks) #verificare se da chiamare una volta sola nel main loop

        # Coordinate chiave: spalle, anche, polsi
        #right_shoulder = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        #left_shoulder = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        #right_hip = pose_landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        #left_hip = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        #right_wrist = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        #left_wrist = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        # Converti in pixel
        #getPixelBodyPoints()
        #right_shoulder_px = (int(body_points["right_shoulder"][0] * w), int(body_points["right_shoulder"][1] * h))
        #left_shoulder_px = (int(body_points["left_shoulder"][0] * w), int(body_points["left_hip"][1] * h))
        #right_wrist_px = (int(body_points["right_wrist"][0] * w), int(body_points["right_wrist"][1] * h))
        #left_wrist_px = (int(body_points["left_wrist"][0] * w), int(body_points["left_wrist"][1] * h))

        # Ottieni profondità dai frame di profondità
        right_shoulder_depth = my_depth_image[body_points["right_shoulder_px"][1], body_points["right_shoulder_px"][0]] * depth_scale
        left_shoulder_depth = my_depth_image[body_points["left_shoulder_px"][1], body_points["left_shoulder_px"][0]] * depth_scale
        right_wrist_depth = my_depth_image[body_points["right_wrist_px"][1], body_points["right_wrist_px"][0]] * depth_scale
        left_wrist_depth = my_depth_image[body_points["right_left_px"][1], body_points["right_left_px"][0]] * depth_scale

        # Coordinate 3D
        right_shoulder_3d = (body_points["right_shoulder"][0], body_points["right_shoulder"][1], right_shoulder_depth)
        left_shoulder_3d = (body_points["left_shoulder"][0], body_points["left_hip"][1], left_shoulder_depth)
        right_wrist_3d = (body_points["right_wrist"][0], body_points["right_wrist"][1], right_wrist_depth)
        left_wrist_3d = (body_points["left_wrist"][0], body_points["left_wrist"][1], left_wrist_depth)

        # Calcola la distanza 3D tra spalla e polso
        right_arm_length = calculate_distance_3d(right_shoulder_3d, right_wrist_3d)
        left_arm_length = calculate_distance_3d(left_shoulder_3d, left_wrist_3d)

        # Verifica che entrambe le braccia siano distese
        if right_arm_length < ARM_MIN_LENGTH or left_arm_length < ARM_MIN_LENGTH:
            myLevel = 0
            return

        # Altezza media delle mani
        avg_hand_height = (body_points["right_wrist"][1] + body_points["left_wrist"][1]) / 2

        # Altezza media delle spalle e delle anche
        avg_shoulder_height = (body_points["right_shoulder"][1] + body_points["left_hip"][1]) / 2
        avg_hip_height = (body_points["right_hip"][1] + body_points["left_hip"][1]) / 2

        # Calcolo della differenza di altezza tra i polsi
        wrist_height_diff = abs(body_points["right_wrist"][1] - body_points["left_wrist"][1])

        # Se non rileva entrambe le mani, il livello non può essere incrementato
        if not (right_arm_length >= ARM_MIN_LENGTH and left_arm_length >= ARM_MIN_LENGTH):
            myLevel = 0
            prev_level = myLevel
            return

        # Condizioni per aumentare il livello: entrambe le braccia devono essere sollevate sopra le anche,
        # distese, e le mani devono essere a livello simile
        if body_points["right_wrist"][1] < avg_hip_height and body_points["left_wrist"][1] < avg_hip_height:  # Le mani sono sopra le anche
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
            myLevel = min(new_level, max_level)  # Tronca il livello a max_level (10)
            prev_level = myLevel


    except IndexError:
        pass


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

            #update all local datas
            getUpdatedLandmarks(pose_results.pose_landmarks.landmark)
            getPixelBodyPoints()

            heart = 0
            # Controlla se le mani sono sovrapposte al cuore
            if check_hands_on_heart(pose_results.pose_landmarks.landmark):
                # Mostra il messaggio se le mani sono sovrapposte al cuore
                heart = 1
                
                cv2.putText(color_image, "Hands on Heart Detected!", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            print(f"heart: {heart}")


            # Controlla se il braccio destro è alzato e braccio sx abbassato
            landmarks = pose_results.pose_landmarks.landmark

            right_arm_high = 0

            if is_right_arm_raised():
                cv2.putText(color_image, "Right arm raised!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                print("Funzione attivata: braccio destro alzato!")
                right_arm_high = 1

            print(f"right_arm_high: {right_arm_high}")

            # Verifica che siano passati abbastanza secondi prima di calcolare il livello --- TRACKING 3 -- CO2
            if time.time() - initial_time > STABILITY_WAIT_TIME:
                # Calcola il livello
                calculate_level(pose_results.pose_landmarks.landmark)


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






















