import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# Carica il modello
model = load_model('/Users/filippo/Library/CloudStorage/OneDrive-PolitecnicodiMilano/Corsi/Creative Programming and Computing ⌨️/Clone GitHub/FlowVision/Core/ML/modello_Python_aggiornato.h5')

# Inizializza MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Apri la webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip per un'esperienza tipo specchio
    frame = cv2.flip(frame, 1)
    # Pre-processing per contrastare il controluce
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(lab)

    # Applica CLAHE sul canale L
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)

    # Ricostruisci immagine con canale L equalizzato
    limg = cv2.merge((cl, a, b))
    enhanced_frame = cv2.cvtColor(limg, cv2.COLOR_Lab2BGR)

    # Riduzione del rumore (opzionale, utile se molta luce)
    enhanced_frame = cv2.GaussianBlur(enhanced_frame, (3, 3), 0)

    # Conversione in RGB per MediaPipe
    rgb_frame = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Ottieni bounding box dai landmark
            h, w, _ = frame.shape
            landmark_array = np.array([(lm.x * w, lm.y * h) for lm in hand_landmarks.landmark])
            x_min = int(np.min(landmark_array[:, 0]) - 20)
            y_min = int(np.min(landmark_array[:, 1]) - 20)
            x_max = int(np.max(landmark_array[:, 0]) + 20)
            y_max = int(np.max(landmark_array[:, 1]) + 20)

            # Assicurati che i limiti siano validi
            x_min, y_min = max(x_min, 0), max(y_min, 0)
            x_max, y_max = min(x_max, w), min(y_max, h)

            hand_img = frame[y_min:y_max, x_min:x_max]
            hand_img = cv2.resize(hand_img, (120, 120))
            hand_img = img_to_array(hand_img) / 255.0
            hand_img = np.expand_dims(hand_img, axis=0)

            # Predizione
            prediction = model.predict(hand_img)
            predicted_class = np.argmax(prediction)
            confidence = np.max(prediction)

            # Disegna bounding box e testo
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            text = f"Classe: {predicted_class}, Conf: {confidence:.2f}"
            cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # (Opzionale) Disegna i landmark
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Mostra il video
    cv2.imshow("Real-time Hand Detection + Prediction", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
