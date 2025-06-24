import cv2
import mediapipe as mp
import pyrealsense2 as rs
import numpy as np
import time
from pythonosc.udp_client import SimpleUDPClient

def run(stop_event):
    # Inizializza MediaPipe
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

    # Inizializza RealSense Pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # Configure OSC Client Address and Port
    ip = "127.0.0.1"
    port1 = 7700
    client = SimpleUDPClient(ip, port1)

    # Variabili globali
    HEART_REGION_TOLERANCE = 0.10
    SHOULDER_DISTANCE = 0.45
    ARM_LENGTH = 0.60
    max_level = 10
    level = 0
    prev_level = 0
    ARM_MIN_LENGTH = 0.45
    HAND_HEIGHT_TOLERANCE = 0.10
    STABILITY_WAIT_TIME = 1.0
    LEVEL_CHANGE_THRESHOLD = 1

    # Funzioni ausiliarie
    def calculate_distance(p1, p2):
        return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def calculate_conversion_distances(p1, p2, right_shoulder, left_shoulder):
        shoulder_distance_px = round(
            np.sqrt((right_shoulder[0] - left_shoulder[0]) ** 2 + (right_shoulder[1] - left_shoulder[1]) ** 2), 3)
        conversion_factor = SHOULDER_DISTANCE / shoulder_distance_px
        distance_px = np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
        return distance_px * conversion_factor

    def is_right_arm_raised(landmarks, w, h):
        try:
            rs = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            ls = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
            lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

            rs_px = [rs.x * w, rs.y * h, rs.z]
            ls_px = [ls.x * w, ls.y * h, rs.z]
            rw_px = [rw.x * w, rw.y * h, rw.z]
            lw_px = [lw.x * w, lw.y * h, lw.z]

            return rw_px[1] < rs_px[1] and lw_px[1] > ls_px[1]
        except IndexError:
            return False

    def check_hands_on_heart(landmarks, w, h):
        try:
            rs = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            ls = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
            lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
            lh = landmarks[mp_pose.PoseLandmark.LEFT_HIP]

            if rw.y > rs.y and rw.y < lh.y:
                heart_x = (rs.x + ls.x) / 2
                heart_y = rs.y - ((rs.y - lh.y) / 4)
                heart_region = (int(heart_x * w), int(heart_y * h))
                rw_dist = calculate_distance((rw.x * w, rw.y * h), heart_region)
                lw_dist = calculate_distance((lw.x * w, lw.y * h), heart_region)
                return rw_dist < HEART_REGION_TOLERANCE * w and lw_dist < HEART_REGION_TOLERANCE * w
            return False  # se nessuna condizione è soddisfatta
        except IndexError:
            return False
        except Exception as e:
            print(f"Errore in check_hands_on_heart: {e}")
            return False

    def calculate_level(landmarks, w, h):
        nonlocal level, prev_level
        try:
            rs = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            ls = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            rh = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
            lh = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
            lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]

            rs_px = (int(rs.x * w), int(rs.y * h))
            ls_px = (int(ls.x * w), int(ls.y * h))
            rw_px = (int(rw.x * w), int(rw.y * h))
            lw_px = (int(lw.x * w), int(lw.y * h))

            right_arm_length = calculate_conversion_distances(rw_px, rs_px, rs_px, ls_px)
            left_arm_length = calculate_conversion_distances(lw_px, ls_px, rs_px, ls_px)

            if right_arm_length < ARM_LENGTH or left_arm_length < ARM_LENGTH:
                level = 0
                return

            avg_hand_height = (rw.y + lw.y) / 2
            avg_shoulder_height = (rs.y + ls.y) / 2
            avg_hip_height = (rh.y + lh.y) / 2
            wrist_diff = abs(rw.y - lw.y)

            if rw.y < avg_hip_height and lw.y < avg_hip_height and wrist_diff < HAND_HEIGHT_TOLERANCE:
                normalized_height = (avg_hip_height - avg_hand_height) / (avg_hip_height - avg_shoulder_height * 0.5)
                new_level = min(int(normalized_height * max_level), max_level)
            else:
                new_level = 0

            if abs(new_level - prev_level) >= LEVEL_CHANGE_THRESHOLD:
                level = new_level
                prev_level = level
        except IndexError:
            pass

    def send_osc_message(addr, value):
        client.send_message(addr, value)
        print(f"Sent {value} to {addr}")

    # Start pipeline
    try:
        pipeline.start(config)
    except Exception as e:
        print(f"Errore nell'avvio della pipeline: {e}")
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

                heart = int(check_hands_on_heart(landmarks, w, h))
                send_osc_message("/lights", heart)

                right_arm_high = int(is_right_arm_raised(landmarks, w, h))
                send_osc_message("/blinders", right_arm_high)

                if not right_arm_high and time.time() - initial_time > STABILITY_WAIT_TIME:
                    calculate_level(landmarks, w, h)

                send_osc_message("/fireMachine", level)

                cv2.putText(color_image, f"Level: {level}", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0) if level == max_level else (0, 0, 255), 2)

                if level == max_level:
                    cv2.putText(color_image, "Max Level Reached!", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
            #cv2.imshow("Hand and Body Tracking Detection", color_image)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break

    except RuntimeError as e:
        print(f"Errore durante l'acquisizione dei frame: {e}")
    finally:
        pose.close()
        pipeline.stop()
        cv2.destroyAllWindows()
