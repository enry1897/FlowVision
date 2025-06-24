import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time
from pythonosc.udp_client import SimpleUDPClient
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import threading
import queue # Importa il modulo queue

# -----------------------------------------------------------------------------
# Load ML models
# -----------------------------------------------------------------------------
model_hand = load_model('ML/modello_Python_aggiornato.h5')
model_cuoricini = load_model('ML/cuoricini_ep_40.h5')

# -----------------------------------------------------------------------------
# Initialise MediaPipe solutions
# -----------------------------------------------------------------------------
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

# -----------------------------------------------------------------------------
# Intel RealSense pipeline
# -----------------------------------------------------------------------------
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

ctx = rs.context()
print(f"{len(ctx.query_devices())} RealSense device(s) found.")

depth_scale = None  # will be filled after pipeline start

# -----------------------------------------------------------------------------
# OSC configuration
# -----------------------------------------------------------------------------
IP_LIGHTS = "192.168.1.34"   # light system
IP_RPI    = "192.168.1.19"   # raspberry‑pi side
PORT_OSC  = 8100

client_lights = SimpleUDPClient(IP_LIGHTS, PORT_OSC)
client_rpi    = SimpleUDPClient(IP_RPI,  PORT_OSC)

# -----------------------------------------------------------------------------
# Hand‑on‑heart (tracking‑2) constants
# -----------------------------------------------------------------------------
HEART_REGION_TOLERANCE   = 0.10  # % of image width
SHOULDER_DISTANCE        = 0.45  # m
ARM_LENGTH               = 0.60  # m
CLOSENESS_WRISTS_TOLERANCE = 0.10
SIDE_FALLBACK_HAND       = 160   # px

# Tracking‑3 (CO₂) constants
MAX_LEVEL              = 10
ARM_MIN_LENGTH         = 0.45     # m
HAND_HEIGHT_TOLERANCE  = 0.10     # ~10 cm
STABILITY_WAIT_TIME    = 1.0      # s
LEVEL_CHANGE_THRESHOLD = 1
HYSTERESIS_FRAMES      = 10

# -----------------------------------------------------------------------------
# Globals for tracking‑3 hysteresis
# -----------------------------------------------------------------------------
level          = 0  # current level
_prev_level    = 0
_stable_count  = 0
_last_level    = 0

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def calculate_distance(p1, p2):
    """2‑D Euclidean distance (pixels)."""
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

def calculate_conversion_distances(p1, p2, right_shoulder, left_shoulder):
    """Return 2‑D distance in **metres** between *p1* / *p2* given pixel reference
    distance between shoulders and real‑world SHOULDER_DISTANCE."""
    shoulder_distance_px = np.hypot(right_shoulder[0] - left_shoulder[0],
                                    right_shoulder[1] - left_shoulder[1])
    conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1]) * conversion_factor

def preprocess_hand_roi(hand_roi: np.ndarray, target_size: int = 120) -> np.ndarray:
    """Enhance ROI locally and pad to *target_size*×*target_size*."""
    lab = cv2.cvtColor(hand_roi, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(lab)
    cl = cv2.createCLAHE(3.0, (8, 8)).apply(l)
    enhanced = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_Lab2BGR)
    enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # Sharpen
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    enhanced = cv2.filter2D(enhanced, -1, sharpen_kernel)

    # Boost saturation
    hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = np.clip(cv2.add(s, 40), 0, 255).astype(hsv.dtype)
    enhanced = cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

    h_roi, w_roi = enhanced.shape[:2]
    if max(h_roi, w_roi) > target_size:
        scale = target_size / float(max(h_roi, w_roi))
        enhanced = cv2.resize(enhanced, (int(w_roi * scale), int(h_roi * scale)), cv2.INTER_AREA)
        h_roi, w_roi = enhanced.shape[:2]

    dy, dx = target_size - h_roi, target_size - w_roi
    top, bottom = dy // 2, dy - dy // 2
    left, right = dx // 2, dx - dx // 2
    return cv2.copyMakeBorder(enhanced, top, bottom, left, right, cv2.BORDER_CONSTANT)

# -----------------------------------------------------------------------------
# Core detection helpers
# -----------------------------------------------------------------------------

def is_right_arm_raised(frame: np.ndarray,
                        hand_detector: mp.solutions.hands.Hands,
                        landmarks: list,
                        w: int,
                        h: int) -> bool:
    """True if right arm is raised **and** hand is closed."""
    results = hand_detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    predicted_class = 0  # default = open hand

    rs, ls = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER], landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    rw, lw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST],   landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

    rs_xy, ls_xy = np.array([rs.x*w, rs.y*h]), np.array([ls.x*w, ls.y*h])
    rw_xy, lw_xy = np.array([rw.x*w, rw.y*h]), np.array([lw.x*w, lw.y*h])


    # Posture check: right wrist above right shoulder AND left wrist down
    if rw_xy[1] < rs_xy[1] and lw_xy[1] > ls_xy[1] and 2*rw_xy[1] < lw_xy[1]:
        rois, boxes = [], []

        # 1) Try MediaPipe Hands boxes
        if results.multi_hand_landmarks:
            fh, fw = frame.shape[:2]
            for hls in results.multi_hand_landmarks:
                pts = np.array([(lm.x*fw, lm.y*fh) for lm in hls.landmark])
                x_min, y_min = (pts.min(0) - 20).astype(int)
                x_max, y_max = (pts.max(0) + 20).astype(int)
                x_min, y_min = max(x_min,0), max(y_min,0)
                x_max, y_max = min(x_max,fw), min(y_max,fh)
                boxes.append((x_min,y_min,x_max,y_max))
                rois.append(frame[y_min:y_max, x_min:x_max])

        # 2) Fallback: square around right wrist
        if not rois:
            half = SIDE_FALLBACK_HAND // 4
            cx, cy = map(int, rw_xy)
            x_min, y_min = max(cx - half, 0), max(cy - half - 40, 0)
            x_max, y_max = min(cx + half, w), min(cy + half - 10, h)
            if x_max - x_min > 10 and y_max - y_min > 10:
                boxes.append((x_min,y_min,x_max,y_max))
                rois.append(frame[y_min:y_max, x_min:x_max])

        # Classify each ROI
        for (x_min,y_min,x_max,y_max), roi in zip(boxes,rois):
            hand_img = preprocess_hand_roi(roi)
            hand_img = np.expand_dims(img_to_array(hand_img)/255.0, 0)
            pred = model_hand.predict(hand_img, verbose=0)
            cls = int(np.argmax(pred))
            conf = float(pred.max())
            cv2.rectangle(frame, (x_min,y_min), (x_max,y_max), (0,255,0), 2)
            cv2.putText(frame, f"Class:{cls} Conf:{conf:.2f}", (x_min,y_min-10),
                        cv2.FONT_HERSHEY_SIMPLEX, .8, (255,255,255), 2)
            predicted_class = max(predicted_class, cls)
    return predicted_class == 1  # 1 = closed hand


def check_hands_on_heart(pose_landmarks, w, h, color_image):
    """Return True if both wrists are over the heart region and form a heart‑shape."""
    try:
        rs = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        ls = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        rw = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        lw = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        lh = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]

        if rw.y > rs.y and rw.y < lh.y:
            heart_x = (rs.x + ls.x) / 2
            heart_y = rs.y - ((rs.y - lh.y) / 4)
            heart_px = int(heart_x * w), int(heart_y * h)

            rw_dist = calculate_distance((rw.x*w, rw.y*h), heart_px)
            lw_dist = calculate_distance((lw.x*w, lw.y*h), heart_px)

            tol_px = HEART_REGION_TOLERANCE * w
            if rw_dist < tol_px and lw_dist < tol_px:
                # Bounding box around wrists
                pts = np.array([(rw.x*w, rw.y*h), (lw.x*w, lw.y*h)])
                x_min = int(np.min(pts[:,0]) - 10)
                y_min = int(np.min(pts[:,1]) - 50)
                x_max = int(np.max(pts[:,0]) + 10)
                y_max = int(np.max(pts[:,1]) + 30)
                x_min, y_min = max(x_min,0), max(y_min,0)
                x_max, y_max = min(x_max,w), min(y_max,h)

                roi = color_image[y_min:y_max, x_min:x_max]
                cv2.rectangle(color_image, (x_min,y_min), (x_max,y_max), (0,0,255), 2)

                roi_resized = cv2.resize(roi, (120,120))
                roi_arr = np.expand_dims(img_to_array(roi_resized)/255.0, 0)
                pred = model_cuoricini.predict(roi_arr, verbose=0)
                cls = int(np.argmax(pred))
                conf = float(np.max(pred))
                cv2.putText(color_image, f"Cuoricini:{cls} Conf:{conf:.2f}",
                            (x_min, y_min-10), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,0,255), 2)

                wrist_dist = calculate_distance((rw.x*w, rw.y*h), (lw.x*w, lw.y*h))
                if cls == 1 and wrist_dist > CLOSENESS_WRISTS_TOLERANCE * w:
                    return True
    except IndexError:
        pass
    return False


def calculate_level(pose_landmarks, w, h):
    """Update global *level* based on hand height (tracking‑3)."""
    global level, _prev_level, _stable_count, _last_level

    try:
        rs = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        ls = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        rh = pose_landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        lh = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        rw = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        lw = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

        rs_px, ls_px = (int(rs.x*w), int(rs.y*h)), (int(ls.x*w), int(ls.y*h))
        rw_px, lw_px = (int(rw.x*w), int(rw.y*h)), (int(lw.x*w), int(lw.y*h))

        r_arm_len = calculate_conversion_distances(rw_px, rs_px, rs_px, ls_px)
        l_arm_len = calculate_conversion_distances(lw_px, ls_px, rs_px, ls_px)
        if r_arm_len < ARM_LENGTH or l_arm_len < ARM_LENGTH:
            level = 0
            return

        avg_hand_y = (rw.y + lw.y) / 2
        avg_sh_y   = (rs.y + ls.y) / 2
        wrist_diff = abs(rw.y - lw.y)
        upper_lim  = avg_sh_y + 0.10
        lower_lim  = (rh.y + lh.y) / 2

        if rw.y < lower_lim and lw.y < lower_lim and wrist_diff < HAND_HEIGHT_TOLERANCE:
            norm_h = np.clip((lower_lim - avg_hand_y) / (lower_lim - upper_lim), 0, 1)
            new_level = min(int(norm_h * MAX_LEVEL), MAX_LEVEL)
        else:
            new_level = 0

        if new_level == _last_level:
            _stable_count += 1
        else:
            _stable_count = 1
            _last_level = new_level

        if abs(new_level - _prev_level) >= LEVEL_CHANGE_THRESHOLD and _stable_count >= HYSTERESIS_FRAMES:
            level = new_level
            _prev_level = level
    except IndexError:
        pass

# -----------------------------------------------------------------------------
# OSC send helpers (no hidden globals)
# -----------------------------------------------------------------------------

def send_number_blinders(value: int):
    client_lights.send_message("/blinders", value)
    client_rpi.send_message("/blinders", value)
    print(f"→ /blinders {value}")


def send_number_lights(value: int):
    client_lights.send_message("/lights", value)
    client_rpi.send_message("/lights", value)
    print(f"→ /lights {value}")


def send_number_fire_machine(value: int):
    client_lights.send_message("/fireMachine", value*10)  # 0‑100 for lights
    client_rpi.send_message("/fireMachine", value)        # raw 0‑10 for RPi
    print(f"→ /fireMachine {value}")

# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------

def start_pipeline() -> bool:
    try:
        pipeline.start(config)
        global depth_scale
        depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
        print(f"Pipeline started (depth scale {depth_scale:.4f} m/unit)")
        return True
    except Exception as e:
        print(f"Error starting pipeline: {e}")
        return False


# Modifica qui: aggiungi stop_event e frame_queue come parametri
def run(stop_event: threading.Event, frame_queue: queue.Queue): # Aggiungi frame_queue
    if not start_pipeline():
        return

    init_time = time.time()
    right_arm_fixed = False
    counter_arm = 0
    SAMPLE_EVERY = 5

    try:
        while True:
            if stop_event.is_set():
                print("Segnale di stop ricevuto, terminazione di main.py...")
                break

            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            if not color_frame or not depth_frame:
                continue

            color_image = cv2.cvtColor(np.asanyarray(color_frame.get_data()), cv2.COLOR_RGB2BGR)
            depth_image = np.asanyarray(depth_frame.get_data())  # kept if you need depth later
            h, w, _ = color_image.shape

            pose_results = pose.process(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
            if pose_results.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(color_image, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                # ---------- Tracking‑2 (heart) ----------
                heart = int(check_hands_on_heart(pose_results.pose_landmarks.landmark, w, h, color_image))
                send_number_lights(heart)

                # ---------- Tracking‑1 (right arm raised) ----------
                right_arm_high = is_right_arm_raised(color_image, hands, pose_results.pose_landmarks.landmark, w, h)

                if right_arm_high != right_arm_fixed:
                    counter_arm += 1
                    if counter_arm >= SAMPLE_EVERY:
                        right_arm_fixed = right_arm_high
                        counter_arm = 0

                send_number_blinders(int(right_arm_fixed))

                # ---------- Tracking‑3 (arm level) ----------
                if not right_arm_high and time.time() - init_time > STABILITY_WAIT_TIME:
                    calculate_level(pose_results.pose_landmarks.landmark, w, h)

                send_number_fire_machine(level)

            # HUD
            cv2.putText(color_image, f"Level:{level}", (50,50), cv2.FONT_HERSHEY_SIMPLEX,1,
                        (0,255,0) if level == MAX_LEVEL else (0,0,255), 2)
            if level == MAX_LEVEL:
                cv2.putText(color_image, "Max Level Reached!", (50,100), cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)

            # Invece di cv2.imshow, inserisci il frame nella coda
            ret, buffer = cv2.imencode('.jpg', color_image)
            if not ret:
                continue
            frame = buffer.tobytes()
            try:
                # Metti il frame nella coda. Usa un timeout per non bloccare indefinitamente
                frame_queue.put(frame, block=False) 
            except queue.Full:
                # Se la coda è piena, salta il frame. Questo evita che main.py si blocchi
                pass
            
            # Non è più necessario waitKey con un timeout per lo stop, 
            # il controllo stop_event.is_set() è sufficiente.
            # Rimuoviamo anche il controllo 'q' dato che l'interfaccia è web.
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break

    except RuntimeError as e:
        print(f"Runtime error: {e}")
    finally:
        print("Stopping pipeline…")
        pipeline.stop()
        pose.close()
        hands.close()
        # Non è necessario cv2.destroyAllWindows() qui, dato che non mostriamo finestre.
        # cv2.destroyAllWindows()


# Rimuovi il blocco if __name__ == "__main__": per evitare l'esecuzione automatica
# quando main.py viene importato come modulo.
