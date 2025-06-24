import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time
import threading
from pythonosc.udp_client import SimpleUDPClient

# Inizializza MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# OSC
ip = "127.0.0.1"
port1 = 7700
client = SimpleUDPClient(ip, port1)

# Parametri costanti
HEART_REGION_TOLERANCE = 0.10
SHOULDER_DISTANCE = 0.45
ARM_LENGTH = 0.60
ARM_MIN_LENGTH = 0.45
HAND_HEIGHT_TOLERANCE = 0.10
STABILITY_WAIT_TIME = 1.0
LEVEL_CHANGE_THRESHOLD = 1
max_level = 10
level = 0
prev_level = 0

# === FUNZIONI DI SUPPORTO (identiche) ===
# [omesse per brevità: calculate_distance, calculate_distance_3d, etc.]
# Copia e incolla le funzioni già presenti nel tuo script originale qui sopra

# === FUNZIONE MAIN LOOP ===
def run(stop_event):
    global level, prev_level

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
        return

    depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
    print(f"Depth Scale: {depth_scale} meters per unit")

    try:
        initial_time = time.time()

        while not stop_event.is_set():
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            h, w, _ = color_image.shape

            rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            pose_results = pose.process(rgb_image)

            if pose_results.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    color_image, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                landmarks = pose_results.pose_landmarks.landmark

                heart = 1 if check_hands_on_heart(landmarks, w, h) else 0
                client.send_message("/lights", heart)
                print(f"heart: {heart}")

                right_arm_high = 1 if is_right_arm_raised(landmarks, w, h) else 0
                client.send_message("/blinders", right_arm_high)
                print(f"right_arm_high: {right_arm_high}")

                if not right_arm_high and time.time() - initial_time > STABILITY_WAIT_TIME:
                    calculate_level(landmarks, w, h, depth_image)

                client.send_message("/fireMachine", level)

            cv2.putText(color_image, f"Level: {level}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if level == max_level else (0, 0, 255), 2)

            if level == max_level:
                cv2.putText(color_image, "Max Level Reached!", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Hand and Body Tracking Detection", color_image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except RuntimeError as e:
        print(f"Errore durante l'acquisizione dei frame: {e}")
    finally:
        pose.close()
        pipeline.stop()
        cv2.destroyAllWindows()
        print("Pipeline and resources released.")

